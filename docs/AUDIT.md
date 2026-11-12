# Project audit

A record of the audit begun on 10 November 2026 (TODO, Phase A). Each step lists what was checked, what was found and what was done.

## Summary

**Why:** the project grew one question at a time over six weeks. Before building anything new, every part was checked for three things: that it is still **relevant**, **easy to understand** for a reader who did not build it, and **educational**. Accuracy and shared code were checked along the way.

| Step | What changed | Why it matters |
|---|---|---|
| A1. Relevance | Every notebook kept; 10 and 15 marked historical; 07 dated; the interactive breakout board linked again; an unused folder removed and a parked dashboard archived | A reader can no longer mistake an old model's numbers for the current ones |
| A2. Easy to understand | Every notebook opens with **In brief** (question, answer, decisions, where it fits) and closes with findings; a glossary in the README; stale lines corrected | The answer is at the top, and every term means one thing |
| A3. Educational | Plain-words notes for five methods that were named but not explained; a reading path in the README | A newcomer knows where to start and why each method was chosen |
| A4. Accuracy | Every findings number checked against its notebook's output by script; two stale results and a wrong date corrected; every notebook's findings dated | Every number can be traced to an output, and every finding says when it was written |
| A5. Code | Model scoring and the live-race builder moved into `src/unicorn/` (`mip_eval`, `live_race`); five notebooks re-run with identical outputs | One definition of each test, with the same names everywhere |

**What it did not change:** no model, decision or result. Every correction was to wording, a stale number or a date, and the refactor was verified to leave every output unchanged.

**Next:** Phase B (points per game as the illustration, not the model), then Phase C (similar players at the same career stage). See [TODO.md](../TODO.md).

## A1. Relevance

**Checked:** all 21 notebooks, all 69 figures, the README sections, and the other folders (`archive/`, `models/`, `dashboard/`, `outputs/tables/`, `scripts/`).

**Overall:** every notebook still answers a question the project needs, and all 21 run without errors. Nothing needs deleting. The main problem is that some notebooks are **historical**, recording an earlier stage that later work replaced, but they do not say so. A reader could take an old number for the current one.

### Notebooks

| Notebook | Question it answers | Status | Action |
|---|---|---|---|
| 00 Setup | Which NBA.com endpoints can be trusted, and are they time-correct? | Foundation | Keep |
| 01 Data exploration | What does the raw data look like? | Foundation | Keep. Run its one unrun cell (imports only) |
| 02 Player seasons | The clean player-season table; shrinkage; season-relative scaling | Foundation | Keep |
| 03 Player trajectories | Level, trend and change for every feature, without leakage | Foundation | Keep |
| 04 Unicorn hunting | What is a unicorn: rare combinations or extremes? | Current | Keep |
| 05 Breakout hunting | What counts as a breakout and a star? | Current | Keep |
| 06 Breakout backtest | Can breakouts and stars be predicted a season ahead? | Current | Keep |
| 07 Current players | 2026-27 breakout outlook; Egor Dëmin | Current, dated | Keep. Add the date the outlook refers to |
| 08 Breakout board | Each season's top-10 picks against what happened | Current | Keep. Restore the README link to the interactive page `outputs/breakout_board.html` |
| 09 Routes to stardom | Breakout route against steady climb | Current | Keep |
| 10 Most Improved leaps | Can the winner be named from the box score? The **first** Most Improved model | **Historical:** its model predates D27, D38 and D39 | Keep: it shows how the model was first built. Add a status note at the top pointing to notebooks 12 (current model) and 19 (how it evolved) |
| 11 Preseason | Who is set up to improve before the season? | Current | Keep |
| 12 Live race | The live 2026-27 race, day by day | Current | Keep |
| 13 Archetypes | What kinds of players are there? | Current | Keep. 13C (five clusters) is the step to the chosen eight, so it stays as part of the reasoning |
| 14 Team changes | Do new teams or teammates make a Most Improved Player? | Current (fed D29) | Keep |
| 15 Most Improved 2000-26 | Three views of every season since 2000-01 | **Historical:** uses the model before D38 and D39; notebook 19 reruns the same test with every decision | Keep. Add a status note pointing to notebook 19 |
| 16 Do leaps last? | The blip test on 609 leaps | Current | Keep. Its leap definition is points per game only (Phase B) |
| 17 Already a star | Do voters pass over established stars? | Current (fed D38) | Keep |
| 18 Ty Jerome effect | Do hot starts like Jerome's last? | Current (fed D39) | Keep |
| 19 Predictor evolution | How the model was built, one decision at a time | Current | Keep |
| 20 Calibration | Are the chances honest? | Current (fed D40) | Keep |

**Reading order.** The numbers follow the order the work was done, not the order a reader needs: archetypes (13) sit among the Most Improved notebooks. Renumbering would break links and the commit history, so the notebooks keep their numbers and the README gains a reading path instead (A3).

### Figures

- 69 figures: 22 are shown in the README; the other 47 illustrate their notebooks and stay there.
- Every figure is produced by current code: by its notebook, or by the shared chart functions in `src/unicorn/archetypes.py`.
- Notebook 10 saves pairs of early and final versions of the same chart (for example `10_mip_vote_weights.png` and `10_mip_vote_weights_final.png`). Both are part of how that notebook builds up its model, so both stay, and the README uses only the final versions.

### Other folders

| Item | Finding | Recommended action |
|---|---|---|
| `models/` | An empty folder kept only by a placeholder file; no model is ever saved there | **Removed** |
| `archive/` | Ignored by git (an early scratch notebook); not part of the repository | No change |
| `dashboard/app.py` | Parked; still works | **Archived:** moved to `archive/dashboard/` (kept locally, not in the repository) to revisit later; Streamlit removed from the requirements |
| `outputs/tables/` | Three CSV tables from notebooks 07 and 08 | Keep |
| `scripts/update_mip_race.sh` | Used for every live update | Keep |
| `outputs/breakout_board.html` | Interactive breakout board from notebook 08; no longer linked from the README | Keep and link it again |

### README

Every section is relevant. Two gaps carry into later steps:
- There is no reading path for a newcomer (A3).
- There is no glossary for the recurring terms (A2).

### Actions completed (10 November)
- Status notes added at the top of notebooks 10 and 15, pointing to notebooks 12 and 19; both marked as historical in the README's notebook table.
- Notebook 07 dated: its outlook stands at the end of 2025-26.
- The README links the interactive breakout board again.
- `models/` removed; the parked dashboard archived locally (`archive/dashboard/`) to revisit later.
- Notebook 01's cache check corrected: NBA.com has since added two columns and respelled two names, while every statistic still matches, so the check now compares statistics and reports such changes instead of failing.

## A2. Easy to understand

**Checked:** how every notebook opens and closes; whether each names the decisions it rests on; whether the recurring terms are used consistently.

**Found:**
- No notebook opened with a short answer. A reader had to reach the findings, often 20–50 cells down, to learn the result. The openings followed three or four different styles.
- Notebooks 00 and 01 had no findings.
- Several notebooks did not name their decisions (for example, 05 defines D17 and 14 led to D29, but neither said so).
- Terms were consistent once read closely, but undefined: "leave-one-out" is the short form of "leave-one-season-out"; "× random" (breakouts) and "× a blind guess" (Most Improved) are different measures.
- Stale lines: notebook 18 still gave Ty Jerome's chance before D39; notebook 19 called calibration "the next step" after notebook 20 had done it; notebooks 17, 18 and 20 cited TODO item numbers that no longer exist; notebook 02 said 703 cached requests where its own output shows 733.

**Done:**
- Every notebook (00–20) now opens with **In brief**: the question, the answer, the decisions it rests on (linked to the decision log), and where it fits. Status and as-of notes stay directly under the title. Where the original opening also began with "Question", it is now labelled "In detail".
- Notebooks 00 and 01 close with findings.
- The stale lines above are corrected.
- The README gains **Terms used throughout**: a glossary of testing, Most Improved and measurement terms, linked from the contents. Both "× random" and "× a blind guess" are kept, because they measure different things.

## A3. Educational

**Checked:** where each method is first named in the notebooks (23 methods and measures, from shrinkage to temperature scaling), and whether it is explained in plain words at that point; whether a newcomer can tell where to start.

**Found:**
- Most methods are explained well where they first appear: the choice model (10), clustering and its three checks (13), the backtest metrics (06) and temperature scaling (20).
- Five were named but not explained: shrinkage (02, described only in technical terms), Spearman correlation and the player-level bootstrap (02), ridge regression (04), and logistic regression and the Brier score (06).
- There was no reading path. The numbering follows the order of the work, so archetypes (13) sit among the Most Improved notebooks, and the first Most Improved notebook (10) is historical.

**Done:**
- An *In plain words* note at each of the five places, saying what the method does, why it suits the problem, and which decision it belongs to (D10, D11, D15, D19).
- The README gains **How to read this project**: a ten-minute tour, then three routes (Most Improved, breakouts and stars, unicorns and playing styles) with the order to read the notebooks and why, plus where to check the data.

## A4. Accuracy

**Checked:**
- Every number in every notebook's findings against that notebook's own outputs, by script: decimals, percentages and × values matched at the same precision, and whole numbers of 100 or more matched exactly. Anything not found was checked by hand.
- Every number in the README against the notebooks and the decision log.
- Every date written in the project against the git history.

**Found:**
- **Most findings match their outputs.** The exceptions are values read off charts (notebooks 03 and 13) and values quoted from other notebooks (19, 20), all of which check out at their source.
- **Two stale results:**
  - Notebook 10C (and the README) gave 1,109 "eruption" games and +3.5 for the next seven; the current output is 1,089 and +3.4. The conclusion is unchanged.
  - Notebook 02B gave the tables as 113 and 98 columns; they are now 123 and 107.
- **A wrong date:** the work on D39, D40, the archiving and this audit was dated 11 November in the notebooks, TODO, this file and a code comment. The git history shows 10 November.
- **Findings were undated** in all but three notebooks (07, 12 and the status notes in 10 and 15).

**Done:**
- The two stale results and the date are corrected everywhere.
- Every notebook's In brief now has a **Dated** line: when its findings were written (taken from the git history, ignoring the audit commits) and that the numbers were checked against the outputs on 10 November 2026. For notebook 12 it says the live findings are updated by hand after each run, the latest being 8 November (day 20).

## A5. Code

**Checked:** every function defined inside a notebook, and which of them were copied between notebooks.

**Found:** two pieces of logic had been copied, with small differences between copies:
- **Scoring a Most Improved model** (fit on the strict or leave-one-out seasons, find the winner's rank, compute × a blind guess) was written out separately in notebooks 11, 17 (twice), 18 and 19, with different names for the same results ("top 7", "in top 7"; "× blind guess", "times better than a blind guess").
- **The live race's candidate builder** (the 2026-27 player table and the candidates on a given day) was copied between notebooks 12 and 17; notebooks 19 and 20 each built the live race's inputs for past seasons by hand.

**Done:**
- `src/unicorn/mip_eval.py`: `winner_ranks` and `scorecard` (one way to score a model, with the glossary's names: winner #1, in top 3, in top 7, in top 20, median rank, × a blind guess), `current_frame` (the live race's inputs on any past day) and `LIVE_INPUTS`. Used by notebooks 11, 17, 18, 19 and 20.
- `src/unicorn/live_race.py`: `live_games`, `player_table_with_live_season` and `race`. Used by notebooks 12 and 17.
- **Verified unchanged:** notebooks 11, 17, 18, 19 and 20 were re-run; every number in every output and every chart is identical to before. Notebook 12 downloads the newest games whenever it runs, so it was not re-run here (that would also update the live race); instead the shared builder was checked against notebook 12's old code on the same cached data, on days 2, 13, 19, 29 and 84, and gave identical results. Its next update run will use the shared code.

**Left as they are, deliberately:**
- Notebook 12's own `winner_ranks` re-chooses the turning point inside every fold (D32), which the shared version does not do.
- Notebook 15's `score` summarises the 2000-26 walk-forward backtest (`mip_history.walk_forward`); the notebook is historical.
- Notebook 10 uses the earlier `out_of_sample_probabilities` and `summarize` in `mip.py`, which choose λ inside each fold (before D30); the notebook is historical.
- Two names shared by unrelated helpers (`frame` in 16 is a chart helper; `short` in 08 and 10 shortens player names) are not duplicated logic.

---

# Audit 2: overfitting, focus and the betting markets (12 November 2026)

**Why:** after three model changes in three days (D41–D43 tested, D41 and D42 adopted), and a live board that disagrees with the betting markets, the question was whether the model is improving or overfitting, and whether the work is on track.

## Are the recent gains real?

Method ([scripts/audit_gains.py](../scripts/audit_gains.py)): for each model version, every season's strict-test score (the log of the winner's chance times the number of candidates); versions compared season by season; the seasons resampled 5,000 times.

| Comparison | Day 19 | Day 85 | Season's end | Seasons better / worse (season's end) | Verdict |
|---|---|---|---|---|---|
| Stage 3 (the voter inputs) → today (D42) | 5.1× → 6.8× | 16.1× → 20.5× | 19.2× → 26.1× | 16 / 5 | **Real:** better in every resample (+21% to +54% at season's end) |
| 10 November (D39) → D41 (game-score turning point) | 6.5× → 6.6× | 19.9× → 19.8× | 24.9× → 24.9× | 9 / 12 | **No measurable change:** 40–57% of resamples |
| D41 → D42 (already clearly a star) | 6.6× → 6.8× | 19.8× → 20.5× | 24.9× → 26.1× | 19 / 2 | **Consistent but small:** +2% to +7% |
| 10 November → today | 6.5× → 6.8× | 19.9× → 20.5× | 24.9× → 26.1× | 11 / 10 | **Not clearly:** 71–86% of resamples; the range includes no gain |

**Reading it:**
- The model's structure (baseline fix, voter inputs, turning point, already an All-Star) is robust.
- The recent changes are small. D41 is a tie on this test bed (it passed notebook 21B's rule by margins too small to detect). D42 is consistent, but it was chosen *after* looking at these seasons, which resampling cannot correct for.
- About 21 inputs now explain 26 winners, after roughly a dozen tests on the same seasons. The penalty (λ = 3) limits the damage, but each new input is now more likely to fit noise than signal.

## Are we getting sidetracked?

- **Three of the last five model changes were prompted by names on the live board** (D38: Sengun; D39: Jerome; D42: Wembanyama and Flagg). Each passed a test written in advance, but choosing what to test because the board "looks wrong" pulls the model towards our intuitions.
- **Phase B drifted.** Two of its four rules are tested (D41, D43); an unplanned input was added (D42); the blip test, the lookalikes and B3 are still open.
- **Two bugs reached the outputs** on 12 November (a calibration cell building its own frame on the old turning point; missing baselines in the new inputs). Both were caught by hand and fixed; automated tests (T1–T3) would catch this class of bug.

## Our board against the betting markets (12 November)

| | Our board (11 November) | Markets (snapshots of varying dates) |
|---|---|---|
| Ty Jerome | #1, 12.3% | #1: about 37% (Kalshi), +250 at FanDuel (about 28% before the margin) |
| Ajay Mitchell | 5th, 3.3% | #2: 21% (Kalshi), +600 |
| Brandon Miller, Dylan Harper | 42nd; not near the top | near the top on some books |

- **Agreement on who leads; disagreement on how sure to be.** Our caution is deliberate and tested: 3 of 19 early favourites given 25%+ won (D40), and no player returning from a lost season has won (D39).
- **The market names we lack come from expectations, not the box score.** Brandon Miller (20.2 → 20.6 points) has not jumped yet; Dylan Harper is a second-year player, and none has won since 2006-07.
- **Markets are not the truth either,** and copying them would be its own form of overfitting.

## Decisions

- **D44: the live model is frozen** from 12 November until the end of 2026-27 (bug fixes only), so this season is a genuine out-of-sample test. New ideas are tested and recorded for 2027-28.
- **D45: the markets become a benchmark, not an input.** A weekly snapshot (`benchmarks/mip_markets_2026_27.csv`) is scored against our dated chances at season's end.
- **Next:** finish Phase B without touching the live model (the blip test shown alongside; the lookalikes), then the automated tests (T1–T3).
