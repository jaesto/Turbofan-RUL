"""
Generate a synthetic run-to-failure dataset in the NASA C-MAPSS FD001 format.

WHY THIS EXISTS
---------------
The real NASA C-MAPSS turbofan degradation data is public but must be downloaded
separately (see data/README.md). To keep this repository clonable and runnable in
one command, this script produces a *synthetic* dataset with the exact same schema
and file names as C-MAPSS FD001. The degradation physics are simplified but
realistic: each engine has a hidden health state that decays with accelerating
wear, and sensors respond to that health plus operating conditions and noise.
Several sensors are intentionally flat, mirroring the real data, so the feature
selection step has something real to do.

To use the REAL data instead, drop the official
train_FD001.txt / test_FD001.txt / RUL_FD001.txt into this folder (same names).
Everything downstream is format-identical and will just work.

The generator is deterministic (fixed seed) so results are reproducible.
"""

import numpy as np
import os

SEED = 42
N_TRAIN_UNITS = 100
N_TEST_UNITS = 100
HERE = os.path.dirname(os.path.abspath(__file__))

# 3 operational settings + 21 sensors, matching C-MAPSS FD001 columns.
N_OP = 3
N_SENSORS = 21

# Which sensors carry a real degradation trend vs. flat/noise-only.
# In real FD001, roughly 7 sensors are effectively constant; we mirror that.
TRENDING_UP = [2, 3, 4, 8, 11, 13, 15, 17]      # rise as the engine degrades
TRENDING_DOWN = [7, 9, 12, 14, 20, 21]          # fall as the engine degrades
FLAT = [1, 5, 6, 10, 16, 18, 19]                # near-constant (uninformative)


def _health_curve(life, exponent):
    """Hidden health index from 1.0 (new) to ~0.0 (failed), accelerating wear.
    The exponent varies per engine, so degradation shape is not identical."""
    t = np.arange(1, life + 1)
    frac = t / life
    degradation = frac ** exponent
    return 1.0 - degradation  # 1 -> 0


def _make_unit(unit_id, life, rng):
    # Per-unit variation so engines are not interchangeable.
    exponent = rng.uniform(1.6, 2.6)
    health = _health_curve(life, exponent)
    cycles = np.arange(1, life + 1)

    # Operating settings: mild regime variation around FD001-like values.
    op1 = rng.normal(0.0, 0.0025, life)
    op2 = rng.normal(0.0, 0.00025, life)
    op3 = np.full(life, 100.0)

    cols = [np.full(life, unit_id), cycles, op1, op2, op3]

    wear = 1.0 - health                   # 0 -> 1
    for s in range(1, N_SENSORS + 1):
        # per-unit baseline offset (manufacturing/unit-to-unit spread)
        base = 100.0 + s * 7.0 + rng.normal(0.0, 3.0)
        if s in TRENDING_UP:
            amp = 9.0 + (s % 5)
            noise = rng.normal(0.0, 2.5, life)
            sig = base + amp * wear + noise
        elif s in TRENDING_DOWN:
            amp = 8.0 + (s % 4)
            noise = rng.normal(0.0, 2.5, life)
            sig = base - amp * wear + noise
        else:  # FLAT (uninformative)
            sig = base + rng.normal(0.0, 0.3, life)
        cols.append(sig)

    return np.column_stack(cols)


def _fmt_row(row):
    unit = int(row[0]); cyc = int(row[1])
    rest = " ".join(f"{v:.4f}" for v in row[2:])
    return f"{unit} {cyc} {rest}"


def main():
    rng = np.random.default_rng(SEED)

    # ---- training set: full run-to-failure trajectories ----
    train_rows = []
    for u in range(1, N_TRAIN_UNITS + 1):
        life = int(rng.integers(128, 357))          # FD001-like life range
        train_rows.append(_make_unit(u, life, rng))
    train = np.vstack(train_rows)

    # ---- test set: trajectories truncated before failure; RUL is the remainder ----
    test_rows = []
    rul_truth = []
    for u in range(1, N_TEST_UNITS + 1):
        life = int(rng.integers(128, 357))
        full = _make_unit(u, life, rng)
        # cut somewhere in the second half so there is real signal but life remains
        cut = int(rng.integers(int(life * 0.45), int(life * 0.95)))
        test_rows.append(full[:cut])
        rul_truth.append(life - cut)
    test = np.vstack(test_rows)

    with open(os.path.join(HERE, "train_FD001.txt"), "w") as f:
        for r in train:
            f.write(_fmt_row(r) + " \n")
    with open(os.path.join(HERE, "test_FD001.txt"), "w") as f:
        for r in test:
            f.write(_fmt_row(r) + " \n")
    with open(os.path.join(HERE, "RUL_FD001.txt"), "w") as f:
        for v in rul_truth:
            f.write(f"{int(v)}\n")

    print(f"Wrote synthetic C-MAPSS FD001:")
    print(f"  train: {train.shape[0]} rows across {N_TRAIN_UNITS} units")
    print(f"  test:  {test.shape[0]} rows across {N_TEST_UNITS} units")
    print(f"  RUL:   {len(rul_truth)} truth labels")


if __name__ == "__main__":
    main()
