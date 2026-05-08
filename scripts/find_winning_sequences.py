"""
Búsqueda automática de secuencias exitosas y ROBUSTAS.

Una secuencia es robusta si aterriza exitosamente con los valores exactos
y también con cada una de las perturbaciones de ±1% en cualquier paso.
Esto garantiza que un estudiante con error de slider de ±1% también vea EXITO.

Sobrescribe `scripts/secuencias_exitosas.txt` con las 10 mejores.
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import physics  # noqa: E402


SEED = 13
NUM_TARGET = 10
MIN_DISTANCE = 20      # distancia L1 mínima entre secuencias seleccionadas
MIN_ROBUST_HITS = 16   # de 20 perturbaciones de ±1%, cuántas deben aterrizar


def random_profile(rng: random.Random) -> list[int]:
    """Caída libre + frenado creciente con jitter."""
    free_fall = rng.randint(2, 5)
    seq = [0] * free_fall
    remaining = 10 - free_fall
    for i in range(remaining):
        progress = i / max(1, remaining - 1)
        base = 50 + progress * 50
        jitter = rng.randint(-25, 15)
        val = int(round(base + jitter))
        seq.append(max(0, min(100, val)))
    return seq


def outcome_of(seq: list[int]) -> str:
    states = physics.simulate([float(v) for v in seq])
    return physics.classify_outcome(states)


def impact_speed(seq: list[int]) -> float:
    states = physics.simulate([float(v) for v in seq])
    return abs(states[-1]['v'])


def robust_score(seq: list[int], delta: int = 1) -> int:
    """
    Cuenta cuántas perturbaciones individuales de ±delta% siguen aterrizando
    exitosamente. Hay 20 perturbaciones (10 pasos × 2 direcciones).
    """
    hits = 0
    for i in range(len(seq)):
        for d in (-delta, +delta):
            new_val = seq[i] + d
            if not (0 <= new_val <= 100):
                hits += 1  # perturbación inválida (clamp), no penalizar
                continue
            perturbed = seq.copy()
            perturbed[i] = new_val
            if outcome_of(perturbed) == "EXITO":
                hits += 1
    return hits


def l1_distance(a: list[int], b: list[int]) -> int:
    return sum(abs(x - y) for x, y in zip(a, b))


def search(num_iterations: int = 300_000) -> list[tuple[list[int], int]]:
    rng = random.Random(SEED)
    robust: list[tuple[list[int], int]] = []
    seen: set[tuple[int, ...]] = set()
    checked = 0

    for it in range(num_iterations):
        seq = random_profile(rng)
        key = tuple(seq)
        if key in seen:
            continue
        seen.add(key)

        # Filtro rápido: primero comprobar que la secuencia base aterriza.
        if outcome_of(seq) != "EXITO":
            continue
        checked += 1
        score = robust_score(seq)
        if score >= MIN_ROBUST_HITS:
            robust.append((seq, score))

        if it % 25_000 == 0 and it > 0:
            print(f"  iter {it:>6}  candidatas-EXITO probadas: {checked}  "
                  f"robustas (score≥{MIN_ROBUST_HITS}): {len(robust)}")

    print(f"  Total robustas encontradas: {len(robust)}")
    return robust


def select_diverse(scored: list[tuple[list[int], int]],
                   k: int, min_dist: int) -> list[tuple[list[int], int]]:
    """Elige k secuencias diversas, ordenadas por score (más robustas primero)."""
    sorted_by_score = sorted(scored, key=lambda sc: (-sc[1], impact_speed(sc[0])))
    chosen: list[tuple[list[int], int]] = []
    for s, sc in sorted_by_score:
        if all(l1_distance(s, c[0]) >= min_dist for c in chosen):
            chosen.append((s, sc))
            if len(chosen) >= k:
                break
    return chosen


def main():
    print(f"Buscando secuencias ROBUSTAS (semilla={SEED}, "
          f"score>={MIN_ROBUST_HITS}/20 perturbaciones de ±1%)...")
    scored = search()

    if not scored:
        print("  No se encontraron secuencias robustas.")
        return

    chosen = select_diverse(scored, NUM_TARGET, MIN_DISTANCE)
    print(f"\n  Seleccionadas {len(chosen)} secuencias diversas:\n")

    out_path = Path(__file__).resolve().parent / "secuencias_exitosas.txt"
    lines = []
    for i, (seq, sc) in enumerate(chosen, 1):
        seq_str = "[" + ", ".join(str(v) for v in seq) + "]"
        lines.append(f"{i}. {seq_str}")
        v = impact_speed(seq)
        print(f"  {i:2d}. {seq_str}   robust={sc}/20   |v_impact|={v:.2f} m/s")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nEscrito: {out_path}")


if __name__ == "__main__":
    main()
