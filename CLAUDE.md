# CLAUDE.md — Simulador de Aterrizaje Lunar

Herramienta educativa interactiva para enseñar **algoritmos y pensamiento computacional** en clase. Los estudiantes ingresan una secuencia de 10 valores de empuje (0–100%) que el simulador ejecuta paso a paso, mostrando si la nave aterriza con éxito o se estrella.

## Ejecutar el proyecto

```bash
uv run run.py
```

## Estructura del proyecto

```
landing-or-not/
├── src/
│   ├── main.py         # UI pygame — 3 pantallas: Input, Simulación, Resultado
│   └── physics.py      # Motor de física puro, sin dependencias externas
├── scripts/
│   ├── generate_demo_images.py     # Genera PNGs educativos (matplotlib)
│   ├── generate_landing_gif.py     # Genera GIF animado
│   ├── find_winning_sequences.py   # Busca y guarda 10 secuencias exitosas
│   └── secuencias_exitosas.txt     # 10 secuencias que logran aterrizaje exitoso
├── img/                # Imágenes generadas por los scripts
├── run.py              # Entry point — importa App desde src/main.py
├── pyproject.toml      # Dependencias: pygame + matplotlib (gestionado con uv)
└── CLAUDE.md           # Este archivo
```

## Comandos útiles

```bash
uv run run.py                                  # Iniciar el simulador
uv run scripts/generate_demo_images.py         # Regenerar imágenes de demostración
uv run scripts/generate_landing_gif.py         # Regenerar GIF animado
uv run scripts/find_winning_sequences.py       # Buscar nuevas secuencias exitosas
```

## Dependencias

Gestionadas con **uv**. No usar pip directamente.

```bash
uv add <paquete>      # Agregar dependencia
uv sync               # Sincronizar entorno
```

## Arquitectura

Patrón MVC simplificado:
- **Model**: `src/physics.py` — física pura, sin pygame. Función `simulate(thrusts)` retorna estados; `classify_outcome(states)` retorna `"EXITO"`, `"CHOQUE"` o `"SIN_ATERRIZAJE"`.
- **View + Controller**: `src/main.py` — clase `App` gestiona la máquina de estados (3 pantallas). Cada pantalla es una clase con `handle_event`, `update`, `draw`.

## Reglas de contribución

- **No modificar `src/physics.py`** sin actualizar primero los valores esperados en `scripts/secuencias_exitosas.txt`. La física es la fuente de verdad pedagógica.
- Las pantallas están desacopladas: `InputScreen → SimulationScreen → ResultScreen` via callbacks en `App`. No agregar dependencias directas entre pantallas.
- Constantes de color y layout en la parte superior de `main.py` — no hardcodear valores en los métodos `draw()`.
- Usar `uv run` para todos los comandos, no `python` directamente.

## Física del simulador

```
Gravedad:           4.0 m/s²  (hacia abajo)
Empuje máximo:     10.0 m/s²  (al 100%, hacia arriba)
Velocidad segura:  ≤ 3 m/s    para aterrizaje exitoso
Altura inicial:   100 m
Velocidad inicial:  0 m/s     (la nave parte en reposo)
Duración:          10 segundos (1 valor de empuje por segundo)
```

Integración por paso (solución cerrada del MRUA, dt=1s):
```
a = (empuje% / 100) * 10 - 4
h_nueva = h + v*dt + 0.5 * a * dt²
v_nueva = v + a*dt
```

Si la nave cruza el suelo dentro de un step, se calcula el instante exacto
de impacto y la velocidad real en ese instante (no la del final del step).
Esto evita declarar éxitos falsos cuando la nave pasa por h=0 a alta velocidad.

Tiempo teórico de caída libre (sin empuje): √50 ≈ 7.07 s.

## Secuencia exitosa de referencia

```python
[0, 0, 0, 0, 37, 52, 56, 84, 71, 100]
```

Más alternativas en `scripts/secuencias_exitosas.txt`. Para regenerar tras un
cambio en la física:

```bash
uv run scripts/find_winning_sequences.py
```
