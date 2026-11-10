# Project audit

A record of the audit begun on 11 November 2026 (TODO, Phase A). Each step lists what was checked, what was found and what was done.

## A1. Relevance

**Checked:** all 21 notebooks, all 69 figures, the README sections, and the other folders (`archive/`, `models/`, `dashboard/`, `outputs/tables/`, `scripts/`).

**Overall:** every notebook still answers a question the project needs, and all 21 run without errors. Nothing needs deleting. The main problem is that some notebooks are **historical**, recording an earlier stage that later work replaced, but they do not say so. A reader could take an old number for the current one.

### Notebooks

| Notebook | Question it answers | Status | Action |
|---|---|---|---|
| 00 Setup | Which NBA.com endpoints can be trusted, and are they time-correct? | Foundation | Keep. Remove emojis (A6) |
| 01 Data exploration | What does the raw data look like? | Foundation | Keep. Run its one unrun cell (imports only). Remove emojis (A6) |
| 02 Player seasons | The clean player-season table; shrinkage; season-relative scaling | Foundation | Keep |
| 03 Player trajectories | Level, trend and change for every feature, without leakage | Foundation | Keep. Remove emojis (A6) |
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
| 18 Ty Jerome effect | Do hot starts like Jerome's last? | Current (fed D39) | Keep. Remove emojis (A6) |
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
| `models/` | An empty folder kept only by a placeholder file; no model is ever saved there | Remove |
| `archive/` | Ignored by git (an early scratch notebook); not part of the repository | No change |
| `dashboard/app.py` | Parked; still works; contains emojis | **Your decision:** remove it from the repository, or keep it with emojis removed |
| `outputs/tables/` | Three CSV tables from notebooks 07 and 08 | Keep |
| `scripts/update_mip_race.sh` | Used for every live update | Keep |
| `outputs/breakout_board.html` | Interactive breakout board from notebook 08; no longer linked from the README | Keep and link it again |

### README

Every section is relevant. Two gaps carry into later steps:
- There is no reading path for a newcomer (A3).
- There is no glossary for the recurring terms (A2).
