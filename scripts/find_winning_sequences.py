"""
Búsqueda automática de secuencias exitosas para el simulador lunar.

Estrategia:
  1. Búsqueda aleatoria amplia con perfiles "caída libre + frenado".
  2. Filtrado por outcome == "EXITO".
  3. Selección de secuencias DIVERSAS (distancia mínima entre ellas).

Sobrescribe `scripts/secuencias_exitosas.txt` con las 10 mejores.
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import physics  # noqa: E402


SEED = 7
NUM_TARGET = 10
MIN_DISTANCE = 25  # distancia L1 mínima entre secuencias seleccionadas


def random_profile(rng: random.Random) -> list[int]:
    """
    Genera un perfil plausible: K segundos de caída libre seguidos de
    empujes crecientes/aleatorios. Aumenta la tasa de éxito vs. random puro.
    """
    free_fall = rng.randint(2, 5)
    seq = [0] * free_fall
    remaining = 10 - free_fall

    # Empuje base alto al final, con jitter
    for i in range(remaining):
        progress = i / max(1, remaining - 1)
        base = 50 + progress * 50  # 50% → 100%
        jitter = rng.randint(-20, 15)
        val = int(round(base + jitter))
        seq.append(max(0, min(100, val)))

    return seq


def is_winning(seq: list[int]) -> tuple[bool, dict]:
    """Returns (success, final_state)."""
    states = physics.simulate([float(v) for v in seq])
    outcome = physics.classify_outcome(states)
    return outcome == "EXITO", states[-1]


def l1_distance(a: list[int], b: list[int]) -> int:
    return sum(abs(x - y) for x, y in zip(a, b))


def search(num_iterations: int = 200_000) -> list[tuple[list[int], dict]]:
    rng = random.Random(SEED)
    winners: list[tuple[list[int], dict]] = []
    seen: set[tuple[int, ...]] = set()

    for _ in range(num_iterations):
        seq = random_profile(rng)
        key = tuple(seq)
        if key in seen:
            continue
        seen.add(key)

        ok, final = is_winning(seq)
        if ok:
            winners.append((seq, final))

    return winners


def select_diverse(winners: list[tuple[list[int], dict]],
                   k: int,
                   min_dist: int) -> list[tuple[list[int], dict]]:
    """
    Selección codiciosa: ordena por |v_impacto| (más suave primero) y
    descarta candidatos demasiado parecidos a los ya elegidos.
    """
    winners_sorted = sorted(winners, key=lambda w: abs(w[1]['v']))
    chosen: list[tuple[list[int], dict]] = []

    for seq, final in winners_sorted:
        if all(l1_distance(seq, c[0]) >= min_dist for c in chosen):
            chosen.append((seq, final))
            if len(chosen) >= k:
                break

    return chosen


def main():
    print(f"Buscando secuencias exitosas (semilla={SEED})...")
    winners = search()
    print(f"  Encontradas {len(winners)} secuencias exitosas en total.")

    chosen = select_diverse(winners, NUM_TARGET, MIN_DISTANCE)
    print(f"  Seleccionadas {len(chosen)} secuencias diversas.\n")

    out_path = Path(__file__).resolve().parent / "secuencias_exitosas.txt"
    lines = []
    for i, (seq, final) in enumerate(chosen, 1):
        seq_str = "[" + ", ".join(str(v) for v in seq) + "]"
        lines.append(f"{i}. {seq_str}")
        print(f"  {i:2d}. {seq_str}   |v_impacto|={abs(final['v']):.2f} m/s")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nEscrito: {out_path}")


if __name__ == "__main__":
    main()
