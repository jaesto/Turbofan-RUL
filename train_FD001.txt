# Data

This project uses the **NASA C-MAPSS Turbofan Engine Degradation** dataset
(subset **FD001**), the standard public benchmark for Remaining Useful Life (RUL)
prognostics. The data is included in this repo so the pipeline runs out of the box.

Files (space separated, one row per engine per cycle):

- `train_FD001.txt` — 100 engines run to failure (full trajectories)
- `test_FD001.txt` — 100 engines observed only partway through life
- `RUL_FD001.txt` — ground-truth remaining life for each test engine

Each row is: `unit  cycle  op1 op2 op3  s1 s2 ... s21` (3 operating settings and
21 sensor channels). FD001 is the single-operating-condition, single-fault-mode
subset.

## Source and citation

NASA Prognostics Center of Excellence (PCoE), Turbofan Engine Degradation
Simulation Data Set. Public domain (U.S. Government work).

> A. Saxena and K. Goebel (2008). "Turbofan Engine Degradation Simulation Data
> Set", NASA Prognostics Data Repository, NASA Ames Research Center, Moffett
> Field, CA.

## Optional: synthetic data generator

`generate_synthetic_cmapss.py` produces a synthetic dataset in the exact same
FD001 format (same file names, same columns). It is not needed for normal use;
the real data above is the default. It exists only for quick offline experiments
or to run the pipeline without the real files present. Running it will overwrite
the `.txt` files in this folder, so restore the real files afterward if you use it.
