"""
Simulador de física para aterrizaje lunar.
Módulo puro sin dependencias externas.
"""

# Physics constants
H0 = 100.0           # Initial height (m)
V0 = -5.0            # Initial velocity (m/s) — negative = falling
GRAVITY = 4.0        # m/s² downward
MAX_THRUST = 10.0    # m/s² upward at 100% thrust
SAFE_SPEED = 3.0     # |v| <= 3 m/s for soft landing
NUM_SECONDS = 10


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def simulate(thrusts: list[float]) -> list[dict]:
    """
    Simulate the landing sequence given 10 thrust percentages.

    Args:
        thrusts: list of 10 floats (0-100 representing thrust percentage)

    Returns:
        list of 11 dicts (initial state + one per second after)
        Each dict contains: {t, h, v, thrust, net_accel, outcome}
    """
    states = []

    # Initial state (t=0)
    h = H0
    v = V0
    states.append({
        't': 0,
        'h': h,
        'v': v,
        'thrust': 0.0,
        'net_accel': 0.0,
        'outcome': None
    })

    # Simulate each second
    for i in range(NUM_SECONDS):
        # Clamp thrust to valid range
        thrust_clamped = clamp(thrusts[i], 0.0, 100.0)

        # Calculate net acceleration
        # thrust_accel is upward (positive), gravity is downward (negative)
        thrust_accel = (thrust_clamped / 100.0) * MAX_THRUST
        net_accel = thrust_accel - GRAVITY

        # Update velocity (Euler method, dt=1 second)
        v = v + net_accel

        # Update height
        h = h + v

        # Check landing condition
        outcome = None
        if h <= 0:
            h = 0.0
            if abs(v) <= SAFE_SPEED:
                outcome = "EXITO"
            else:
                outcome = "CHOQUE"

        states.append({
            't': i + 1,
            'h': h,
            'v': v,
            'thrust': thrust_clamped,
            'net_accel': net_accel,
            'outcome': outcome
        })

        # Stop simulation if landed or crashed
        if outcome is not None:
            break

    # If we never landed, mark final state as no landing
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
    # Test cases
    print("=== Test 1: Free fall (all 0% thrust) ===")
    states = simulate([0] * 10)
    for s in states:
        print(f"t={s['t']:2d}  h={s['h']:6.1f}  v={s['v']:7.1f}  outcome={s['outcome']}")

    print("\n=== Test 2: Hover (40% thrust) ===")
    states = simulate([40] * 10)
    for s in states:
        print(f"t={s['t']:2d}  h={s['h']:6.1f}  v={s['v']:7.1f}  outcome={s['outcome']}")

    print("\n=== Test 3: Soft landing ===")
    # Strategy: gradual descent with thrust at the end
    thrusts = [0, 0, 20, 40, 50, 60, 70, 80, 70, 60]
    states = simulate(thrusts)
    for s in states:
        print(f"t={s['t']:2d}  h={s['h']:6.1f}  v={s['v']:7.1f}  outcome={s['outcome']}")
