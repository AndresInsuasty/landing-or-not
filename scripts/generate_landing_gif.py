"""
Genera un GIF animado de un atterrizaje exitoso.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from physics import simulate
from PIL import Image
import io

# Estrategia ganadora (verificada con la física actual: V0=0, integración exacta).
# Secuencia robusta: tolera desviaciones de ±1% en cualquier slider.
winning_strategy = [0, 0, 0, 0, 36, 45, 52, 93, 94, 75]
states = simulate(winning_strategy)

print("Generando frames para GIF...")

frames = []

# Configurar estilo
plt.style.use('dark_background')

# Crear frames para cada segundo
for i, state in enumerate(states):
    fig, ax = plt.subplots(figsize=(10, 8), dpi=80)

    # Fondo (cielo)
    ax.add_patch(patches.Rectangle((0, 0), 100, 100,
                                   facecolor='#0a0a2a', edgecolor='none'))

    # Estrellas
    np.random.seed(42)
    for _ in range(20):
        x, y = np.random.uniform(0, 100, 2)
        ax.plot(x, y, 'o', color='#ffff88', markersize=2, alpha=0.8)

    # Suelo
    ax.add_patch(patches.Rectangle((0, 0), 100, 5,
                                   facecolor='#444466', edgecolor='#aabbff', linewidth=3))
    ax.text(50, 2.5, 'LUNAR SURFACE', ha='center', va='center',
            fontsize=10, color='#aabbff', fontweight='bold')

    # Nave (procedural)
    h = max(5, state['h'])  # Minimo de 5 para que se vea en el suelo

    # Cuerpo
    ax.add_patch(patches.Rectangle((45, h - 3), 10, 6,
                                   facecolor='#4488ff', edgecolor='white', linewidth=2))

    # Nariz
    nose = patches.Polygon([[45, h + 3], [50, h + 6], [55, h + 3]],
                          facecolor='#4488ff', edgecolor='white', linewidth=2)
    ax.add_patch(nose)

    # Aletas
    left_fin = patches.Polygon([[43, h - 1], [40, h + 2], [43, h + 2]],
                              facecolor='#4488ff', edgecolor='white', linewidth=1)
    right_fin = patches.Polygon([[57, h - 1], [60, h + 2], [57, h + 2]],
                               facecolor='#4488ff', edgecolor='white', linewidth=1)
    ax.add_patch(left_fin)
    ax.add_patch(right_fin)

    # Llama de los motores
    if state['thrust'] > 5:
        flame_height = (state['thrust'] / 100) * 12

        # Llama exterior (naranja)
        outer_flame = patches.Polygon([[42, h - 3], [50, h - 3 - flame_height], [58, h - 3]],
                                     facecolor='#ff6600', edgecolor='#ffaa00', linewidth=2)
        ax.add_patch(outer_flame)

        # Llama interior (amarilla)
        inner_flame = patches.Polygon([[46, h - 3], [50, h - 3 - flame_height * 0.6], [54, h - 3]],
                                     facecolor='#ffaa00', edgecolor='#ffdd00', linewidth=1)
        ax.add_patch(inner_flame)

    # Panel de informacion
    info_x = 5
    info_y = 80

    # Titulo
    ax.text(info_x + 45, 95, 'LUNAR LANDING SIMULATOR', ha='center',
            fontsize=14, color='#00ff00', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#000000', alpha=0.7))

    # Telemetria
    ax.text(info_x, info_y, f'Time:    {state["t"]:2d}s / 10s',
            fontsize=11, color='#aabbff', family='monospace',
            bbox=dict(boxstyle='round', facecolor='#0a0a1a', alpha=0.8))

    ax.text(info_x, info_y - 7, f'Height:  {state["h"]:6.1f}m',
            fontsize=11, color='#aabbff', family='monospace',
            bbox=dict(boxstyle='round', facecolor='#0a0a1a', alpha=0.8))

    vel_color = '#00ff00' if abs(state['v']) <= 3 else '#ffaa00' if abs(state['v']) <= 6 else '#ff4444'
    ax.text(info_x, info_y - 14, f'Velocity:{state["v"]:7.1f}m/s',
            fontsize=11, color=vel_color, family='monospace', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#0a0a1a', alpha=0.8))

    thrust_color = '#ff6600' if state['thrust'] > 80 else '#ffaa00' if state['thrust'] > 40 else '#666666'
    ax.text(info_x, info_y - 21, f'Thrust:  {state["thrust"]:5.0f}%',
            fontsize=11, color=thrust_color, family='monospace', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#0a0a1a', alpha=0.8))

    # Status
    if state['outcome'] == 'EXITO':
        status = 'SUCCESS!'
        status_color = '#00ff00'
    elif state['outcome'] == 'CHOQUE':
        status = 'CRASH!'
        status_color = '#ff4444'
    elif state['outcome'] is None:
        status = 'IN FLIGHT'
        status_color = '#ffaa00'
    else:
        status = 'INCOMPLETE'
        status_color = '#ffaa00'

    ax.text(info_x, info_y - 28, f'Status:  {status}',
            fontsize=11, color=status_color, family='monospace', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#0a0a1a', alpha=0.8))

    # Grafica de altitud
    times = [s['t'] for s in states[:i+1]]
    heights = [s['h'] for s in states[:i+1]]
    ax.plot(times, heights, 'o-', linewidth=2, markersize=5,
            color='#00ff00', alpha=0.6, label='Altitude trace')

    # Linea de seguridad
    ax.axhline(y=0, color='#ff4444', linestyle='--', linewidth=2, alpha=0.5)

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect('equal')
    ax.axis('off')

    # Guardar frame en memoria
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=80, bbox_inches='tight', facecolor='#0a0a1a')
    buf.seek(0)
    frame = Image.open(buf).convert('RGB')
    frames.append(frame)
    plt.close(fig)

    print(f"  Frame {i+1}/{len(states)} - t={state['t']}s")

# Crear GIF
print("\nGuardando GIF...")
frames[0].save('landing_animation.gif',
               save_all=True,
               append_images=frames[1:],
               duration=800,  # 800ms por frame
               loop=0)

print("OK: landing_animation.gif generado exitosamente!")
print(f"  - {len(frames)} frames")
print(f"  - Duracion total: {len(frames) * 0.8:.1f} segundos")
