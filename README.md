# NBA Unicorn & Breakout Hunting

**Question:** Could we have identified future NBA stars and "unicorns" *before* they became obvious, using only information available at the time?

The approach is a historical backtest, like testing an investment strategy: for each past season, rebuild what was knowable then, make predictions, and score them against what actually happened later.

## Principles
- **No leakage.** A feature for season *t* may use only data from seasons ≤ *t*.
- **Walk-forward validation** (expanding window), 2011-12 → 2025-26. 2026-27 is held out as a live test.
- **Simple, interpretable baselines** before complex models.
- **Raw data is immutable.** Processed data is fully reproducible from code.

## Layout
```
notebooks/   numbered research pipeline (00_setup → 07_current_players)
src/         reusable code (data loading, features, validation)
data/raw/    untouched API responses (git-ignored)
data/processed/  cleaned tables (git-ignored)
models/      fitted models (git-ignored)
outputs/     figures and tables
```

## Data
- [`nba_api`](https://github.com/swar/nba_api) (NBA.com stats)

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
