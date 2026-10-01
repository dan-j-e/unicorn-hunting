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
pip install -e .   # makes `import unicorn` (src/unicorn) available in notebooks
```

## Methodological decisions
| # | Decision | Rationale / caveat |
|---|---|---|
| D1 | Unit of analysis = one consolidated row per player-season (`LeagueDashPlayerStats`); `TEAM_COUNT` kept as a traded flag | Player development is the object of study. Team context for traded players needs per-team splits, which we'll add only if needed. |
| D2 | Request totals and derive rates ourselves; take possession-based rates (USG%, AST%, …) from NBA.com | Totals add up across seasons and stints, which rolling windows and shrinkage need. |
| D3 | Height/weight = **as listed each season** (`LeagueDashPlayerBioStats`) | Time-correct. Caveat: the NBA switched to measured heights in 2019-20 (56% of players got shorter, mean −0.57 in), so there is a level shift at that season. |
| D4 | Listed position = **as listed each season** (`CommonTeamRoster`), never `PlayerIndex` | `PlayerIndex` returns current values for any season, which leaks future information. Roster position is missing for about 9% of player-seasons (about 1.4% of minutes). |
| D5 | Also build a **derived continuous position spectrum** from same-season stats; evaluate against listed position | Listed labels are coarse (G/F/C + hybrids). Where derived and listed position disagree may itself be a "unicorn" signal. |
| D6 | Age = exact age on **Feb 1** of the season (from roster birth date); NBA integer age as fallback (`age_source`) | Mid-season convention. Birth date is a fixed fact, so it can come from any season's roster without leakage. |
| D7 | **No rows dropped** for low minutes; reliability columns (`min`, `poss`, `fga`, `fta`, `fg3a`) kept | Minimum-minute thresholds are a modelling choice. They will be toggleable and their effect examined. |
| D8 | Playoffs in a **separate table** (`player_season_playoffs`), same key | Not every player has playoff data, and keeping it apart prevents accidental leakage. Planned use: does *early* playoff experience predict development? |
| D9 | Draft info from `DraftHistory` (by player ID), not the bio endpoint | The bio endpoint carries wrong draft records for some players (e.g. Walker Russell Jr. has his father's 1982 pick). |
