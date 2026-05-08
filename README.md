# Aterrizaje Lunar — Simulador de Algoritmos

Una herramienta educativa interactiva para enseñar algoritmos como "secuencia predefinida de instrucciones".

Los estudiantes arrastran **10 sliders** para configurar el empuje de una nave espacial segundo a segundo y la ven aterrizar (o estrellarse) en tiempo real.

---

## Vista Previa

### Animación de aterrizaje exitoso

![Animacion de aterrizaje exitoso](img/landing_animation.gif)

---

### Gráficas de simulación

![Graficos de altura, velocidad y empuje](img/demo_graphs.png)

Las tres métricas clave de una simulación completa:
- **Izquierda:** Altura desciende de 100 m a 0 m
- **Centro:** Velocidad controlada para llegar dentro del rango seguro (≤ 3 m/s) al aterrizar
- **Derecha:** Secuencia de empujes aplicados segundo a segundo

---

### Secuencia visual de aterrizaje

![Secuencia en 5 momentos clave](img/demo_sequence.png)

Los 5 momentos clave del descenso: caída libre, inicio de frenada y aterrizaje suave.

---

### Estrategias ganadoras de referencia

![Tabla de 5 estrategias ganadoras](img/demo_strategies.png)

Cinco secuencias que logran aterrizaje exitoso — úsalas como punto de partida o desafío.

---

## Instalación y Ejecución

### Requisitos

- Python 3.11+
- `uv` (manejador de paquetes moderno)

### Pasos

```bash
# Clonar el repositorio
git clone https://github.com/AndresInsuasty/landing-or-not.git
cd landing-or-not

# Ejecutar (uv instala las dependencias automáticamente)
uv run run.py
```

---

## Estructura del Proyecto

```
landing-or-not/
├── src/
│   ├── physics.py              # Motor de simulación puro (sin pygame)
│   └── main.py                 # Aplicación pygame con 3 pantallas
├── scripts/
│   ├── generate_demo_images.py     # Genera imágenes demostrativas
│   ├── generate_landing_gif.py     # Genera GIF animado
│   ├── find_winning_sequences.py   # Busca secuencias robustas automaticamente
│   └── secuencias_exitosas.txt     # Listado de 10 estrategias ganadoras
├── img/
│   ├── demo_graphs.png         # Gráficos de simulación
│   ├── demo_sequence.png       # Secuencia visual de aterrizaje
│   ├── demo_strategies.png     # Tabla de estrategias
│   └── landing_animation.gif   # Animación GIF del aterrizaje
├── run.py                      # Entry point
├── pyproject.toml              # Configuración uv
├── CLAUDE.md                   # Guía para Claude Code
└── README.md                   # Este archivo
```

---

## Cómo Usar

### 1. Pantalla de Entrada

- Arrastra los **10 sliders** para configurar el empuje de cada segundo (0–100%)
- Usa ← → para ajuste fino de ±5 % · Shift + ← → para ±1 %
- **Clave:** Empuje al **40 %** cancela la gravedad (hover perfecto)
- Haz clic en **SIMULAR** para ejecutar tu algoritmo

### 2. Simulación

- Observa la nave animada descendiendo con llamas reactivas
- Panel izquierdo muestra telemetría en tiempo real: altura, velocidad, empuje
- Barra de progreso de tiempo en la parte superior (10 segmentos)
- Duración: ~1.5 s de animación por segundo simulado

### 3. Resultados

Tres posibles resultados:

| Resultado | Condición | Color |
|-----------|-----------|-------|
| **ATERRIZAJE EXITOSO** | `\|v\|` ≤ 3 m/s al tocar suelo | Verde |
| **CHOQUE — NAVE DESTRUIDA** | `\|v\|` > 3 m/s al tocar suelo | Rojo |
| **SIN ATERRIZAJE** | Altura > 0 m después de 10 s | Amarillo |

Haz clic en **INTENTAR DE NUEVO** para probar otra estrategia.

---

## Fisica del Simulador

### Constantes Globales

- Altura inicial: 100 m
- Velocidad inicial: 0 m/s (la nave parte en reposo)
- Gravedad: 4 m/s² hacia abajo
- Empuje maximo: 10 m/s² hacia arriba (al 100%)
- Punto de equilibrio (hover): 40% de empuje
- Criterio de exito: Altura <= 0 m Y |v| <= 3 m/s
- Tiempo de caida libre teorico: √50 ≈ 7.07 s

### Ecuacion de Movimiento (cada segundo)

Integracion exacta del MRUA con dt = 1 s:

```
a = (empuje% / 100) * 10 - 4
altura_nueva   = altura + velocidad * 1 + 0.5 * a * 1²
velocidad_nueva = velocidad + a * 1
```

Si la nave cruza el suelo dentro de un segundo, el simulador resuelve la
cuadratica para obtener el instante exacto de impacto y reportar la velocidad
real al tocar tierra (no la del final del paso). Esto garantiza que el
resultado mostrado sea fisicamente correcto.

### Por que 40% es especial

Si empuje = 40%:
- Aceleracion neta = (40/100) * 10 - 4 = 4 - 4 = 0
- La velocidad NO cambia (hover perfecto)
- Si la nave esta inmovil con 40% se mantiene flotando indefinidamente

---

## Estrategias de Aterrizaje Exitoso

Las 10 secuencias de `scripts/secuencias_exitosas.txt` son **robustas**: cada una
sigue aterrizando con éxito aunque el estudiante se desvíe ±1% en la mayoría de
los sliders. Esto compensa la imprecisión natural al arrastrarlos.

Aquí tienes 5 ejemplos para empezar:

---

### Estrategia 1: Aterrizaje Suave (referencia)

```
Segundo  1  2  3  4  5  6  7  8  9 10
Empuje % 0  0  0  0 36 45 52 93 94 75
```

**Simulación paso a paso:**
```
t= 0  h=100.0m  v=  0.0m/s  emp=  0%
t= 1  h= 98.0m  v= -4.0m/s  emp=  0%   <- Caida libre
t= 2  h= 92.0m  v= -8.0m/s  emp=  0%
t= 3  h= 82.0m  v=-12.0m/s  emp=  0%
t= 4  h= 68.0m  v=-16.0m/s  emp=  0%   <- 4s de caida libre acumulada
t= 5  h= 51.8m  v=-16.4m/s  emp= 36%   <- Inicia frenada suave
t= 6  h= 35.7m  v=-15.9m/s  emp= 45%   <- Empuje creciente
t= 7  h= 20.4m  v=-14.7m/s  emp= 52%
t= 8  h=  8.3m  v= -9.4m/s  emp= 93%   <- Frenada agresiva
t= 9  h=  1.6m  v= -4.0m/s  emp= 94%
t=10  h=  0.0m  v= -2.2m/s  emp= 75%   <- EXITO!
```

**Características:**
- 4 segundos de caída libre para ganar velocidad
- Frenada progresiva creciente
- Aterriza a -2.2 m/s en t=10 (dentro del límite de 3 m/s)

---

### Estrategia 2: Frenada Equilibrada

```
Segundo  1  2  3  4  5  6  7  8  9 10
Empuje % 0  0  0  0 28 53 54 93 93 76
```

Frenado fuerte concentrado al final. Aterriza a -2.5 m/s.

---

### Estrategia 3: Frenado Pico

```
Segundo  1  2  3  4  5  6  7  8  9 10
Empuje % 0  0  0  0 30 48 59 87 100 79
```

Empuje máximo (100%) justo antes del último segundo. Aterriza a -2.1 m/s.

---

### Estrategia 4: Curva Pronunciada

```
Segundo  1  2  3  4  5  6  7  8  9 10
Empuje % 0  0  0  0 38 36 70 83 89 75
```

Empuje crece rápidamente desde el 70%. Aterriza a -2.2 m/s.

---

### Estrategia 5: Frenado Tardío

```
Segundo  1  2  3  4  5  6  7  8  9 10
Empuje % 0  0  0  0 32 46 67 76 98 78
```

Concentra el empuje cerca del final. Aterriza a -2.2 m/s.

---

## Desafios para Estudiantes

### Nivel 1: Principiante
Usa una de las 5 estrategias exitosas tal cual esta. Observa que sucede.

### Nivel 2: Intermedio
Cambia UNO de los valores de las estrategias existentes. Sigue aterrizando? A que velocidad?

### Nivel 3: Avanzado
Diseña tu propia estrategia desde cero. Prueba diferentes distribuciones.

### Reto Extremo
Encuentra una estrategia que atterrice con velocidad EXACTAMENTE igual a -2.0 m/s
(mas preciso que -3.0 m/s).

---

## Estructura del Codigo

### src/physics.py — Motor de Simulacion Puro

Sin dependencias externas:

```python
simulate(thrusts: list[float]) -> list[dict]
  Entrada: lista de 10 valores de empuje (0-100%)
  Salida: lista de estados (estado inicial + uno por cada segundo simulado).
          Si la nave aterriza antes del segundo 10, la simulacion se detiene
          en ese instante.
  Cada estado contiene: t, h, v, thrust, net_accel, outcome

classify_outcome(states: list[dict]) -> str
  Retorna: "EXITO", "CHOQUE" o "SIN_ATERRIZAJE"
```

### src/main.py — Aplicación Pygame

Tres pantallas con máquina de estados:

1. **InputScreen**: 10 sliders arrastrables con previsualización en tiempo real
2. **SimulationScreen**: Animación 60 FPS con telemetría, grid de altitud y barra de tiempo
3. **ResultScreen**: Panel de resultados con barras de empuje y mensaje educativo

---

## Scripts Utiles

Los scripts en la carpeta `scripts/` pueden ejecutarse independientemente:

```bash
# Regenerar imagenes demostrativas
uv run scripts/generate_demo_images.py

# Regenerar GIF animado
uv run scripts/generate_landing_gif.py

# Buscar nuevas secuencias robustas (sobrescribe secuencias_exitosas.txt)
uv run scripts/find_winning_sequences.py
```

`find_winning_sequences.py` hace una busqueda aleatoria filtrando por dos
criterios: (1) la secuencia base aterriza con exito y (2) al menos 16 de las
20 perturbaciones de ±1% en cualquier paso tambien aterrizan exitosamente.
Util tras cualquier cambio en la fisica.

---

## Para Docentes: Valor Pedagogico

Esta herramienta enseña:

**ALGORITMOS COMO SECUENCIA PREDEFINIDA**
- Los estudiantes preparan un "plan" (algoritmo) antes de ejecutarlo
- Refuerza la idea de que los algoritmos son instrucciones secuenciales

**PENSAMIENTO COMPUTACIONAL**
- Necesitan razonar sobre causa y efecto
- Empuje → Aceleracion → Velocidad → Altura
- Desarrollo de intuicion fisica-computacional

**OPTIMIZACION**
- Existen multiples soluciones; NO hay una unica respuesta correcta
- Hay trade-offs: diferentes estrategias tienen distintas caracteristicas
- Oportunidad de comparar y analizar soluciones

**PRUEBA Y ERROR ITERATIVO**
- Refuerza el ciclo: Predecir → Simular → Analizar → Ajustar
- Feedback visual inmediato
- Motivacion intrinseca (resolver el "puzzle")

### Actividades Sugeridas en Clase

1. **Fase 1 - Prediccion:**
   - Distribuir una estrategia en papel
   - Pedir a los estudiantes: "Que creen que pasara?"
   - Registrar predicciones

2. **Fase 2 - Simulacion:**
   - Ejecutar la estrategia
   - Comparar resultado real vs prediccion

3. **Fase 3 - Analisis:**
   - Mostrar graficos de altura/velocidad/empuje
   - Preguntar: "Donde ocurrio el cambio mayor?"

4. **Fase 4 - Iteracion:**
   - Pedir ajustes pequenos: "Que pasa si subes 10% en t=5?"
   - Fomentar experimentacion

5. **Fase 5 - Reto Colaborativo:**
   - Competencia: Quien consigue velocidad de atterrizaje mas cercana a 0?
   - Documentacion: Escribir estrategia ganadora y explicar razonamiento

---

## Ejemplos de Estrategias Fallidas (Para Analisis)

### CRASH CLASICO: Sin empuje

```
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
```
Resultado: Caida libre → CHOQUE a -28.3 m/s aproximadamente en t ≈ 7.07 s.

### HOVER ETERNO: Empuje justo en el equilibrio

```
[40, 40, 40, 40, 40, 40, 40, 40, 40, 40]
```
Resultado: La nave se queda inmovil a 100 m. Como parte en reposo y el empuje
compensa exactamente la gravedad, nunca cae → SIN ATERRIZAJE.

### SIN ATERRIZAJE: Demasiado empuje

```
[50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
```
Resultado: La nave SUBE en lugar de bajar (a > 0 m/s² hacia arriba) → SIN ATERRIZAJE.

---

## Tecnologias Utilizadas

- **Python 3.11+** - Lenguaje de programacion
- **pygame** - Para la interfaz grafica y animaciones
- **matplotlib** - Para graficos y visualizaciones
- **Pillow** - Para procesamiento de imagenes y generacion de GIFs
- **uv** - Manejador moderno de paquetes Python

---

## Soporte y Contribuciones

Para dudas, sugerencias o reportar problemas:
1. Verifica que tienes Python 3.11+
2. Asegúrate de haber instalado todas las dependencias con `uv add pygame matplotlib`
3. Intenta con una de las 5 estrategias exitosas del README

---

## Licencia

Creado para fines educativos. Libre para usar, modificar y compartir.

---

**Buena suerte, a atterrizar! Saludos.** 🚀🌙
