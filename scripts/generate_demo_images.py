"""
Genera imágenes demostrativas para el README.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from physics import simulate, classify_outcome

# Configuración de estilo
plt.style.use('dark_background')
FIGSIZE = (14, 5)
DPI = 100

# Estrategia exitosa (verificada con la física actual: V0=0, integración exacta)
winning_strategy = [0, 0, 0, 0, 37, 52, 56, 84, 71, 100]
states = simulate(winning_strategy)

# ============================================================================
# IMAGEN 1: Gráficos de altura, velocidad y empuje
# ============================================================================

fig, axes = plt.subplots(1, 3, figsize=FIGSIZE, dpi=DPI)
fig.suptitle('Simulación: Atterrizaje Exitoso', fontsize=16, fontweight='bold')

times = [s['t'] for s in states]
heights = [s['h'] for s in states]
velocities = [s['v'] for s in states]
thrusts = [s['thrust'] for s in states]

# Altura vs tiempo
ax = axes[0]
ax.plot(times, heights, 'o-', linewidth=3, markersize=8, color='#00ff00')
ax.axhline(y=0, color='#ff4444', linestyle='--', linewidth=2, label='Superficie')
ax.fill_between(times, heights, 0, alpha=0.2, color='#00ff00')
ax.set_xlabel('Tiempo (s)', fontsize=11, fontweight='bold')
ax.set_ylabel('Altura (m)', fontsize=11, fontweight='bold')
ax.set_title('Altura vs Tiempo', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.set_ylim(-5, 110)

# Velocidad vs tiempo
ax = axes[1]
colors = ['#ff4444' if v < -6 else '#ffaa00' if v < -3 else '#00ff00' for v in velocities]
ax.plot(times, velocities, 'o-', linewidth=3, markersize=8, color='#4488ff')
ax.axhline(y=-3, color='#00ff00', linestyle='--', linewidth=2, label='Límite seguro')
ax.axhline(y=3, color='#00ff00', linestyle='--', linewidth=2)
ax.fill_between(times, -3, 3, alpha=0.1, color='#00ff00')
ax.set_xlabel('Tiempo (s)', fontsize=11, fontweight='bold')
ax.set_ylabel('Velocidad (m/s)', fontsize=11, fontweight='bold')
ax.set_title('Velocidad vs Tiempo', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(loc='lower right')

# Empuje vs tiempo
ax = axes[2]
colors_thrust = ['#ff6600' if t > 80 else '#ffaa00' if t > 40 else '#666666' for t in thrusts]
bars = ax.bar(times, thrusts, width=0.8, color=colors_thrust, edgecolor='white', linewidth=1.5)
ax.axhline(y=40, color='#00ff00', linestyle='--', linewidth=2, label='Punto hover')
ax.set_xlabel('Tiempo (s)', fontsize=11, fontweight='bold')
ax.set_ylabel('Empuje (%)', fontsize=11, fontweight='bold')
ax.set_title('Empuje vs Tiempo', fontsize=12, fontweight='bold')
ax.set_ylim(0, 110)
ax.grid(True, alpha=0.3, axis='y')
ax.legend()

plt.tight_layout()
plt.savefig('demo_graphs.png', dpi=DPI, bbox_inches='tight', facecolor='#0a0a1a')
print("OK: demo_graphs.png saved")
plt.close()

# ============================================================================
# IMAGEN 2: Visualización del atterrizaje (5 momentos clave)
# ============================================================================

fig, axes = plt.subplots(1, 5, figsize=(16, 3), dpi=DPI)
fig.suptitle('Secuencia de Atterrizaje: 5 momentos clave', fontsize=14, fontweight='bold')

key_times = [0, 2, 4, 6, 8]  # Momentos clave

for idx, t in enumerate(key_times):
    ax = axes[idx]
    state = states[t]

    # Cielo
    ax.add_patch(patches.Rectangle((0, 0), 100, 100, facecolor='#0a0a2a', edgecolor='none'))

    # Estrellas
    np.random.seed(42)
    for _ in range(15):
        x, y = np.random.uniform(0, 100, 2)
        ax.plot(x, y, 'o', color='#ffff88', markersize=2, alpha=0.8)

    # Suelo
    ax.add_patch(patches.Rectangle((0, 0), 100, 5, facecolor='#444466', edgecolor='#aabbff', linewidth=2))

    # Nave (simplificada)
    h = state['h']
    if h < 5:
        y_pos = 5 + h
    else:
        y_pos = h

    # Cuerpo
    ax.add_patch(patches.Rectangle((45, y_pos - 3), 10, 6, facecolor='#4488ff', edgecolor='white', linewidth=1))
    # Nariz
    triangle = patches.Polygon([[45, y_pos + 3], [50, y_pos + 6], [55, y_pos + 3]],
                               facecolor='#4488ff', edgecolor='white', linewidth=1)
    ax.add_patch(triangle)

    # Llama
    if state['thrust'] > 5:
        flame_h = (state['thrust'] / 100) * 8
        flame = patches.Polygon([[45, y_pos - 3], [50, y_pos - 3 - flame_h], [55, y_pos - 3]],
                               facecolor='#ff6600', edgecolor='#ffaa00', linewidth=1)
        ax.add_patch(flame)

    # Info
    ax.text(50, 95, f"t = {t}s", ha='center', fontsize=12, fontweight='bold', color='#00ff00')
    ax.text(50, 88, f"h = {state['h']:.1f}m", ha='center', fontsize=10, color='#aabbff')
    ax.text(50, 81, f"v = {state['v']:.1f}m/s", ha='center', fontsize=10, color='#ffaa00')
    ax.text(50, 74, f"emp = {state['thrust']:.0f}%", ha='center', fontsize=10, color='#ff6600')

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect('equal')
    ax.axis('off')

plt.tight_layout()
plt.savefig('demo_sequence.png', dpi=DPI, bbox_inches='tight', facecolor='#0a0a1a')
print("OK: demo_sequence.png saved")
plt.close()

# ============================================================================
# IMAGEN 3: Tabla de estrategias exitosas
# ============================================================================

fig, ax = plt.subplots(figsize=(14, 6), dpi=DPI)
ax.axis('tight')
ax.axis('off')

strategies_list = [
    ("Aterrizaje suave",   [0, 0, 0, 0, 37, 52, 56, 84, 71, 100], "v=0.0 m/s al tocar"),
    ("Frenada equilibrada",[0, 0, 0, 0, 51, 42, 50, 66, 95, 96], "Empuje temprano y final fuerte"),
    ("Curva creciente",    [0, 0, 0, 0, 32, 57, 54, 80, 90, 87], "Empuje crece gradualmente"),
    ("Frenado tardío",     [0, 0, 0, 0, 30, 63, 66, 62, 77, 100], "Picos al final"),
    ("Empuje constante",   [0, 0, 0, 0, 35, 50, 71, 71, 71, 100], "Meseta de 71% estable"),
]

table_data = []
for nombre, strategy, descripcion in strategies_list:
    strategy_str = " → ".join([f"{v}%" for v in strategy])
    table_data.append([nombre, strategy_str, descripcion])

table = ax.table(cellText=table_data,
                colLabels=['Nombre', 'Secuencia de Empuje (s0 a s9)', 'Descripción'],
                cellLoc='left',
                loc='center',
                colWidths=[0.15, 0.65, 0.2])

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2.5)

# Estilo de la tabla
for i in range(len(table_data) + 1):
    for j in range(3):
        cell = table[(i, j)]
        if i == 0:
            cell.set_facecolor('#1a3a5a')
            cell.set_text_props(weight='bold', color='white')
        else:
            cell.set_facecolor('#0a0a1a' if i % 2 == 0 else '#151530')
            cell.set_text_props(color='#aabbff')
        cell.set_edgecolor('#4488ff')
        cell.set_linewidth(1.5)

fig.suptitle('5 Estrategias de Atterrizaje Exitoso', fontsize=16, fontweight='bold', color='#00ff00', y=0.98)
plt.savefig('demo_strategies.png', dpi=DPI, bbox_inches='tight', facecolor='#0a0a1a')
print("OK: demo_strategies.png saved")
plt.close()

print("\nOK: All images generated successfully")
