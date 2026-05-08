"""
Aterrizaje - Simulador de landing lunar para clase de algoritmos.
Aplicación pygame con UI moderna y visual mejorado.
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

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 750

# Fondo y espacio
COLOR_BG          = (5, 7, 20)
COLOR_BG_PANEL    = (12, 16, 38)
COLOR_STAR        = (220, 230, 255)

# Paneles y bordes
COLOR_PANEL       = (16, 24, 56)
COLOR_PANEL_DARK  = (10, 15, 38)
COLOR_BORDER      = (40, 70, 140)

# Texto
COLOR_TEXT        = (210, 220, 255)
COLOR_TEXT_DIM    = (100, 115, 170)

# Acento principal (azul neón)
COLOR_ACCENT      = (70, 160, 255)
COLOR_ACCENT_DIM  = (35, 80, 140)

# Estados
COLOR_SUCCESS     = (50, 220, 100)
COLOR_CRASH       = (240, 55, 55)
COLOR_WARNING     = (255, 195, 30)

# Empuje y cohete
COLOR_THRUST      = (255, 130, 20)
COLOR_ROCKET      = (160, 185, 220)
COLOR_ROCKET_DARK = (90, 110, 145)
COLOR_FLAME_CORE  = (255, 240, 120)
COLOR_FLAME_MID   = (255, 150, 30)
COLOR_FLAME_OUTER = (220, 55, 10)

# Plataforma de aterrizaje
COLOR_PAD         = (80, 105, 130)
COLOR_PAD_STRIPE  = (255, 200, 50)

# Inputs
COLOR_INPUT_BG     = (12, 18, 45)
COLOR_INPUT_ACTIVE = (20, 40, 100)
COLOR_INPUT_BORDER = (50, 120, 220)

# Botones
COLOR_BUTTON_BG    = (25, 50, 130)
COLOR_BUTTON_HOVER = (50, 100, 210)

# Animation timing
ANIM_DURATION_PER_STEP = 1.5


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_stars(n: int, seed: int = 42) -> list[tuple]:
    """Generate n random (x, y, radius, phase) tuples for twinkling stars."""
    random.seed(seed)
    stars = []
    for _ in range(n):
        x = random.randint(0, WINDOW_WIDTH)
        y = random.randint(0, WINDOW_HEIGHT)
        r = random.choice([1, 1, 1, 2])
        phase = random.uniform(0, math.pi * 2)
        stars.append((x, y, r, phase))
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


def draw_text_right(surface, text: str, font, color, x: float, y: float):
    """Render text with right edge at x, top at y."""
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(topright=(x, y))
    surface.blit(text_surf, text_rect)


def draw_rounded_panel(surface, rect: pygame.Rect, color, radius: int = 12):
    """Draw a filled rounded rectangle."""
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_glow(surface, rect: pygame.Rect, color, layers: int = 4, radius: int = 10):
    """Draw glowing border effect around a rect (outer → inner, alpha decreases)."""
    glow_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    for i in range(layers, 0, -1):
        expand = i * 2
        alpha = int(60 / i)
        r = (color[0], color[1], color[2], alpha)
        expanded = rect.inflate(expand * 2, expand * 2)
        pygame.draw.rect(glow_surf, r, expanded, border_radius=radius + expand, width=2)
    surface.blit(glow_surf, (0, 0))


def draw_progress_bar(surface, rect: pygame.Rect, value: float,
                      color_fill, color_bg=(12, 18, 45), radius: int = 4):
    """Draw a horizontal progress bar. value in [0.0, 1.0]."""
    pygame.draw.rect(surface, color_bg, rect, border_radius=radius)
    if value > 0:
        fill_w = max(1, int(rect.width * clamp_01(value)))
        fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
        pygame.draw.rect(surface, color_fill, fill_rect, border_radius=radius)
    pygame.draw.rect(surface, COLOR_BORDER, rect, 1, border_radius=radius)


def height_to_screen_y(h: float, vp_y: int = 80, vp_h: int = 640) -> float:
    """Map height [0, 100] to screen y in the viewport."""
    return (vp_y + vp_h - 20) - (h / 100.0) * (vp_h - 40)


def is_mouse_over_rect(mouse_pos, rect: pygame.Rect) -> bool:
    """Check if mouse is over rectangle."""
    return rect.collidepoint(mouse_pos)


def draw_rocket(surface, cx: float, cy: float, thrust_pct: float, time: float = 0.0):
    """Draw a detailed procedural rocket with multi-layer flame effect."""
    bw, bh = 26, 62

    # Sombra del cuerpo
    shadow_rect = pygame.Rect(cx - bw // 2 + 3, cy - bh // 2 + 3, bw, bh)
    pygame.draw.rect(surface, (5, 8, 20), shadow_rect, border_radius=6)

    # Cuerpo principal
    body_rect = pygame.Rect(cx - bw // 2, cy - bh // 2, bw, bh)
    pygame.draw.rect(surface, COLOR_ROCKET, body_rect, border_radius=5)

    # Panel lateral izquierdo (detalle)
    stripe_rect = pygame.Rect(cx - bw // 2 + 3, cy - bh // 4, 5, bh // 2)
    pygame.draw.rect(surface, COLOR_ROCKET_DARK, stripe_rect)

    # Cono nasal (polígono)
    nose_tip_y = cy - bh // 2 - 16
    nose_points = [
        (cx, nose_tip_y),
        (cx - 14, cy - bh // 2),
        (cx + 14, cy - bh // 2),
    ]
    pygame.draw.polygon(surface, COLOR_ROCKET, nose_points)

    # Ventana circular
    win_cx = int(cx)
    win_cy = int(cy - 6)
    pygame.draw.circle(surface, (30, 50, 90), (win_cx, win_cy), 7)
    pygame.draw.circle(surface, (70, 140, 220), (win_cx, win_cy), 7, 2)
    pygame.draw.circle(surface, (160, 210, 255), (win_cx - 2, win_cy - 2), 2)

    # Aletas (más pronunciadas)
    fin_y_top = cy + bh // 2 - 16
    fin_y_bot = cy + bh // 2 + 6
    left_fin = [
        (cx - bw // 2, fin_y_top),
        (cx - bw // 2 - 12, fin_y_bot),
        (cx - bw // 2, fin_y_bot),
    ]
    right_fin = [
        (cx + bw // 2, fin_y_top),
        (cx + bw // 2 + 12, fin_y_bot),
        (cx + bw // 2, fin_y_bot),
    ]
    pygame.draw.polygon(surface, COLOR_ROCKET_DARK, left_fin)
    pygame.draw.polygon(surface, COLOR_ROCKET_DARK, right_fin)
    pygame.draw.polygon(surface, COLOR_ROCKET, left_fin, 1)
    pygame.draw.polygon(surface, COLOR_ROCKET, right_fin, 1)

    # Llamas en 3 capas con flicker
    if thrust_pct > 1:
        flicker1 = math.sin(time * 25) * 4
        flicker2 = math.cos(time * 31) * 3
        base_y = cy + bh // 2

        fh_outer = int(thrust_pct / 100.0 * 42) + 10 + int(flicker1)
        fw_outer = int(thrust_pct / 100.0 * 14) + 8

        # Capa exterior (rojo-naranja)
        outer = [(cx - fw_outer, base_y), (cx, base_y + fh_outer), (cx + fw_outer, base_y)]
        pygame.draw.polygon(surface, COLOR_FLAME_OUTER, outer)

        # Capa media (naranja)
        fw_mid = fw_outer * 2 // 3
        fh_mid = int(fh_outer * 0.68) + int(flicker2)
        mid = [(cx - fw_mid, base_y), (cx, base_y + fh_mid), (cx + fw_mid, base_y)]
        pygame.draw.polygon(surface, COLOR_FLAME_MID, mid)

        # Núcleo (amarillo brillante)
        fw_core = fw_outer // 3
        fh_core = int(fh_outer * 0.4)
        core = [(cx - fw_core, base_y), (cx, base_y + fh_core), (cx + fw_core, base_y)]
        pygame.draw.polygon(surface, COLOR_FLAME_CORE, core)


# ============================================================================
# SLIDER CLASS
# ============================================================================

class SliderBox:
    """Slider drag widget for thrust percentage entry (0–100%)."""

    TRACK_H = 14
    KNOB_R  = 11

    def __init__(self, rect: pygame.Rect, index: int):
        self.rect = rect   # track rect
        self.index = index
        self.value = 0.0
        self.active = False
        self.dragging = False

    # ── internal helpers ────────────────────────────────────────
    def _value_from_x(self, x: int) -> float:
        # Snap a entero: lo que ve el estudiante en pantalla coincide con
        # el valor que se simula. Sin esto, un slider en "71.8%" se muestra
        # como "71%" pero internamente se usa 71.8 → la nave no aterriza
        # como anuncia la pantalla.
        ratio = (x - self.rect.left) / max(1, self.rect.width)
        return float(round(clamp_01(ratio) * 100.0))

    def _knob_x(self) -> int:
        return self.rect.left + int(self.rect.width * self.value / 100.0)

    def _fill_color(self):
        v = self.value
        if v < 20:   return COLOR_TEXT_DIM
        if v < 45:   return COLOR_SUCCESS
        if v < 70:   return COLOR_ACCENT
        return COLOR_THRUST

    # ── public API (matches old InputBox interface) ──────────────
    def get_value(self) -> float:
        return self.value

    def update(self, dt):
        pass

    def handle_event(self, event, on_next_field_callback=None):
        if event.type == pygame.MOUSEBUTTONDOWN:
            hit = self.rect.inflate(0, 18)
            if hit.collidepoint(event.pos):
                self.active = True
                self.dragging = True
                self.value = self._value_from_x(event.pos[0])
            else:
                self.active = False
                self.dragging = False

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.value = self._value_from_x(event.pos[0])

        elif event.type == pygame.KEYDOWN and self.active:
            step = 1 if (event.mod & pygame.KMOD_SHIFT) else 5
            if event.key == pygame.K_LEFT:
                self.value = max(0.0, self.value - step)
            elif event.key == pygame.K_RIGHT:
                self.value = min(100.0, self.value + step)
            elif event.key in (pygame.K_TAB, pygame.K_RETURN):
                self.active = False
                if on_next_field_callback:
                    on_next_field_callback(self.index)

    def draw(self, surface, font):
        cy  = self.rect.centery
        th  = self.TRACK_H
        kr  = self.KNOB_R
        kx  = self._knob_x()
        fc  = self._fill_color()

        # Track background
        track_rect = pygame.Rect(self.rect.x, cy - th // 2, self.rect.width, th)
        pygame.draw.rect(surface, COLOR_INPUT_BG, track_rect, border_radius=th // 2)

        # Filled portion
        if kx > self.rect.left:
            fill_rect = pygame.Rect(self.rect.x, cy - th // 2,
                                    kx - self.rect.left, th)
            pygame.draw.rect(surface, fc, fill_rect, border_radius=th // 2)

        # Track border
        pygame.draw.rect(surface, COLOR_ACCENT if self.active else COLOR_BORDER,
                         track_rect, 1, border_radius=th // 2)

        # Knob glow (active/drag)
        if self.active or self.dragging:
            gs = pygame.Surface((kr * 6, kr * 6), pygame.SRCALPHA)
            for gi in range(4, 0, -1):
                pygame.draw.circle(gs, (*fc, 30 // gi),
                                   (kr * 3, kr * 3), kr + gi * 3)
            surface.blit(gs, (kx - kr * 3, cy - kr * 3))

        # Knob ring + inner dot
        pygame.draw.circle(surface, fc,        (kx, cy), kr)
        pygame.draw.circle(surface, COLOR_BG,  (kx, cy), kr - 4)
        pygame.draw.circle(surface, fc,        (kx, cy), 5)
        if self.active:
            pygame.draw.circle(surface, COLOR_ACCENT, (kx, cy), kr + 2, 2)

        # Value label to the right of the track
        val_text = f"{int(self.value):3d}%"
        draw_text_left(surface, val_text, font, fc,
                       self.rect.right + 14, cy - 9)


# ============================================================================
# SCREEN CLASSES
# ============================================================================

class InputScreen:
    """Screen for inputting 10 thrust percentages via sliders."""

    # Layout constants
    _ROW_H    = 51         # height per slider row
    _LABEL_W  = 58         # width of "t=Ns" label
    _VAL_W    = 52         # width of "XXX%" label to the right
    _MARGIN_X = 115        # horizontal margin from window edge to label
    _TOP_Y    = 102        # y of first row center

    def __init__(self, app):
        self.app = app
        self.sliders: list[SliderBox] = []
        self.error_text = ""
        self.error_timer = 0.0

        # Slider track width fills the available space
        slider_x = self._MARGIN_X + self._LABEL_W + 12
        slider_w = WINDOW_WIDTH - slider_x - self._VAL_W - 28 - self._MARGIN_X

        for i in range(10):
            cy = self._TOP_Y + i * self._ROW_H
            rect = pygame.Rect(slider_x, cy - 10, slider_w, 20)
            self.sliders.append(SliderBox(rect, i))

        btn_w = 260
        btn_y = self._TOP_Y + 10 * self._ROW_H + 22
        self.button_rect = pygame.Rect(WINDOW_WIDTH // 2 - btn_w // 2, btn_y, btn_w, 50)

    def _on_next_field(self, current_index: int):
        next_index = (current_index + 1) % len(self.sliders)
        self.sliders[next_index].active = True

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_rect.collidepoint(event.pos):
                self._simulate()

        for sl in self.sliders:
            sl.handle_event(event, self._on_next_field)

    def _simulate(self):
        thrusts = [sl.get_value() for sl in self.sliders]
        states = physics.simulate(thrusts)
        self.app.go_to_simulation(states, thrusts)

    # keep old name so external code (if any) still works
    validate_and_simulate = _simulate

    def update(self, dt):
        self.error_timer -= dt
        for sl in self.sliders:
            sl.update(dt)

    def draw(self, surface):
        # ── Header panel ──────────────────────────────────────────
        header_rect = pygame.Rect(60, 10, WINDOW_WIDTH - 120, 76)
        draw_rounded_panel(surface, header_rect, COLOR_PANEL, 12)
        draw_glow(surface, header_rect, COLOR_ACCENT, layers=3, radius=12)
        pygame.draw.rect(surface, COLOR_ACCENT, header_rect, 1, border_radius=12)

        draw_text_centered(surface, "SIMULADOR DE ATERRIZAJE LUNAR",
                           self.app.font_title, COLOR_TEXT,
                           WINDOW_WIDTH // 2, 36)
        draw_text_centered(surface,
                           "Arrastra los sliders para configurar el empuje de cada segundo"
                           "  ·  ← → para ajuste fino  ·  Shift+← → paso de 1%",
                           self.app.font_small, COLOR_ACCENT,
                           WINDOW_WIDTH // 2, 66)

        # ── Panel de sliders ───────────────────────────────────────
        panel_rect = pygame.Rect(
            self._MARGIN_X - 14,
            self._TOP_Y - 22,
            WINDOW_WIDTH - (self._MARGIN_X - 14) * 2,
            10 * self._ROW_H + 10,
        )
        draw_rounded_panel(surface, panel_rect, COLOR_PANEL, 10)
        pygame.draw.rect(surface, COLOR_BORDER, panel_rect, 1, border_radius=10)

        # Separador decorativo a la mitad (entre t=5 y t=6)
        mid_y = self._TOP_Y + 5 * self._ROW_H - self._ROW_H // 2
        pygame.draw.line(surface, COLOR_BORDER,
                         (panel_rect.left + 20, mid_y),
                         (panel_rect.right - 20, mid_y), 1)

        # ── Filas: etiqueta + slider ───────────────────────────────
        for i, sl in enumerate(self.sliders):
            cy = self._TOP_Y + i * self._ROW_H
            lx = self._MARGIN_X

            # Fila de fondo alternada para legibilidad
            if i % 2 == 0:
                row_bg = pygame.Rect(panel_rect.left + 2, cy - self._ROW_H // 2 + 2,
                                     panel_rect.width - 4, self._ROW_H - 2)
                pygame.draw.rect(surface, COLOR_PANEL_DARK, row_bg, border_radius=6)

            # Etiqueta "t = Ns"
            draw_text_left(surface, f"t = {i + 1}s",
                           self.app.font_medium, COLOR_TEXT_DIM, lx, cy - 9)

            # Slider (dibuja también el valor a su derecha)
            sl.draw(surface, self.app.font_medium)

        # ── Panel de física ────────────────────────────────────────
        phys_y = panel_rect.bottom + 10
        phys_rect = pygame.Rect(self._MARGIN_X - 14, phys_y,
                                WINDOW_WIDTH - (self._MARGIN_X - 14) * 2, 36)
        draw_rounded_panel(surface, phys_rect, COLOR_PANEL_DARK, 8)
        pygame.draw.rect(surface, COLOR_BORDER, phys_rect, 1, border_radius=8)
        draw_text_centered(surface,
                           "Gravedad: 4 m/s²  ·  Empuje máx: 10 m/s²  ·  "
                           "Vel. segura: ≤ 3 m/s  ·  Altura inicial: 100 m",
                           self.app.font_small, COLOR_TEXT_DIM,
                           WINDOW_WIDTH // 2, phys_rect.centery)

        # ── Botón SIMULAR ──────────────────────────────────────────
        mouse = pygame.mouse.get_pos()
        hover = is_mouse_over_rect(mouse, self.button_rect)
        draw_rounded_panel(surface, self.button_rect,
                           COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_BG, 10)
        draw_glow(surface, self.button_rect,
                  COLOR_ACCENT if hover else COLOR_ACCENT_DIM, layers=3, radius=10)
        pygame.draw.rect(surface, COLOR_ACCENT, self.button_rect, 2, border_radius=10)
        draw_text_centered(surface, "  SIMULAR  ",
                           self.app.font_large, COLOR_TEXT,
                           self.button_rect.centerx, self.button_rect.centery)

        if self.error_timer > 0:
            draw_text_centered(surface, self.error_text,
                               self.app.font_small, COLOR_CRASH,
                               WINDOW_WIDTH // 2, self.button_rect.bottom + 14)


class SimulationScreen:
    """Screen showing the animated landing simulation."""

    VP_X = 310
    VP_Y = 80
    VP_W = WINDOW_WIDTH - 310 - 20
    VP_H = WINDOW_HEIGHT - 100

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
        pass

    def update(self, dt):
        if self.done:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self.app.go_to_result(self.states, self.thrusts)
            return

        self.step_t += dt
        alpha = clamp_01(self.step_t / ANIM_DURATION_PER_STEP)

        if self.current_step < len(self.states) - 1:
            h_from = self.states[self.current_step]['h']
            h_to   = self.states[self.current_step + 1]['h']
            self.current_h = lerp(h_from, h_to, alpha)

            v_from = self.states[self.current_step]['v']
            v_to   = self.states[self.current_step + 1]['v']
            self.current_v = lerp(v_from, v_to, alpha)

        if self.step_t >= ANIM_DURATION_PER_STEP:
            self.step_t = 0.0
            self.current_step += 1
            if self.current_step >= len(self.states) - 1:
                self.done = True
            elif self.states[self.current_step]['outcome'] is not None:
                self.done = True

    def _draw_time_progress(self, surface):
        """Barra de progreso continua: se llena suavemente con la simulación."""
        bar_x = self.VP_X
        bar_y = 16
        bar_w = self.VP_W
        bar_h = 12
        radius = bar_h // 2

        # Progreso real: paso actual + fracción del paso en curso
        total_steps = len(self.states) - 1
        progress = clamp_01(
            (self.current_step + clamp_01(self.step_t / ANIM_DURATION_PER_STEP))
            / max(total_steps, 1)
        )

        track_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)

        # Fondo
        pygame.draw.rect(surface, COLOR_PANEL, track_rect, border_radius=radius)

        # Relleno
        fill_w = max(radius * 2, int(bar_w * progress))
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
        pygame.draw.rect(surface, COLOR_ACCENT, fill_rect, border_radius=radius)

        # Borde exterior
        pygame.draw.rect(surface, COLOR_BORDER, track_rect, 1, border_radius=radius)

        # Punto luminoso en el frente del relleno
        tip_x = bar_x + fill_w
        glow = int(abs(math.sin(self.app.time * 5)) * 60 + 160)
        tip_color = (glow, min(255, glow + 40), 255)
        pygame.draw.circle(surface, tip_color, (tip_x, bar_y + bar_h // 2), bar_h // 2)

    def _draw_telemetry_panel(self, surface):
        """Panel izquierdo con telemetría detallada."""
        px, py = 12, 50
        pw, ph = 285, WINDOW_HEIGHT - 65

        draw_rounded_panel(surface, pygame.Rect(px, py, pw, ph), COLOR_PANEL, 8)
        pygame.draw.rect(surface, COLOR_ACCENT, pygame.Rect(px, py, pw, ph),
                         1, border_radius=8)

        # Título
        draw_text_centered(surface, "TELEMETRIA",
                           self.app.font_medium, COLOR_ACCENT,
                           px + pw // 2, py + 20)

        # Separador
        pygame.draw.line(surface, COLOR_BORDER,
                         (px + 15, py + 38), (px + pw - 15, py + 38))

        y = py + 52

        # Altura
        draw_text_left(surface, "↕  ALTURA",
                       self.app.font_small, COLOR_TEXT_DIM, px + 15, y)
        y += 20
        h_color = COLOR_SUCCESS if self.current_h > 10 else COLOR_WARNING
        draw_text_left(surface, f"{self.current_h:.1f} m",
                       self.app.font_large, h_color, px + 15, y)
        y += 38

        # Barra de altura
        h_bar = pygame.Rect(px + 15, y, pw - 30, 10)
        draw_progress_bar(surface, h_bar, self.current_h / 100.0,
                          COLOR_SUCCESS if self.current_h > 10 else COLOR_WARNING)
        y += 22

        # Velocidad
        draw_text_left(surface, "⚡ VELOCIDAD",
                       self.app.font_small, COLOR_TEXT_DIM, px + 15, y)
        y += 20
        spd = abs(self.current_v)
        vel_color = (COLOR_SUCCESS if spd <= 3 else
                     COLOR_WARNING if spd <= 7 else COLOR_CRASH)
        draw_text_left(surface, f"{self.current_v:+.1f} m/s",
                       self.app.font_large, vel_color, px + 15, y)
        y += 38

        # Barra de velocidad (peligro: verde→rojo)
        v_bar = pygame.Rect(px + 15, y, pw - 30, 10)
        v_ratio = clamp_01(spd / 10.0)
        draw_progress_bar(surface, v_bar, v_ratio, vel_color)
        y += 22

        # Empuje
        current_thrust = (self.states[self.current_step]['thrust']
                          if self.current_step < len(self.states) else 0)
        draw_text_left(surface, "🔥 EMPUJE",
                       self.app.font_small, COLOR_TEXT_DIM, px + 15, y)
        y += 20
        draw_text_left(surface, f"{current_thrust:.0f}%",
                       self.app.font_large, COLOR_THRUST, px + 15, y)
        y += 38

        # Barra de empuje
        t_bar = pygame.Rect(px + 15, y, pw - 30, 10)
        draw_progress_bar(surface, t_bar, current_thrust / 100.0, COLOR_THRUST)
        y += 26

        # Tiempo
        draw_text_left(surface, "⏱ TIEMPO",
                       self.app.font_small, COLOR_TEXT_DIM, px + 15, y)
        y += 20
        draw_text_left(surface, f"{min(self.current_step, 10)} / 10 s",
                       self.app.font_large, COLOR_TEXT, px + 15, y)
        y += 50

        # Separador
        pygame.draw.line(surface, COLOR_BORDER,
                         (px + 15, y), (px + pw - 15, y))
        y += 15

        # Parámetros de referencia
        draw_text_left(surface, "Referencia",
                       self.app.font_small, COLOR_TEXT_DIM, px + 15, y)
        y += 20
        draw_text_left(surface, "Vel. segura: ≤ 3 m/s",
                       self.app.font_tiny, COLOR_SUCCESS, px + 15, y)
        y += 18
        draw_text_left(surface, "Gravedad: -4 m/s²",
                       self.app.font_tiny, COLOR_TEXT_DIM, px + 15, y)
        y += 18
        draw_text_left(surface, "Empuje 40% = hover",
                       self.app.font_tiny, COLOR_TEXT_DIM, px + 15, y)

    def _draw_space_viewport(self, surface):
        """Viewport de espacio con cohete, plataforma y grid de altitud."""
        vx, vy = self.VP_X, self.VP_Y
        vw, vh = self.VP_W, self.VP_H

        # Fondo de viewport
        vp_rect = pygame.Rect(vx, vy, vw, vh)
        draw_rounded_panel(surface, vp_rect, COLOR_BG_PANEL, 8)
        pygame.draw.rect(surface, COLOR_BORDER, vp_rect, 1, border_radius=8)

        # Estrellas con twinkle (dentro del viewport)
        for (sx, sy, sr, sphase) in self.app.stars:
            mapped_x = vx + (sx % vw)
            mapped_y = vy + (sy % vh)
            twinkle_r = max(1, sr + int(math.sin(self.app.time * 2 + sphase) * 0.5 + 0.5))
            pygame.draw.circle(surface, COLOR_STAR, (mapped_x, mapped_y), twinkle_r)

        # Grid de altitud horizontal (cada 20 m)
        for alt in range(0, 101, 20):
            gy = int(height_to_screen_y(alt, vy, vh))
            if vy < gy < vy + vh:
                line_color = COLOR_BORDER
                pygame.draw.line(surface, line_color, (vx + 5, gy), (vx + vw - 5, gy), 1)
                label = f"{alt}m"
                draw_text_right(surface, label, self.app.font_tiny,
                                COLOR_TEXT_DIM, vx + vw - 8, gy - 12)

        # Plataforma de aterrizaje
        pad_y = int(height_to_screen_y(0, vy, vh))
        pad_rect = pygame.Rect(vx + 60, pad_y, vw - 120, 18)
        pygame.draw.rect(surface, COLOR_PAD, pad_rect, border_radius=3)
        # Franjas de la plataforma
        stripe_w = 20
        stripe_gap = 40
        for sx in range(pad_rect.left + 10, pad_rect.right - 10, stripe_gap):
            sr = pygame.Rect(sx, pad_y + 4, stripe_w, 10)
            if sr.right < pad_rect.right - 5:
                pygame.draw.rect(surface, COLOR_PAD_STRIPE, sr)
        pygame.draw.rect(surface, COLOR_ACCENT, pad_rect, 2, border_radius=3)

        # Cohete
        rocket_cx = vx + vw // 2
        raw_cy = height_to_screen_y(self.current_h, vy, vh)
        rocket_cy = max(vy + 20, min(vy + vh - 30, raw_cy))

        current_thrust = (self.states[self.current_step]['thrust']
                          if self.current_step < len(self.states) else 0)
        draw_rocket(surface, rocket_cx, rocket_cy,
                    current_thrust, self.app.time)

        # Flash de choque
        if self.done and self.states[-1]['outcome'] == "CHOQUE":
            flash_alpha = int(clamp_01(self.transition_timer / 2.5) * 140)
            flash_surf = pygame.Surface((vw, vh))
            flash_surf.fill(COLOR_CRASH)
            flash_surf.set_alpha(flash_alpha)
            surface.blit(flash_surf, (vx, vy))

    def draw(self, surface):
        # Cabecera
        draw_text_left(surface, "SIMULANDO...",
                       self.app.font_large, COLOR_ACCENT, 12, 18)
        self._draw_time_progress(surface)
        self._draw_telemetry_panel(surface)
        self._draw_space_viewport(surface)


class ResultScreen:
    """Screen showing landing results."""

    def __init__(self, app, states: list[dict], thrusts: list[float]):
        self.app = app
        self.states = states
        self.thrusts = thrusts
        self.outcome = physics.classify_outcome(states)
        self.fade_timer = 0.5
        btn_w = 260
        self.button_rect = pygame.Rect(
            WINDOW_WIDTH // 2 - btn_w // 2, 660, btn_w, 52)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_rect.collidepoint(event.pos):
                self.app.go_to_input()

    def update(self, dt):
        self.fade_timer = max(0.0, self.fade_timer - dt)

    def draw(self, surface):
        # Tinte de resultado en toda la pantalla
        if self.outcome == "EXITO":
            tint = (COLOR_SUCCESS[0], COLOR_SUCCESS[1], COLOR_SUCCESS[2])
            title = "¡ ATERRIZAJE EXITOSO !"
            title_color = COLOR_SUCCESS
        elif self.outcome == "CHOQUE":
            tint = (COLOR_CRASH[0], COLOR_CRASH[1], COLOR_CRASH[2])
            title = "¡ CHOQUE !  NAVE DESTRUIDA"
            title_color = COLOR_CRASH
        else:
            tint = (COLOR_WARNING[0], COLOR_WARNING[1], COLOR_WARNING[2])
            title = "SIN ATERRIZAJE"
            title_color = COLOR_WARNING

        tint_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        tint_surf.fill(tint)
        tint_surf.set_alpha(18)
        surface.blit(tint_surf, (0, 0))

        # Fade-in
        if self.fade_timer > 0:
            alpha = int((self.fade_timer / 0.5) * 200)
            fade_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(alpha)
            surface.blit(fade_surf, (0, 0))

        # ── Título ─────────────────────────────────────────────────
        title_rect = pygame.Rect(60, 15, WINDOW_WIDTH - 120, 75)
        draw_rounded_panel(surface, title_rect, COLOR_PANEL, 12)
        draw_glow(surface, title_rect, title_color, layers=4, radius=12)
        pygame.draw.rect(surface, title_color, title_rect, 2, border_radius=12)
        draw_text_centered(surface, title, self.app.font_title, title_color,
                           WINDOW_WIDTH // 2, title_rect.centery)

        # ── Panel de estadísticas ──────────────────────────────────
        stats_rect = pygame.Rect(60, 105, 400, 230)
        draw_rounded_panel(surface, stats_rect, COLOR_PANEL, 10)
        pygame.draw.rect(surface, COLOR_BORDER, stats_rect, 1, border_radius=10)

        final_h = self.states[-1]['h']
        final_v = self.states[-1]['v']
        final_t = self.states[-1]['t']

        sy = stats_rect.top + 16
        draw_text_left(surface, "ESTADÍSTICAS FINALES",
                       self.app.font_medium, COLOR_ACCENT,
                       stats_rect.left + 20, sy)
        sy += 34

        pygame.draw.line(surface, COLOR_BORDER,
                         (stats_rect.left + 15, sy - 4),
                         (stats_rect.right - 15, sy - 4))

        rows = [
            ("↕  Altura final", f"{final_h:.1f} m",
             COLOR_SUCCESS if final_h < 1 else COLOR_WARNING),
            ("⚡ Velocidad impacto", f"{final_v:+.1f} m/s",
             COLOR_SUCCESS if abs(final_v) <= 3 else COLOR_CRASH),
            ("⏱  Tiempo total", f"{final_t} s", COLOR_TEXT),
            ("🚀 Resultado", self.outcome, title_color),
        ]

        for label, value, vc in rows:
            draw_text_left(surface, label, self.app.font_small,
                           COLOR_TEXT_DIM, stats_rect.left + 20, sy)
            draw_text_right(surface, value, self.app.font_medium,
                            vc, stats_rect.right - 20, sy - 2)
            sy += 38

        # ── Panel de secuencia de empujes ──────────────────────────
        seq_rect = pygame.Rect(480, 105, WINDOW_WIDTH - 540, 230)
        draw_rounded_panel(surface, seq_rect, COLOR_PANEL, 10)
        pygame.draw.rect(surface, COLOR_BORDER, seq_rect, 1, border_radius=10)

        draw_text_left(surface, "SECUENCIA DE EMPUJE",
                       self.app.font_medium, COLOR_ACCENT,
                       seq_rect.left + 20, seq_rect.top + 16)

        bar_w = (seq_rect.width - 40) // 10 - 4
        bar_max_h = 100
        bar_base_y = seq_rect.top + 185
        bar_start_x = seq_rect.left + 20

        for i, thrust in enumerate(self.thrusts):
            bx = bar_start_x + i * (bar_w + 4)
            if thrust < 20:
                bc = COLOR_TEXT_DIM
            elif thrust < 45:
                bc = COLOR_SUCCESS
            elif thrust < 70:
                bc = COLOR_ACCENT
            else:
                bc = COLOR_THRUST

            filled_h = max(4, int((thrust / 100.0) * bar_max_h))
            # Fondo de barra
            bg_rect = pygame.Rect(bx, bar_base_y - bar_max_h, bar_w, bar_max_h)
            pygame.draw.rect(surface, COLOR_PANEL_DARK, bg_rect, border_radius=3)
            pygame.draw.rect(surface, COLOR_BORDER, bg_rect, 1, border_radius=3)
            # Relleno
            fill_rect = pygame.Rect(bx, bar_base_y - filled_h, bar_w, filled_h)
            pygame.draw.rect(surface, bc, fill_rect, border_radius=3)
            # Valor
            val_text = f"{int(thrust)}"
            draw_text_centered(surface, val_text, self.app.font_tiny, bc,
                               bx + bar_w // 2, bar_base_y - bar_max_h - 12)
            # Etiqueta t=N
            draw_text_centered(surface, f"t{i+1}", self.app.font_tiny,
                               COLOR_TEXT_DIM, bx + bar_w // 2, bar_base_y + 4)

        # ── Mensaje educativo ──────────────────────────────────────
        edu_rect = pygame.Rect(60, 348, WINDOW_WIDTH - 120, 50)
        draw_rounded_panel(surface, edu_rect, COLOR_PANEL_DARK, 8)
        pygame.draw.rect(surface, COLOR_BORDER, edu_rect, 1, border_radius=8)

        if self.outcome == "EXITO":
            seq_str = "[" + ", ".join(str(int(t)) for t in self.thrusts) + "]"
            edu_msg = f"Secuencia: {seq_str}"
            edu_color = COLOR_SUCCESS
        elif self.outcome == "CHOQUE":
            edu_msg = (f"La nave chocó a {abs(final_v):.1f} m/s  "
                       f"(velocidad segura: ≤ 3 m/s).  ¡Intenta frenar antes!")
            edu_color = COLOR_CRASH
        else:
            edu_msg = ("La nave nunca llegó al suelo.  "
                       "Prueba con menos empuje en los últimos segundos.")
            edu_color = COLOR_WARNING

        draw_text_centered(surface, edu_msg, self.app.font_small, edu_color,
                           WINDOW_WIDTH // 2, edu_rect.centery)

        # ── Gráficas de simulación ─────────────────────────────────
        self._draw_simulation_graphs(surface)

        # ── Botón ──────────────────────────────────────────────────
        mouse = pygame.mouse.get_pos()
        hover = is_mouse_over_rect(mouse, self.button_rect)
        btn_color = COLOR_BUTTON_HOVER if hover else COLOR_BUTTON_BG
        draw_rounded_panel(surface, self.button_rect, btn_color, 10)
        draw_glow(surface, self.button_rect,
                  COLOR_ACCENT if hover else COLOR_ACCENT_DIM, layers=3, radius=10)
        pygame.draw.rect(surface, COLOR_ACCENT, self.button_rect, 2, border_radius=10)
        draw_text_centered(surface, "INTENTAR DE NUEVO",
                           self.app.font_large, COLOR_TEXT,
                           self.button_rect.centerx, self.button_rect.centery)

    def _draw_mini_chart(self, surface, rect, title,
                         x_vals, y_vals, y_min, y_max, line_color,
                         safe_band=None):
        """Dibuja una mini gráfica de línea dentro de rect.
        safe_band=(y_lo, y_hi) resalta una banda horizontal (p.ej. zona segura de velocidad).
        """
        font = self.app.font_tiny
        ml, mr, mt, mb = 36, 8, 20, 17
        pw = rect.width - ml - mr
        ph = rect.height - mt - mb
        px0, py0 = rect.x + ml, rect.y + mt
        x_min, x_max = min(x_vals), max(x_vals)
        x_rng = (x_max - x_min) or 1
        y_rng = (y_max - y_min) or 1

        def sp(xi, yi):
            sx = px0 + int((xi - x_min) / x_rng * pw)
            sy = py0 + ph - int((yi - y_min) / y_rng * ph)
            return sx, max(py0, min(py0 + ph, sy))

        # Panel de fondo
        draw_rounded_panel(surface, rect, COLOR_PANEL, 6)
        pygame.draw.rect(surface, COLOR_BORDER, rect, 1, border_radius=6)

        # Título
        draw_text_centered(surface, title, font, COLOR_ACCENT,
                           rect.centerx, rect.y + 10)

        # Banda de zona segura (para velocidad)
        if safe_band:
            blo, bhi = safe_band
            _, y_top = sp(x_min, min(bhi, y_max))
            _, y_bot = sp(x_min, max(blo, y_min))
            if y_bot > y_top:
                bsurf = pygame.Surface((pw, y_bot - y_top), pygame.SRCALPHA)
                bsurf.fill((50, 220, 100, 28))
                surface.blit(bsurf, (px0, y_top))
                # Líneas punteadas en los bordes de la banda
                pygame.draw.line(surface, (*COLOR_SUCCESS, 80),
                                 (px0, y_top), (px0 + pw, y_top), 1)
                pygame.draw.line(surface, (*COLOR_SUCCESS, 80),
                                 (px0, y_bot), (px0 + pw, y_bot), 1)

        # Grid horizontal
        n_ticks = 4
        for i in range(n_ticks + 1):
            gy_grid = py0 + i * ph // n_ticks
            pygame.draw.line(surface, COLOR_BORDER,
                             (px0, gy_grid), (px0 + pw, gy_grid))
            yval = y_max - i * y_rng / n_ticks
            draw_text_right(surface, f"{yval:.0f}", font,
                            COLOR_TEXT_DIM, px0 - 2, gy_grid - 6)

        # Eje X inferior
        pygame.draw.line(surface, COLOR_BORDER,
                         (px0, py0 + ph), (px0 + pw, py0 + ph))

        # Etiquetas eje X
        step_x = max(1, int(x_max) // 2)
        for xi_lbl in range(0, int(x_max) + 1, step_x):
            lx = px0 + int((xi_lbl - x_min) / x_rng * pw)
            draw_text_centered(surface, str(xi_lbl), font,
                               COLOR_TEXT_DIM, lx, py0 + ph + 7)

        if len(x_vals) < 2:
            return

        pts = [sp(xi, yi) for xi, yi in zip(x_vals, y_vals)]

        # Relleno bajo la curva (transparente)
        zero_y = sp(x_min, max(y_min, min(0.0, y_max)))[1]
        poly = [(pts[0][0], zero_y)] + pts + [(pts[-1][0], zero_y)]
        fill_s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        local_poly = [(p[0] - rect.x, p[1] - rect.y) for p in poly]
        pygame.draw.polygon(fill_s, (*line_color, 38), local_poly)
        surface.blit(fill_s, rect.topleft)

        # Línea de datos
        pygame.draw.lines(surface, line_color, False, pts, 2)

        # Puntos de datos (coloreados por seguridad en gráfica de velocidad)
        for i, (sx, sy) in enumerate(pts):
            dot_c = line_color
            if safe_band is not None:
                v = y_vals[i]
                dot_c = (COLOR_SUCCESS if abs(v) <= 3
                         else COLOR_WARNING if abs(v) <= 7
                         else COLOR_CRASH)
            pygame.draw.circle(surface, dot_c, (sx, sy), 3)
            pygame.draw.circle(surface, COLOR_BG, (sx, sy), 1)

    def _draw_simulation_graphs(self, surface):
        """Tres gráficas de medición debajo del mensaje educativo."""
        t_vals  = [s['t']      for s in self.states]
        h_vals  = [s['h']      for s in self.states]
        v_vals  = [s['v']      for s in self.states]
        emp_vals = [s['thrust'] for s in self.states]

        margin_x = 60
        gy   = 408
        gh   = 240
        gap  = 10
        gw   = (WINDOW_WIDTH - margin_x * 2 - gap * 2) // 3

        v_min = min(v_vals) - 1.0
        v_max = max(max(v_vals), 3.0) + 0.5

        charts = [
            (pygame.Rect(margin_x, gy, gw, gh),
             "ALTURA  (m)",
             t_vals, h_vals, 0.0, 105.0, COLOR_SUCCESS, None),
            (pygame.Rect(margin_x + gw + gap, gy, gw, gh),
             "VELOCIDAD  (m/s)",
             t_vals, v_vals, v_min, v_max, COLOR_ACCENT, (-3.0, 3.0)),
            (pygame.Rect(margin_x + 2 * (gw + gap), gy, gw, gh),
             "EMPUJE  (%)",
             t_vals, emp_vals, 0.0, 105.0, COLOR_THRUST, None),
        ]

        for rect, title, xv, yv, ymn, ymx, col, sband in charts:
            self._draw_mini_chart(surface, rect, title,
                                  xv, yv, ymn, ymx, col, sband)


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
        self.time = 0.0

        # Fuentes
        font_candidates = ["Arial", "Helvetica", "DejaVu Sans", "FreeSans"]
        chosen = None
        for name in font_candidates:
            try:
                test = pygame.font.SysFont(name, 20)
                if test:
                    chosen = name
                    break
            except Exception:
                pass

        if chosen:
            self.font_title  = pygame.font.SysFont(chosen, 40, bold=True)
            self.font_large  = pygame.font.SysFont(chosen, 30, bold=True)
            self.font_medium = pygame.font.SysFont(chosen, 21)
            self.font_small  = pygame.font.SysFont(chosen, 16)
            self.font_tiny   = pygame.font.SysFont(chosen, 13)
        else:
            self.font_title  = pygame.font.Font(None, 44)
            self.font_large  = pygame.font.Font(None, 34)
            self.font_medium = pygame.font.Font(None, 24)
            self.font_small  = pygame.font.Font(None, 18)
            self.font_tiny   = pygame.font.Font(None, 14)

        self.stars = build_stars(250)
        self.current_screen = InputScreen(self)

    def go_to_simulation(self, states: list[dict], thrusts: list[float]):
        self.current_screen = SimulationScreen(self, states, thrusts)

    def go_to_result(self, states: list[dict], thrusts: list[float]):
        self.current_screen = ResultScreen(self, states, thrusts)

    def go_to_input(self):
        self.current_screen = InputScreen(self)

    def draw_background(self):
        """Fondo con estrellas titilantes."""
        self.screen.fill(COLOR_BG)
        for (x, y, r, phase) in self.stars:
            brightness = int(180 + math.sin(self.time * 1.5 + phase) * 60)
            brightness = max(100, min(255, brightness))
            star_color = (brightness, brightness, min(255, brightness + 20))
            twinkle_r = max(1, r + int(math.sin(self.time * 2.5 + phase) * 0.6 + 0.6))
            pygame.draw.circle(self.screen, star_color, (x, y), twinkle_r)

    def run(self):
        """Main game loop."""
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            self.time += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.current_screen.handle_event(event)

            self.current_screen.update(dt)

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
