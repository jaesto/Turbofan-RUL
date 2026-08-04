# Turbofan Remaining Useful Life (RUL)

Forecasting how many operating cycles a jet engine has left before it fails, on
the NASA C-MAPSS degradation benchmark. Built as a full pipeline: a governed SQL
data layer, machine learning models, a Bayesian model that reports its own
uncertainty, and a classical reliability / survival analysis in R.

This is a predictive maintenance (Condition Based Maintenance, CBM+) problem: the
kind of Prognostics and Health Management work used to decide when to service a
component based on evidence of wear rather than a fixed calendar.

---

## Overview

Every engine in the dataset is observed cycle by cycle through 21 sensors. In the
training set the engines run all the way to failure, so I can look back and label
each moment with its true Remaining Useful Life. The goal is to learn that
mapping and then, for a set of engines observed only partway through life,
predict how much life remains, and say how confident that prediction is.

---

## Why I built it this way

I wanted this to reflect how the problem is actually solved, not just fit one
model to a table. A few decisions drove the design.

**I started with the data layer, not the model.** The raw sensor logs go into a
SQLite database, and the RUL label is computed in SQL as `max_cycle - cycle`.
Doing the labeling and the train / test / lifetime views declaratively keeps the
data preparation auditable and hands clean tables to everything downstream. On a
system meant to run for decades, the architecture matters more than any single
model, so I treated it as the foundation.

**I used three model families on purpose.** Reliability statistics, machine
learning, and a Bayesian model each answer a slightly different question, and a
real program needs all three. The tree models learn the sensor to RUL mapping
without assuming any physics. The Weibull survival model describes how the whole
population fails. The Bayesian model gives a distribution rather than a single
number. Seeing where they agree and disagree is more honest than trusting one.

**I scored for the real cost of being wrong.** RMSE treats a late prediction and
an early one as equally bad. They are not. Predicting that an engine has more life
than it really does can mean a missed failure, which on a critical system is far
worse than servicing a little early. So alongside RMSE I use the asymmetric NASA
prognostic score, which penalizes late predictions more heavily. The model choice
should follow the cost, not the other way around.

**I treated uncertainty as part of the answer.** A maintainer plans against a
confidence bound, not a point. The Bayesian model returns a mean and a spread for
every engine, and I check whether those intervals are actually calibrated. Where
they are not, I say so in the results rather than hide it. Knowing the limits of
a model is part of using it responsibly.

**I made it fully reproducible.** The repo includes the real, public NASA C-MAPSS
FD001 data, so anyone can clone and run the whole pipeline in one command and get
the numbers below. A synthetic data generator in the same schema is also included
for quick offline experiments, but the default and the reported results are the
real data.

---

## Architecture

```
data/                      SQL layer                 modeling                    reliability
─────────                  ─────────────────          ────────────────────        ─────────────
train/test/RUL   ──▶  SQLite: sensor_readings   ──▶  Python: RF, HistGBM     ──▶  R: Weibull fit,
(C-MAPSS format)      views: train_labeled,           prognostic metrics           Kaplan-Meier,
                      test_snapshot, lifetimes    ──▶  Python: Bayesian ridge        hazard, B10 life
                      (RUL labeled in SQL)             + interval calibration
```

---

## Build plan

I am building this in layers, and each phase is a self contained step I review
before moving on.

1. **Foundation** — project scaffold and the NASA C-MAPSS FD001 data (plus a
   synthetic generator in the same schema for offline runs).
2. **Data layer** — SQLite schema, loader, and the SQL views that label RUL.
3. **Modeling** — feature engineering, exploratory analysis, and the Random
   Forest and Gradient Boosting RUL models with prognostic metrics.
4. **Uncertainty** — a Bayesian model that returns calibrated predictive
   intervals, not just point estimates.
5. **Reliability** — a Weibull survival analysis of the fleet, plus final
   documentation and a full walkthrough.

---

## Results

_Populated as each phase lands. See the build plan above._

---

## Running it

```bash
pip install -r requirements.txt      # Python deps
# R deps: base + 'survival' + 'MASS' (ship with R; no extra install)

bash run_all.sh                      # full pipeline end to end
```

---

## Honest notes

- This uses the FD001 subset (single operating condition, one fault mode). The
  other C-MAPSS subsets (FD002 to FD004) add operating regimes and fault modes and
  are harder; the same pipeline extends to them.
- The Bayesian model assumes constant Gaussian noise. That is a simplification; if
  the noise grows sharply near end of life, a heteroscedastic model, quantile
  regression, or conformal prediction would give better-calibrated intervals. I
  check the calibration in the results rather than assume it.
- No sequence model yet. An LSTM or temporal CNN over the full trajectory is the
  natural next step and typically improves on tabular models for this dataset.

---

## Repository layout

```
turbofan-rul/
├── data/            NASA C-MAPSS FD001 data + optional synthetic generator
├── sql/             schema, loader, RUL labeling views
├── python/          EDA, RUL models, Bayesian uncertainty, shared utils
├── R/               Weibull / survival reliability analysis
├── outputs/         figures + metrics.json
├── run_all.sh       one command pipeline
└── WALKTHROUGH.md   plain language tour of every piece
```
