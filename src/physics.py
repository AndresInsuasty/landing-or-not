"""
Simulador de física para aterrizaje lunar.
Módulo puro sin dependencias externas.

Modelo físico:
- En cada segundo se aplica una aceleración constante (empuje - gravedad).
- La integración usa la solución cerrada del MRUA, exacta para a constante:
      h(t+dt) = h(t) + v(t)*dt + 0.5 * a * dt²
      v(t+dt) = v(t) + a * dt
- Si la nave cruza el suelo dentro del step, se calcula el instante exacto
  de impacto resolviendo h(t)=0 y se reporta la velocidad real en ese
  instante (no la del final del step). Esto evita declarar éxitos falsos.
"""

# Physics constants
H0 = 100.0           # Initial height (m)
V0 = 0.0             # Initial velocity (m/s) — la nave parte en reposo
GRAVITY = 4.0        # m/s² downward
MAX_THRUST = 10.0    # m/s² upward at 100% thrust
SAFE_SPEED = 3.0     # |v| <= 3 m/s for soft landing
NUM_SECONDS = 10
DT = 1.0             # Duration of each thrust step (seconds)
GROUND_EPS = 1e-9    # Tolerancia numérica para detectar contacto con el suelo


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def _impact_time(h0: float, v0: float, a: float, dt: float) -> float:
    """
    Devuelve el tiempo t en (0, dt] en el que h0 + v0*t + 0.5*a*t^2 = 0.
    Asume que el cruce ocurre dentro del step (h0 > 0 y h(dt) <= 0).
    """
    if abs(a) < 1e-12:
        # Movimiento uniforme: t = -h0 / v0  (v0 < 0 garantizado por h(dt) <= 0)
        return -h0 / v0

    # Solución cuadrática: 0.5*a*t^2 + v0*t + h0 = 0
    disc = v0 * v0 - 2.0 * a * h0
    if disc < 0:
        # Numéricamente no debería ocurrir si h(dt) <= 0; clamp por seguridad.
        disc = 0.0
    sqrt_disc = disc ** 0.5

    # Dos raíces; nos interesa la primera positiva en (0, dt].
    t1 = (-v0 - sqrt_disc) / a
    t2 = (-v0 + sqrt_disc) / a

    candidates = [t for t in (t1, t2) if 1e-9 < t <= dt + 1e-9]
    if not candidates:
        # Fallback: si por error numérico no hay candidato, devolver dt.
        return dt
    return min(candidates)


def simulate(thrusts: list[float]) -> list[dict]:
    """
    Simulate the landing sequence given 10 thrust percentages.

    Args:
        thrusts: list of 10 floats (0-100 representing thrust percentage)

    Returns:
        list of states (initial state + one per second after, hasta el aterrizaje)
        Each dict contains: {t, h, v, thrust, net_accel, outcome}
    """
    states = []

    h = H0
    v = V0
    states.append({
        't': 0,
        'h': h,
        'v': v,
        'thrust': 0.0,
        'net_accel': 0.0,
        'outcome': None,
    })

    for i in range(NUM_SECONDS):
        thrust_clamped = clamp(thrusts[i], 0.0, 100.0)
        thrust_accel = (thrust_clamped / 100.0) * MAX_THRUST
        net_accel = thrust_accel - GRAVITY

        # Integración exacta para aceleración constante en el intervalo
        h_new = h + v * DT + 0.5 * net_accel * DT * DT
        v_new = v + net_accel * DT

        outcome = None
        if h_new <= GROUND_EPS:
            # La nave cruza el suelo en algún t_imp ∈ (0, DT].
            # Si h_new salió ligeramente positivo por ruido numérico
            # (caso "toca justo al final del step"), tratarlo como impacto en t=DT.
            if h_new >= -GROUND_EPS:
                t_imp = DT
            else:
                t_imp = _impact_time(h, v, net_accel, DT)
            v_impact = v + net_accel * t_imp
            h = 0.0
            v = v_impact
            outcome = "EXITO" if abs(v_impact) <= SAFE_SPEED else "CHOQUE"
        else:
            h = h_new
            v = v_new

        states.append({
            't': i + 1,
            'h': h,
            'v': v,
            'thrust': thrust_clamped,
            'net_accel': net_accel,
            'outcome': outcome,
        })

        if outcome is not None:
            break

    if states[-1]['outcome'] is None:
        states[-1]['outcome'] = "SIN_ATERRIZAJE"

    return states


def classify_outcome(states: list[dict]) -> str:
    """
    Return the outcome of the simulation.
    Returns: "EXITO", "CHOQUE", or "SIN_ATERRIZAJE"
    """
    for state in states:
        if state['outcome'] is not None:
            return state['outcome']
    return "SIN_ATERRIZAJE"


if __name__ == "__main__":
    print("=== Test 1: Caída libre (todo 0%) ===")
    states = simulate([0] * 10)
    for s in states:
        print(f"t={s['t']:2d}  h={s['h']:7.2f}  v={s['v']:7.2f}  outcome={s['outcome']}")

    print("\n=== Test 2: Hover perpetuo (40% siempre) ===")
    states = simulate([40] * 10)
    for s in states:
        print(f"t={s['t']:2d}  h={s['h']:7.2f}  v={s['v']:7.2f}  outcome={s['outcome']}")

    print("\n=== Test 3: Aterrizaje suave de prueba ===")
    thrusts = [0, 0, 0, 0, 70, 90, 90, 90, 95, 100]
    states = simulate(thrusts)
    for s in states:
        print(f"t={s['t']:2d}  h={s['h']:7.2f}  v={s['v']:7.2f}  outcome={s['outcome']}")
