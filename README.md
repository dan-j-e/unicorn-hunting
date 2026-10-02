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
| D10 | **When undecided, keep the feature**; redundancy is flagged, not deleted | Overfitting can be pruned later; information dropped too early cannot be recovered. Final selection happens inside each walk-forward window. |
| D11 | Shooting percentages shrunk with a **beta-binomial prior per season × listed-position group** (`*_shr`) | Validated on the first training window: 29–53% lower next-season error than raw. |
| D12 | **Season-relative** z-score and percentile for every feature, scaled on that season's ≥500-min players (`*_z`, `*_pctl`); raw kept | League 3PA rate rose from 0.22 to 0.42 and mid-range rate fell from 0.29 to 0.09 over 2011-26. |
| D13 | Season-to-season change is measured against the **previous season played**, with `seasons_missed` recording gaps | Keeps injury comebacks (e.g. Klay Thompson 2018-19 → 2021-22) instead of blanking them; the gap itself is informative. |
| D14 | Trajectories: 3-season rolling **level** and **trend** (shooting % weighted by attempts, other stats by minutes) plus **vs-own-past** deviation; outlier seasons kept as they happened | Level, direction and "unusual for him" are different signals. No player-history shrinkage: the actual season is kept and flagged. |
| D15 | Position spectrum on one 1 (G) → 5 (C) scale: **listed**, **body** (height/weight) and **style** (stats only); ridge models fitted on seasons ≤ *t* | Gaps between body and style are a direct unicorn signal (e.g. LeBron, Jokić). Out-of-sample R² vs listed position: style 0.68–0.79, body 0.76–0.83, both declining as the league becomes positionless. |
| D16 | Two unicorn scores, each relative to that season only: **combination** (summed excess rarity of trait pairs a player is top-20% in) and **strangeness** (mean distance to his 5 most similar rotation players) | Rejected after testing: "rarest single pair" (saturates; rewards being #1 at one skill) and robust Mahalanobis distance (treats the whole cluster of traditional centres as outliers). Headline lists require ≥ median impact; raw scores kept. |
| D17 | **Own star metric**: six equally weighted pillars (scoring, creation, rebounding, defense, impact, trust) from that season only, half-adjusted for body size (dial 0.5); star season = top 5% (≥ 1,500 scaled min). Breakout labels: production, role, scoring and any, predicted one season ahead; star predicted within 3 seasons | PIE over-represents bigs (27% of PIE stars vs 14% of players) and media awards carry their own biases. At dial 0.5 bigs are 18% and guards 33% of star seasons. |
| D18 | **Walk-forward backtest**: test season *t* uses features ≤ *t*; a training row from season *s* is used only if its outcome was known by *t* (*s* + horizon ≤ *t*); preprocessing fitted per fold. Population: all players aged ≤ 25 (stars excluded for the star outcome). Metrics: average precision and lift, top-*k* hit rate | Breakouts are rare (1–7%), so accuracy is meaningless. First results: any breakout 3.4×, scoring 4.8×, star-within-3 10× (current star score). |
| D19 | Production models: **boosted trees** for breakout probabilities (best lift and calibration); **current star score** for star potential; **nearest comps** for explanation only | Backtest with player-bootstrap CIs: trees 4.2× any / 6.1× scoring; star score 10× for star-within-3, beating every trained model; inner-window tuning did not help. |

## Backlog (revisit later)
- **External advanced metrics**: Basketball-Reference BPM / OBPM / DBPM / VORP / Win Shares / PER, and CraftedNBA metrics. Popular with analysts; would add impact measures that NBA.com lacks. Check each site's terms and rate limits before scraping. Use as features (lagged) and as alternative outcome definitions.
- **Interactive star dashboard**: sliders for the six star-pillar weights and the size-fairness dial (`unicorn.labels.STAR_PILLARS`, `SIZE_ADJUSTMENT`), showing live who qualifies as a star by season. Current choice (D17): equal pillar weights, dial 0.5. One-dimensional scorers (Booker, Edwards, Brunson) rarely qualify under these settings, which is intended for now.
