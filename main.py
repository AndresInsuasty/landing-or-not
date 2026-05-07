"""
Aterrizaje - Simulador de landing lunar para clase de algoritmos.
Aplicación pygame completa.
"""

import pygame
import sys
import random
import math
from typing import Optional

import physics


# ============================================================================
# WINDOW & COLOR CONSTANTS
# ============================================================================

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700

COLOR_BG = (8, 8, 24)              # Deep space background
COLOR_STAR = (255, 255, 220)
COLOR_PANEL = (20, 30, 60)
COLOR_TEXT = (220, 220, 255)
COLOR_ACCENT = (80, 160, 255)
COLOR_SUCCESS = (60, 220, 100)
COLOR_CRASH = (230, 60, 60)
COLOR_WARNING = (255, 200, 50)
COLOR_THRUST = (255, 140, 30)
COLOR_ROCKET = (180, 200, 230)
COLOR_FLAME_INNER = (255, 180, 50)
COLOR_FLAME_OUTER = (255, 80, 20)
COLOR_PAD = (100, 120, 140)
COLOR_INPUT_BG = (15, 20, 45)
COLOR_INPUT_ACTIVE = (30, 60, 120)
COLOR_INPUT_BORDER = (80, 160, 255)
COLOR_BUTTON_BG = (40, 60, 140)
COLOR_BUTTON_HOVER = (60, 100, 200)

# Animation timing
ANIM_DURATION_PER_STEP = 1.5  # Real seconds per simulation second


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_stars(n: int, seed: int = 42) -> list[tuple]:
    """Generate n random (x, y, radius) tuples."""
    random.seed(seed)
    stars = []
    for _ in range(n):
        x = random.randint(0, WINDOW_WIDTH)
        y = random.randint(0, WINDOW_HEIGHT)
        r = random.randint(1, 2)
        stars.append((x, y, r))
    return stars


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation. t in [0, 1]."""
    return a + (b - a) * t


def clamp_01(t: float) -> float:
    """Clamp t to [0, 1]."""
    return max(0.0, min(1.0, t))


def draw_text_centered(surface, text: str, font, color, cx: float, cy: float):
    """Render text centered at (cx, cy)."""
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=(cx, cy))
    surface.blit(text_surf, text_rect)


def draw_text_left(surface, text: str, font, color, x: float, y: float):
    """Render text with left edge at x, top at y."""
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, (x, y))


def draw_rounded_panel(surface, rect: pygame.Rect, color, radius: int = 12):
    """Draw a filled rounded rectangle."""
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def height_to_screen_y(h: float) -> float:
    """Map height [0, 100] to screen y in the viewport."""
    # h=100 → y=80 (top)
    # h=0   → y=650 (bottom/pad)
    return 650 - (h / 100.0) * 570


def draw_rocket(surface, cx: float, cy: float, thrust_pct: float):
    """Draw a procedural rocket with flame effect."""
    # Body
    body_width, body_height = 20, 50
    body_rect = pygame.Rect(cx - body_width // 2, cy - body_height // 2,
                            body_width, body_height)
    pygame.draw.rect(surface, COLOR_ROCKET, body_rect)

    # Nose cone (triangle on top)
    nose_points = [
        (cx, cy - body_height // 2 - 12),
        (cx - 12, cy - body_height // 2),
        (cx + 12, cy - body_height // 2)
    ]
    pygame.draw.polygon(surface, COLOR_ROCKET, nose_points)

    # Fins (small triangles on sides)
    fin_y_base = cy + body_height // 2 - 10
    left_fin = [(cx - body_width // 2, fin_y_base), (cx - 20, fin_y_base + 12),
                (cx - body_width // 2, fin_y_base + 12)]
    right_fin = [(cx + body_width // 2, fin_y_base), (cx + 20, fin_y_base + 12),
                 (cx + body_width // 2, fin_y_base + 12)]
    pygame.draw.polygon(surface, COLOR_ROCKET, left_fin)
    pygame.draw.polygon(surface, COLOR_ROCKET, right_fin)

    # Flame effect (if thrusting)
    if thrust_pct > 1:
        flame_height = int(thrust_pct / 100.0 * 35) + 5
        flame_width = int(thrust_pct / 100.0 * 15) + 5

        # Add flicker
        flicker = random.randint(-3, 3)
        flame_height += flicker

        # Outer flame (orange)
        flame_base_y = cy + body_height // 2
        outer_flame = [
            (cx - flame_width, flame_base_y),
            (cx, flame_base_y + flame_height),
            (cx + flame_width, flame_base_y)
        ]
        pygame.draw.polygon(surface, COLOR_FLAME_OUTER, outer_flame)

        # Inner flame (yellow)
        inner_width = flame_width // 2
        inner_height = flame_height * 0.6
        inner_flame = [
            (cx - inner_width, flame_base_y),
            (cx, flame_base_y + inner_height),
            (cx + inner_width, flame_base_y)
        ]
        pygame.draw.polygon(surface, COLOR_FLAME_INNER, inner_flame)


def is_mouse_over_rect(mouse_pos, rect: pygame.Rect) -> bool:
    """Check if mouse is over rectangle."""
    return rect.collidepoint(mouse_pos)


# ============================================================================
# INPUT BOX CLASS
# ============================================================================

class InputBox:
    """Text input box for thrust percentage entry."""

    def __init__(self, rect: pygame.Rect, index: int):
        self.rect = rect
        self.index = index
        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0.0

    def handle_event(self, event, on_next_field_callback=None):
        """Handle keyboard/mouse events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.cursor_timer = 0.0
            else:
                self.active = False

        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_TAB:
                self.active = False
                if on_next_field_callback:
                    on_next_field_callback(self.index)
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif event.unicode.isdigit():
                # Only allow if result would be <= 3 chars (max 100%)
                if len(self.text) < 3:
                    self.text += event.unicode

    def get_value(self) -> float:
        """Return clamped value [0, 100]."""
        if not self.text:
            return 0.0
        try:
            val = float(self.text)
            return max(0.0, min(100.0, val))
        except ValueError:
            return 0.0

    def update(self, dt):
        """Update cursor blink."""
        self.cursor_timer += dt
        if self.cursor_timer > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0.0

    def draw(self, surface, font):
        """Draw the input box."""
        # Background
        bg_color = COLOR_INPUT_ACTIVE if self.active else COLOR_INPUT_BG
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=4)

        # Border
        pygame.draw.rect(surface, COLOR_INPUT_BORDER, self.rect, 2, border_radius=4)

        # Text
        if self.text:
            text_surf = font.render(self.text, True, COLOR_TEXT)
        else:
            text_surf = font.render("0", True, (100, 100, 140))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

        # Cursor
        if self.active and self.cursor_visible:
            cursor_x = self.rect.centerx + len(self.text) * 6
            cursor_y = self.rect.top + 8
            pygame.draw.line(surface, COLOR_ACCENT, (cursor_x, cursor_y),
                           (cursor_x, cursor_y + 24), 2)


# ============================================================================
# SCREEN CLASSES
# ============================================================================

class InputScreen:
    """Screen for inputting 10 thrust percentages."""

    def __init__(self, app):
        self.app = app
        self.input_boxes = []
        self.focused_index = 0
        self.cursor_timer = 0.0
        self.error_text = ""
        self.error_timer = 0.0

        # Create 10 input boxes in 2 columns
        left_col_x = 100
        right_col_x = 500
        top_y = 170

        for i in range(10):
            if i < 5:
                x = left_col_x
                y = top_y + i * 65
            else:
                x = right_col_x
                y = top_y + (i - 5) * 65

            rect = pygame.Rect(x + 180, y, 100, 40)
            self.input_boxes.append(InputBox(rect, i))

        self.button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 100, 600, 200, 55)

    def on_next_field(self, current_index: int):
        """Move focus to next field."""
        next_index = (current_index + 1) % len(self.input_boxes)
        self.input_boxes[next_index].active = True
        self.input_boxes[next_index].cursor_timer = 0.0

    def handle_event(self, event):
        """Handle input events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_rect.collidepoint(event.pos):
                self.validate_and_simulate()

        for box in self.input_boxes:
            box.handle_event(event, self.on_next_field)

    def validate_and_simulate(self):
        """Validate inputs and start simulation."""
        thrusts = [box.get_value() for box in self.input_boxes]
        states = physics.simulate(thrusts)
        self.app.go_to_simulation(states, thrusts)

    def update(self, dt):
        """Update cursor blink."""
        self.error_timer -= dt
        for box in self.input_boxes:
            box.update(dt)

    def draw(self, surface):
        """Draw the input screen."""
        # Title
        draw_text_centered(surface, "SIMULADOR DE ATERRIZAJE LUNAR",
                         self.app.font_title, COLOR_TEXT,
                         WINDOW_WIDTH // 2, 30)

        draw_text_centered(surface, "Ingresa el empuje para cada segundo (0-100%)",
                         self.app.font_small, COLOR_ACCENT,
                         WINDOW_WIDTH // 2, 80)

        # Labels and input boxes
        left_col_x = 100
        right_col_x = 500
        top_y = 170

        for i, box in enumerate(self.input_boxes):
            if i < 5:
                x = left_col_x
                y = top_y + i * 65
            else:
                x = right_col_x
                y = top_y + (i - 5) * 65

            label = f"Segundo {i + 1}:"
            draw_text_left(surface, label, self.app.font_medium, COLOR_TEXT, x, y + 5)
            box.draw(surface, self.app.font_medium)

        # Hint text
        hint = "Empuje hover: 40% cancela la gravedad"
        draw_text_centered(surface, hint, self.app.font_small, COLOR_ACCENT,
                         WINDOW_WIDTH // 2, 530)

        # Simulate button
        button_color = COLOR_BUTTON_HOVER if is_mouse_over_rect(
            pygame.mouse.get_pos(), self.button_rect) else COLOR_BUTTON_BG
        pygame.draw.rect(surface, button_color, self.button_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_ACCENT, self.button_rect, 2, border_radius=8)
        draw_text_centered(surface, "SIMULAR", self.app.font_large,
                         COLOR_TEXT, self.button_rect.centerx, self.button_rect.centery)

        # Error message (if any)
        if self.error_timer > 0:
            draw_text_centered(surface, self.error_text, self.app.font_small,
                             COLOR_CRASH, WINDOW_WIDTH // 2, 640)


class SimulationScreen:
    """Screen showing the animated landing simulation."""

    def __init__(self, app, states: list[dict], thrusts: list[float]):
        self.app = app
        self.states = states
        self.thrusts = thrusts
        self.current_step = 0
        self.step_t = 0.0
        self.done = False
        self.transition_timer = 2.5

        self.current_h = states[0]['h']
        self.current_v = states[0]['v']

    def handle_event(self, event):
        """Handle input (for future pause/skip features)."""
        pass

    def update(self, dt):
        """Update animation and physics."""
        if self.done:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self.app.go_to_result(self.states, self.thrusts)
            return

        self.step_t += dt
        alpha = clamp_01(self.step_t / ANIM_DURATION_PER_STEP)

        # Interpolate position between current and next state
        if self.current_step < len(self.states) - 1:
            h_from = self.states[self.current_step]['h']
            h_to = self.states[self.current_step + 1]['h']
            self.current_h = lerp(h_from, h_to, alpha)

            v_from = self.states[self.current_step]['v']
            v_to = self.states[self.current_step + 1]['v']
            self.current_v = lerp(v_from, v_to, alpha)

        # Check if step animation is complete
        if self.step_t >= ANIM_DURATION_PER_STEP:
            self.step_t = 0.0
            self.current_step += 1

            # Check if landing/crash happened or all steps complete
            if self.current_step >= len(self.states) - 1:
                self.done = True
            elif self.states[self.current_step]['outcome'] is not None:
                self.done = True

    def draw_telemetry_panel(self, surface):
        """Draw left telemetry panel."""
        x_start = 20
        y_start = 60

        # Panel background
        panel_rect = pygame.Rect(x_start, y_start, 200, WINDOW_HEIGHT - 80)
        draw_rounded_panel(surface, panel_rect, COLOR_PANEL, 6)
        pygame.draw.rect(surface, COLOR_ACCENT, panel_rect, 1, border_radius=6)

        # Title
        draw_text_left(surface, "TELEMETRÍA", self.app.font_medium,
                      COLOR_ACCENT, x_start + 15, y_start + 15)

        y = y_start + 50

        # Height
        h_text = f"Altura: {self.current_h:.1f} m"
        draw_text_left(surface, h_text, self.app.font_small, COLOR_TEXT,
                      x_start + 15, y)
        y += 35

        # Velocity with color coding
        vel_color = COLOR_SUCCESS if abs(self.current_v) <= 3 else (
            COLOR_WARNING if abs(self.current_v) <= 6 else COLOR_CRASH)
        v_text = f"Vel: {self.current_v:.1f} m/s"
        draw_text_left(surface, v_text, self.app.font_small, vel_color,
                      x_start + 15, y)
        y += 35

        # Thrust
        current_thrust = self.states[self.current_step]['thrust'] if self.current_step < len(
            self.states) else 0
        thrust_text = f"Empuje: {current_thrust:.0f}%"
        draw_text_left(surface, thrust_text, self.app.font_small,
                      COLOR_THRUST, x_start + 15, y)
        y += 35

        # Time
        time_text = f"Tiempo: {min(self.current_step, 10)}s"
        draw_text_left(surface, time_text, self.app.font_small, COLOR_TEXT,
                      x_start + 15, y)
        y += 40

        # Thrust bar
        bar_width = 170
        bar_height = 20
        bar_bg = pygame.Rect(x_start + 15, y, bar_width, bar_height)
        pygame.draw.rect(surface, COLOR_INPUT_BG, bar_bg)

        bar_fill_width = int(bar_width * (current_thrust / 100.0))
        bar_fill = pygame.Rect(x_start + 15, y, bar_fill_width, bar_height)
        pygame.draw.rect(surface, COLOR_THRUST, bar_fill)
        pygame.draw.rect(surface, COLOR_ACCENT, bar_bg, 1)

    def draw_space_viewport(self, surface):
        """Draw the space scene with rocket and landing pad."""
        # Viewport area
        vp_x = 240
        vp_y = 60
        vp_w = WINDOW_WIDTH - vp_x - 20
        vp_h = WINDOW_HEIGHT - 80

        # Background with stars
        for (x, y, r) in self.app.stars:
            pygame.draw.circle(surface, COLOR_STAR, (vp_x + x // 3, vp_y + y // 3), r)

        # Landing pad at bottom
        pad_y = vp_y + vp_h - 30
        pad_rect = pygame.Rect(vp_x + 50, pad_y, vp_w - 100, 25)
        pygame.draw.rect(surface, COLOR_PAD, pad_rect)
        pygame.draw.rect(surface, COLOR_ACCENT, pad_rect, 2)

        # Rocket position
        rocket_cx = vp_x + vp_w // 2
        rocket_cy = height_to_screen_y(self.current_h)

        # Clamp rocket to viewport
        rocket_cy = max(vp_y + 10, min(vp_y + vp_h - 10, rocket_cy))

        # Draw rocket
        draw_rocket(surface, rocket_cx, rocket_cy,
                   self.states[self.current_step]['thrust'])

        # Crash flash
        if self.done and self.states[-1]['outcome'] == "CHOQUE":
            flash_alpha = int(self.transition_timer * 150)
            flash_surf = pygame.Surface((vp_w, vp_h))
            flash_surf.set_colorkey((0, 0, 0))
            flash_surf.fill(COLOR_CRASH)
            flash_surf.set_alpha(flash_alpha)
            surface.blit(flash_surf, (vp_x, vp_y))

    def draw(self, surface):
        """Draw the simulation screen."""
        # Header
        time_str = f"Segundo: {min(self.current_step, 10)} / 10"
        draw_text_left(surface, "SIMULANDO...", self.app.font_large,
                      COLOR_ACCENT, 20, 15)
        draw_text_right(surface, time_str, self.app.font_large,
                       COLOR_ACCENT, WINDOW_WIDTH - 20, 15)

        # Telemetry panel
        self.draw_telemetry_panel(surface)

        # Space viewport
        self.draw_space_viewport(surface)


class ResultScreen:
    """Screen showing landing results."""

    def __init__(self, app, states: list[dict], thrusts: list[float]):
        self.app = app
        self.states = states
        self.thrusts = thrusts
        self.outcome = physics.classify_outcome(states)
        self.fade_timer = 0.5
        self.button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 120, 600, 240, 55)

    def handle_event(self, event):
        """Handle button click."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_rect.collidepoint(event.pos):
                self.app.go_to_input()

    def update(self, dt):
        """Update fade-in animation."""
        self.fade_timer -= dt

    def draw(self, surface):
        """Draw the result screen."""
        # Fade-in overlay
        if self.fade_timer > 0:
            fade_alpha = int((0.5 - self.fade_timer) / 0.5 * 150)
            fade_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(fade_alpha)
            surface.blit(fade_surf, (0, 0))

        # Result title
        if self.outcome == "EXITO":
            title = "¡ATERRIZAJE EXITOSO!"
            color = COLOR_SUCCESS
        elif self.outcome == "CHOQUE":
            title = "¡CHOQUE! NAVE DESTRUIDA"
            color = COLOR_CRASH
        else:
            title = "SIN ATERRIZAJE"
            color = COLOR_WARNING

        draw_text_centered(surface, title, self.app.font_title, color,
                         WINDOW_WIDTH // 2, 80)

        # Statistics panel
        panel_rect = pygame.Rect(150, 200, WINDOW_WIDTH - 300, 300)
        draw_rounded_panel(surface, panel_rect, COLOR_PANEL, 8)
        pygame.draw.rect(surface, COLOR_ACCENT, panel_rect, 2, border_radius=8)

        # Stats
        y = 220
        draw_text_left(surface, "Estadísticas Finales:", self.app.font_medium,
                      COLOR_ACCENT, 180, y)
        y += 40

        final_h = self.states[-1]['h']
        final_v = self.states[-1]['v']
        final_t = self.states[-1]['t']

        h_text = f"Altura final: {final_h:.1f} m"
        draw_text_left(surface, h_text, self.app.font_small, COLOR_TEXT,
                      180, y)
        y += 30

        v_text = f"Velocidad final: {final_v:.1f} m/s"
        draw_text_left(surface, v_text, self.app.font_small, COLOR_TEXT,
                      180, y)
        y += 30

        t_text = f"Tiempo: {final_t} segundos"
        draw_text_left(surface, t_text, self.app.font_small, COLOR_TEXT,
                      180, y)
        y += 45

        # Thrust sequence visualization
        draw_text_left(surface, "Secuencia de empujes:", self.app.font_small,
                      COLOR_ACCENT, 180, y)
        y += 30

        box_size = 20
        box_spacing = 3
        for i, thrust in enumerate(self.thrusts):
            box_x = 180 + i * (box_size + box_spacing)
            box_y = y

            # Color based on thrust level
            if thrust < 20:
                thrust_color = COLOR_INPUT_BG
            elif thrust < 45:
                thrust_color = COLOR_SUCCESS
            elif thrust < 60:
                thrust_color = COLOR_ACCENT
            else:
                thrust_color = COLOR_THRUST

            pygame.draw.rect(surface, thrust_color,
                           pygame.Rect(box_x, box_y, box_size, box_size))
            pygame.draw.rect(surface, COLOR_ACCENT,
                           pygame.Rect(box_x, box_y, box_size, box_size), 1)

        # Button
        button_color = COLOR_BUTTON_HOVER if is_mouse_over_rect(
            pygame.mouse.get_pos(), self.button_rect) else COLOR_BUTTON_BG
        pygame.draw.rect(surface, button_color, self.button_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_ACCENT, self.button_rect, 2, border_radius=8)
        draw_text_centered(surface, "INTENTAR DE NUEVO", self.app.font_large,
                         COLOR_TEXT, self.button_rect.centerx, self.button_rect.centery)


def draw_text_right(surface, text: str, font, color, x: float, y: float):
    """Render text with right edge at x, top at y."""
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(topright=(x, y))
    surface.blit(text_surf, text_rect)


# ============================================================================
# APP CLASS
# ============================================================================

class App:
    """Main application class."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Aterrizaje Lunar — Algoritmos")
        self.clock = pygame.time.Clock()

        # Fonts
        try:
            self.font_title = pygame.font.SysFont("Arial", 42, bold=True)
            self.font_large = pygame.font.SysFont("Arial", 32, bold=True)
            self.font_medium = pygame.font.SysFont("Arial", 22)
            self.font_small = pygame.font.SysFont("Arial", 16)
        except Exception:
            # Fallback to default pygame font
            self.font_title = pygame.font.Font(None, 42)
            self.font_large = pygame.font.Font(None, 32)
            self.font_medium = pygame.font.Font(None, 22)
            self.font_small = pygame.font.Font(None, 16)

        # Stars background
        self.stars = build_stars(200)

        # Current screen
        self.current_screen = InputScreen(self)

    def go_to_simulation(self, states: list[dict], thrusts: list[float]):
        """Transition to simulation screen."""
        self.current_screen = SimulationScreen(self, states, thrusts)

    def go_to_result(self, states: list[dict], thrusts: list[float]):
        """Transition to result screen."""
        self.current_screen = ResultScreen(self, states, thrusts)

    def go_to_input(self):
        """Transition to input screen."""
        self.current_screen = InputScreen(self)

    def draw_background(self):
        """Draw background (stars)."""
        self.screen.fill(COLOR_BG)
        for (x, y, r) in self.stars:
            pygame.draw.circle(self.screen, COLOR_STAR, (x, y), r)

    def run(self):
        """Main game loop."""
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.current_screen.handle_event(event)

            self.current_screen.update(dt)

            # Draw
            self.draw_background()
            self.current_screen.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app = App()
    app.run()
