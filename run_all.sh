#!/usr/bin/env bash
# End-to-end pipeline. Run from the repository root:  bash run_all.sh
set -euo pipefail

echo "[1/5] Check for C-MAPSS FD001 data (uses the real NASA files in data/)"
if [ ! -f data/train_FD001.txt ]; then
  echo "  real data not found; generating synthetic data in the same format as a fallback"
  python3 data/generate_synthetic_cmapss.py
else
  echo "  found data/train_FD001.txt"
fi

echo "[2/5] Load into SQLite + build labeled views (SQL layer)"
python3 sql/load_to_sqlite.py

echo "[3/5] Exploratory data analysis"
python3 python/01_explore.py

echo "[4/5] RUL models (Random Forest, Gradient Boosting) + Bayesian uncertainty"
python3 python/02_model_rul.py
python3 python/03_bayesian_rul.py

echo "[5/5] Reliability / survival analysis (R)"
Rscript R/reliability_analysis.R

echo "Done. See outputs/figures/ and outputs/metrics.json"
