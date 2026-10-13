# NBA Unicorn & Breakout Hunting

**Could we have spotted future NBA breakouts, stars and "unicorns" before they became obvious, using only what was known at the time?**

This project treats scouting like backtesting an investment strategy. For each season from 2011-12 on, it rebuilds what was knowable at the end of that season, ranks players, and scores the rankings against what actually happened. Only then is the method applied to current players.

## Contents
- [Key findings](#key-findings)
- [Most Improved studies](#most-improved-studies)
- [How it works](#how-it-works)
- [Reproduce](#reproduce)
- [Project structure](#project-structure)
- [Limitations](#limitations)
- [What's next](#whats-next)

## Key findings

**Breakouts are partly predictable.** Strict walk-forward backtest, predictions for 2014-15 → 2024-25, players aged 25 or under:

| Outcome | How rare | Best model | Lift over random (95% CI) |
|---|---|---|---|
| Any breakout next season | 6.9% | Boosted trees | **4.2×** (3.3–5.3) |
| Scoring breakout next season | 4.9% | Boosted trees | **6.1×** (4.9–8.0) |
| Star season within 3 years | 1.6% | Current star score | **10×** (6.7–23) |

- **Simple is nearly as good as complex.** A 12-signal logistic regression reaches about 90% of the 197-feature model. Signals: already earning minutes, rising usage and minutes, self-creation, efficiency. Against: age, a late draft slot, already-high usage.
- **For stardom, current all-round quality beats every model.** With about 26 future stars to learn from, extra features overfit.
- **There are two routes to stardom.** Some players break out (Shai Gilgeous-Alexander, Giannis Antetokounmpo, Nikola Jokić); others climb steadily without one breakout season (Anthony Edwards, Devin Booker, Donovan Mitchell). Steady risers are visible early from current quality alone (8.6× random); breakout-route stars need trajectory signals (4.6–5.6×).
- **The models read trajectories, not single seasons.** Shai was ranked 37th of 229 young players after his rookie year, then 12th after year 2.
- **Unicorns come in two kinds:** rare *combinations* of strengths (Giannis, Jokić, Kevin Durant) and *extremes* with no comparable players (Victor Wembanyama is the most extreme player in the data).
- **Egor Dëmin after one season:** a typical 5.3% breakout chance for 2026-27. His rookie profile most resembles Kevin Huerter, Tyler Herro, Jamal Murray and Klay Thompson: shooters who broke out more often than average but rarely became stars.

**Data traps found along the way:** NBA.com's `PlayerIndex` returns *current* heights and positions for past seasons (a leakage trap); the 2019 switch to measured heights made 56% of players shorter overnight; the bio endpoint gives some players the wrong draft record; NBA.com's PIE rating over-represents big men among "stars" about 2×.

| | |
|---|---|
| ![Backtest lift with CIs](outputs/figures/06_backtest_lift_ci.png) | ![Shai vs LaMelo](outputs/figures/03_sga_vs_lamelo.png) |
| Walk-forward lift over random, with bootstrap intervals | Shai Gilgeous-Alexander vs LaMelo Ball, season by season |
| ![Unicorn map](outputs/figures/04_unicorn_map_2025_26.png) | ![Dëmin comps](outputs/figures/07_demin_comps_trajectories.png) |
| 2025-26: rare skill mixes vs no comparable players | Where players with a rookie season like Dëmin's went |

## Most Improved studies

**Could we have named each Most Improved Player (MIP) from the numbers, and what do the votes say "improved" means?** ([notebook 10](notebooks/10_mip_leaps.ipynb))

**Approach**
- **Data:** 404,000 player-games (2010-11 → 2025-26), with Hollinger game score as the one-number measure of a game.
- **Baseline:** each player's own previous season, skipping injury-shortened ones, so a healthy return isn't counted as a leap.
- **Inputs:** the change in every box-score stat, as absolute change (ΔX) and relative change (Δ%), plus team win % change, age and a second-year flag.
- **Model:** a choice model (conditional logit). One eligible player wins each season; scores become win chances that add up to 100%. Every season is predicted by a model that never saw it. Real vote totals ([Basketball-Reference](https://www.basketball-reference.com/awards/)) are used only to evaluate, never to train.

**Results**

| | |
|---|---|
| Winner ranked #1, from about 300 eligible players a season | **8 of 15 seasons** (median winner rank 1) |
| Same model, trained on earlier seasons only | 5 of 10 seasons |
| Using only games before the All-Star break | eventual winner already #1 in 7 of 15 |
| Our top 7 vs the real voting top 7 | 3.1 of 7 in common, on average |

- **Size beats percentage.** ΔX alone names the winner in 7 seasons; Δ% alone in 4.
- **Voters reward** a jump in all-round production (odds ×1.57 per extra point of game score), in scoring (×1.39 per extra point per game), a bigger offensive load, and a team that got better (×1.28 for winning 10% more games).
- **Voters discount** age (×0.88 per year), gains that come only from more minutes, and above all second-year players: 19% of the voting top 7, but no winner in 15 seasons.
- **Most winning leaps show from opening night.** For 11 of 15 winners, the first 10 games already held 80% or more of the season's jump.
- **One huge night is not a signal.** After 1,109 "eruption" games, the next seven looked like the seven before.
- **The winners the model misses crossed a milestone** rather than making the biggest jump: a first 20-ppg season (Goran Dragić), a first star-level season (Julius Randle), becoming the team's leading scorer (Tyrese Maxey, Paul George).

| | |
|---|---|
| ![MIP probabilities](outputs/figures/10_mip_final_probability_bars.png) | ![What voters reward](outputs/figures/10_mip_final_weights.png) |
| Predicted chance of winning (blue = our top 3, ★ = winner) | Every model weight, with 90% ranges from 500 refits |
| ![Winners week by week](outputs/figures/10_mip_week_by_week.png) | ![Top 7 vs real](outputs/figures/10_mip_top7_vs_real.png) |
| Each winner's season, week by week, against his baseline | Our top 7 vs the real voting top 7 |

**Limits:** 15 winners is a small sample, and the model sees box-score changes only. Awards that turned on narrative stay partly unexplained.

## How it works

| Notebook | What it does |
|---|---|
| `00`–`01` | Setup; which `nba_api` endpoints are league-wide and time-correct |
| `02_player_seasons` | 733 cached API responses → clean player-season table; shrinkage of noisy shooting %; season-relative scaling |
| `03_player_trajectories` | Level, trend and change for every feature, tested to be leakage-free |
| `04_unicorn_hunting` | Listed / body / style position spectrum; rarity and strangeness scores |
| `05_breakout_hunting` | Breakout labels relative to each player's own past; our own six-pillar star metric |
| `06_breakout_backtest` | Walk-forward backtest: rules, logistic, boosted trees, comps; intervals, calibration, sensitivity |
| `07_current_players` | 2026-27 outlook; Dëmin profile and historical comps |
| `08_breakout_board` | Each season's top-10 breakout picks vs what happened ([poster](outputs/figures/08_breakout_board.png), plus an interactive page in `outputs/breakout_board.html`) |
| `09_routes_to_stardom` | Breakout route vs steady route into the star tier |
| `10_mip_leaps` | Most Improved Player: weekly leaps, the choice model, the mid-season race, our top 7 vs the real vote |

**Anti-leakage rules**
- Features for season *t* use seasons ≤ *t* only; notebook 03 checks this by deleting later seasons and confirming nothing changes.
- A training example is used only once its outcome was known at prediction time.
- Preprocessing is fitted inside each fold.

There is also a local **Streamlit dashboard** for changing the star-score weights and breakout thresholds and seeing who qualifies: `streamlit run dashboard/app.py`.

Every significant choice, with its evidence, is logged in [docs/DECISIONS.md](docs/DECISIONS.md) (25 decisions).

## Reproduce

```bash
git clone https://github.com/dan-j-e/unicorn-hunting.git && cd unicorn-hunting
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .                 # makes `import unicorn` available
python -m unicorn.download       # ~733 NBA.com requests, ~40 min first time, resumable
```

Then run the notebooks in order (`00` → `10`). Each writes the table the next one reads. Raw responses are cached in `data/raw/`, so re-runs make no API calls. Notebook 10 also fetches 16 seasons of game logs and 15 Basketball-Reference award pages (cached).

## Project structure

```
notebooks/        numbered research pipeline (00 → 10), saved with outputs
src/unicorn/      reusable code
  raw, download            cached NBA.com access and the full download list
  player_season, columns   clean tables and the data dictionary
  features, trajectories   shrinkage, season-relative scaling, leakage-safe trends
  position, unicorn        position spectrum and unicorn scores
  labels, backtest, comps  breakout/star labels, walk-forward engine, comparables
  gamelogs, mip, bref      game-level data, the Most Improved model, voting results
  board, stats, plotting   breakout board, statistics helpers, chart style
dashboard/app.py  Streamlit app
docs/DECISIONS.md decision log
outputs/          figures and tables
data/             raw and processed data (git-ignored, rebuilt from code)
```

## Limitations
- **Box-score data only** (NBA.com). No play-by-play, lineups, injuries, contracts or scouting; on-court net rating mixes player and team quality.
- **Few positive cases:** about 26 future stars, 28 production breakouts and 15 MIP winners, so those results have wide intervals.
- **"Star" is our own definition** (six equally weighted pillars); one-dimensional scorers rarely qualify, by design.
- **One rookie season is thin evidence.** Predictions for second-year players are far better informed than for rookies.

## What's next
See [TODO.md](TODO.md): player archetypes and "who is similar to who", explained picks, a story-led write-up, and tracking the 2026-27 predictions.
