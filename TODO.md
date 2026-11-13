# To do

**Goal:** make the project honest about its metrics (points as the illustration, not the measure), test it automatically, then build the comparisons (similar players, value against reputation, how players develop) and a live site. The analytical decisions are made deliberately, one step at a time.

## Current plan

### Restructure: one notebook per segment (agreed 13 November, D47)

Each segment is one notebook, built from the existing ones, on its own branch and pull request, in this order. The originals move to `notebooks/archive/` as each segment replaces them. Every number is checked against the original output before it goes in.

- [x] **0 Data** (`0_data.ipynb`, from 00–03 and the table builds of 04, 10 and 17; 13 November). Builds every table the segments read. Breakout, star and unicorn work (04–09) archived.
- [x] **1 The basic Most Improved race** (`1_mip_basic.ipynb`, from 10; 13 November). One finding corrected: 9 of 15 winners, not 11, had 80%+ of their leap in their first 10 games.
- [x] **2 Playing styles** (`2_play_styles.ipynb`, from 13; 13 November). Stability re-measured over 20 pairs of halves: five and six are about equally stable (0.83, 0.79), not 0.87 and 0.76.
- [x] **3 Candidate investigations** (`3_mip_investigations.ipynb`, from 14, 16, 17, 18 and 21; 13 November): four player-driven case files (Alexander-Walker, Ty Jerome, already a star, an open role). Calibration (20) and the game-score turning point (21B) move to segment 4. Quick tests re-run; the slow ones (17, 21) cited.
- [x] **4 The revised race** (`4_mip_race.ipynb`, from 11, 15, 19, 20, 21B and 22; 13 November): six checkpoints (after the previous season, preseason, day 15, day 30, the All-Star break, season's end; D48), every model iteration, both tests, honest chances, and 2026-27 at each checkpoint. New finding: by the All-Star break the race is essentially decided (winner in the top 7 in 19 of 21 strict seasons).
- [x] **4b The live race** (`4b_live_race.ipynb`, renamed from 12; 13 November). The update script points to it.
- [x] **README** rewritten around the four segments (13 November): one section per segment, the breakout work in a short archived section, about 290 lines instead of 690.


Work through the phases in order. Tick each box when it is done, and record any decision in [docs/DECISIONS.md](docs/DECISIONS.md).

> **The live Most Improved model is frozen until the end of 2026-27 (D44, 12 November).** Bug fixes only. New Most Improved ideas are tested and recorded, but take effect from 2027-28. See [Audit 2](docs/AUDIT.md).

**Order:** the restructure (below, agreed 13 November) → tests → F → C → D (from January, when there are enough games) → E → G. A is done; B is done (13 November) apart from B3, the 2027-28 package.

### Phase A — Audit what we have

The aim: every notebook, chart and section is **relevant**, **easy to understand** and **educational** for a reader who did not build it.

- [x] **A1. Relevance** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). List every notebook (00–20), figure and README section. For each, decide: keep as is, update, merge, or move to `archive/`. Flag anything superseded by a later decision (for example, notebook 10's model before D27, D38 and D39).
- [x] **A2. Easy to understand** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). Every notebook opens with the question, a plain summary of the answer, and its decisions; and closes with findings. Use the same terms everywhere ("strict", "leave-one-out", "× a blind guess", "baseline season"), with a glossary in the README.
- [x] **A3. Educational** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). Every method choice is explained in words, with a link to its decision; a "how to read this project" path in the README (which notebooks to read, in what order, and why).
- [x] **A4. Accuracy** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). Every number in the README and in each notebook's findings matches that notebook's latest output. Findings carry the date they were written.
- [x] **A5. Code** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). Shared logic lives in `src/unicorn/`, not copied between notebooks (for example, the live-race candidate builder appears in notebooks 12, 17, 18 and 19). Consistent names.
- [x] **A6. Record** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). Write the audit results down (what changed and why), and update the README.

### Phase B — Points per game is the illustration, not the model (closed 13 November; B3 waits for 2027-28)

**The principle:** charts use points per game (PPG) because it is the most familiar statistic for a casual reader. The models should use **every relevant metric we have**, as the playing-style clusters in notebook 13 do with 15 measures.

**Where we stand (checked 10 November):**

| Part of the project | What it uses now | PPG's role |
|---|---|---|
| In-season Most Improved model (live race) | 17 inputs: changes in points, rebounds, assists, steals, blocks, minutes, game score and shooting efficiency; relative changes; team, age, second year; flags | One input among several, but the largest weight |
| Preseason Most Improved model | 16 inputs: minutes, points, usage, team wins, age, second year, new team, last season's trend, preseason production, shot volume and shooting; flags | One input among several |
| Breakout models (notebook 06) | 197 features | One of many |
| Playing-style clusters (notebook 13) | 15 style measures | Not used, by design |
| **Scoring turning point** (D27) | Last season's PPG above 20 | **The definition** |
| **"A 20-point scorer left"** (D29) | The departed player's PPG | **The definition** |
| **The blip test and leaps** (D33, notebook 16) | Share of the PPG jump kept | **The definition** |
| **Ty Jerome lookalikes** (notebook 18) | Up 8+ PPG at day 19 | **The definition** |

- [x] **B1. Inventory** (12 November; notebook 21A). Confirm and extend the table above for every model and rule, and add it to the README.
- [x] **B2. Test all-round versions of the PPG-defined rules.** For each rule above, test the same idea on an all-round measure (game score, or a combination of production measures) and keep whichever does better in the strict test:
  - [x] the turning point on last season's game score (12 November; notebook 21B, D41): **game score in the live race; points kept before the season**;
  - [x] "a star left", measured by usage or game score rather than points (12 November; notebook 21E, D43): **points kept**;
  - [x] the blip test and leaps (13 November; notebook 16D, 12D): **shown on game score alongside the points verdict, not decided** (D46). Game score agrees with points on 84% of verdicts; the break matches the full season 83% of the time (86% on points). D33's points verdict for Alexander-Walker stays as written; the game-score share kept is printed next to it (12D), and notebook 16's agreement check is repeated on game score as a description;
  - ~~lookalikes on an all-round jump~~: **moved to Phase C** (C8, D46), which finds similar players at the same stage on every metric.
- [x] **B2b. "Already clearly a star" beyond All-Star selections** (12 November; notebook 21C–21D, D42): a baseline game score of 16+ and last season in our star tier, both now in the live race. Decided by the strict test on the same seasons, not by the board.
- [ ] **B3. The 2027-28 package: one test, written before the season ends** (D46; the live model is frozen until then, D44). Tested together, once, instead of one idea at a time:
  - more metrics in the Most Improved models: usage, shot profile and the other style measures from notebook 13, and box-score defence (some only exist from 2011-12, which shortens the test);
  - one "established player" measure in place of the five overlapping inputs (baseline game score, the turning point, the 16+ flag, the star tier, already an All-Star; Audit 3);
  - a turning point fixed before the season instead of re-chosen daily (it flips between values with no change in the evidence; D32);
  - **every setting chosen inside each training window** (λ, turning points, thresholds), so the strict score is genuinely strict (Audit 3);
  - 2026-27 as the final holdout. The decision rule is written and agreed before any of it runs.
- [x] **B4. Say it plainly** (13 November): one caption line on every chart where points stand in for the model (notebooks 10, 11, 12, 16, 18), saying what the model uses instead; notebooks 11 and 12 say so under their inputs; the README's "Beyond points per game" section and its inventory table list each model's inputs.
- [x] **B5. Record** (13 November): the results are D41, D42 and D43; the revision and the blip test shown alongside are D46. Nothing else needed deciding.

### Between phases — Tests and automatic checks
Moved up from Later: the strongest sign that the work is engineered, not just explored, and it guards the shared code from the audit.
- [ ] **T1. Leakage tests:** for example, deleting later seasons changes nothing (as notebook 03 checks by hand), and a live-race day uses no later game.
- [ ] **T2. Code tests** for the shared modules (`mip_eval`, `live_race`, `leaps`, `allstars`, `hot_start`).
- [ ] **T3. GitHub Actions** runs them on every pull request, so each shows a green tick (on a small cached sample, not a full download).

### Phase C — Similar players at the same career stage

**The question:** for each 2026-27 candidate at a given point in time, which past players looked most like him at the same stage of their careers? How did *their* season finish, and how did their careers turn out?

- [ ] **C1. Define the stage and the point in time.** Options: same NBA season number (second season, third…), same age, or both; at a given day of the season (as in the live race) or at season's end.
- [ ] **C2. Choose the measures.** All metrics, not PPG alone: production (box-score rates), style (notebook 13's 15 measures), role (minutes, usage, starts) and efficiency.
- [ ] **C3. Adjust for era.** Use notebook 13's findings (confirmed 10 November: notebook 13 only): compare each measure with its own season's league (13D), and use the 2000-26 history (13E) to see how roles shifted.
- [ ] **C4. Method.** Nearest neighbours for each candidate, and clusters of similar players at each stage.
- [ ] **C5. Outcomes.** For each group of lookalikes: how the rest of that season went (jump kept, Most Improved votes) and how the career went (next one to three seasons, star and breakout labels, peak, moves between the eight kinds).
- [ ] **C6. Apply it** to the 2026-27 candidates, and show it in the live race.
- [ ] **C7. Record** the decisions and update the README.
- [ ] **C8. The Ty Jerome lookalikes, redone** (moved from B2, D46): notebook 18's hot starters (up 8+ points at day 19) found again on every metric at the same stage, as the first worked example of this phase. Descriptive: it feeds no model while the live model is frozen.

### Phase D — Has the breakout prophecy come true so far? (later)

**The question:** standing at the end of 2025-26, the breakout model (notebook 07, D19) named its top candidates for 2026-27. For the top 10 for any kind of breakout: what did we predict they would become, and how are they tracking now?

- [ ] **D1. Freeze the predictions.** The top 10 by breakout chance from notebook 07, exactly as written on 2 October 2026 (notebook 07 is dated and not updated, so the list cannot drift). Alongside each: star chance, route to stardom (09) and playing-style cluster (13).
- [ ] **D2. "What we think they will become".** Which kind of breakout each is most likely to make (production, role or scoring). Options: the existing "any breakout" model plus the player's strongest signals; or separate models for each kind (the backtest in 06 supports scoring best, role least).
- [ ] **D3. How they are tracking.** Each label's tests, applied to the season so far from game logs: points, minutes, usage, efficiency and all-round production against the player's own past (all metrics, not points alone; see Phase B). A partial season needs care: the labels assume 1,200+ minutes, so show "on pace" alongside the raw numbers.
- [ ] **D4. Is early tracking a good guide?** For past seasons' top 10s (the breakout board, 08), compare how each player looked at the same point of the season with whether he finally broke out. This says how much to read into November.
- [ ] **D5. Show it and re-check it.** A chart of the 10 against their thresholds; update at the All-Star break and score it at season's end, when the 2026-27 board (08) can be marked.

### Phase E — Does changing your game pay off?

**The question:** Mikal Bridges moved from The Pest to Kerr's Cult. How did his career change afterwards? More generally, do moves between the eight kinds help a player break out, win Most Improved, or simply last longer in the league?

- [ ] **E1. Define a move.** A player's kind in each season (notebook 13D, 2011-26). Clusters overlap, so a one-season flicker near a boundary is not a move. Options: the new kind must hold for two seasons; or the membership share must cross a clear margin (soft membership already gives a share in every kind). The 2000-26 windows (13E) are less stable (0.45), so use them only as a check.
- [ ] **E2. Mikal Bridges first,** as the worked example: his seasons, kinds and membership shares; what changed in his game (style measures, role, usage, team); and what followed (production, efficiency, minutes, contract, awards).
- [ ] **E3. Map every move.** Which moves happen, how often, at what age and career stage, and whether they come with a trade, a new coach or a bigger role.
- [ ] **E4. Outcomes.** For each kind of move, compared with similar players who did not move (same kind, age and level, from Phase C's comparisons):
  - breakouts in the following seasons (05 labels);
  - Most Improved votes and wins;
  - career length: seasons still played and minutes kept. Active players' careers are not finished, so this needs survival analysis (careers still running count as "at least this long"), not simple averages.
- [ ] **E5. Cause or sign?** A move can cause improvement, or simply be what improvement looks like (a player given the ball creates more). The comparison group in E4, and checking whether the move *precedes* the gain, separate the two as far as the data allows. Say plainly where it cannot.
- [ ] **E6. Rookie profiles and growth paths ("the Jack McVeigh rule"; added 12 November).** The rookie-centred half of this phase: each rookie's starting profile (style, body, production, role), the paths players with that profile actually took (which kinds they moved into; how often each path led to a breakout, a star season, a long or short career), the **windows** when each kind of growth tends to happen or stop, and **drift**: how far a player has moved from the usual path for his starting profile. Builds on notebook 03 (normal development), Phase C and E1–E5. A single worked example first.
- [ ] **E7. Record** the decisions and update the README.

### Phase F — Value or reputation? ("the Jaylen Brown rule"; added 12 November)

**The question:** is a player actually good, or good to a casual fan? Two numbers for every player-season, and the gap between them.

- [ ] **F1. Value:** our own measure of how much a player helps his team win, which can be added to a box score as one number. Start with a box-score regression (as BPM is built): weight every box-score statistic by how well it explains the team's point margin with the player on the court. Plus-minus adjusted for teammates and opponents (RAPM-style) only later, if it clearly helps: it needs play-by-play or lineup data and is noisy for one season. Compare with our star score (notebook 05).
- [ ] **F2. Reputation:** what a casual fan sees: points per game, All-Star selections, perhaps award votes.
- [ ] **F3. Does it work?** The value measure must predict next season's team results and on-court margin better than points per game, tested strictly on later seasons.
- [ ] **F4. The gap:** who is better than his reputation, and who is worse; how the gap changes over a career.
- [ ] **F5. Use it:** as an input to the breakout and Most Improved models (the natural end point of Phase B), and record the decisions.

### Phase G — A live site (added 12 November)

- [ ] **G1. GitHub Pages** (chosen over reviving the Streamlit app): a static site at `dan-j-e.github.io/unicorn-hunting` with the live Most Improved race (today's board, the daily chart, each stage's view), the breakout board and the eight kinds of player.
- [ ] **G2. Rebuilt by GitHub Actions** after each race update, once the tests (T1–T3) are in place, so every rebuild is checked first.
- [ ] **G3. Publish derived rankings and charts only,** never NBA.com's raw data.

## Scheduled
- **Weekly: a betting-market snapshot** (D45). Add the top names' prices to `benchmarks/mip_markets_2026_27.csv` from the public pages (date seen, source, price, the page's link). Never used as a model input.
- **End of 2026-27: score the season.** Our dated chances against the market snapshots (same scoring for both), the preseason top 7, and the breakout predictions (Phase D). Then open the model for changes again (D44).
- **All-Star break (February):** run `./scripts/update_mip_race.sh` (it freezes the live race's turning point, D32), then re-run notebook 3: case 3A prints Alexander-Walker's final blip-test verdict (set in advance, D33). Then update the README.
- **Whenever you like:** `./scripts/update_mip_race.sh` updates the live race. Its README lines and notebook findings are updated by hand.

## Later
- **The shrinkage prior can be unidentified** (found 13 November, notebook 0G): for bigs' three-point shooting in 2014-15 the likelihood keeps rising as the prior grows stronger, so the fitted strength (28 million attempts, then 45 million in a new environment) is arbitrary. Results are unaffected (those players are shrunk fully to the group average either way), but a cap on prior strength would make the build exactly reproducible. A methodological change, so to decide.
- **Speed: parallel backtests and parquet caches** (added 12 November; not needed yet). Notebook 21 takes about 30 minutes, almost all of it model fitting: thresholds are chosen inside every training set, so a tuned variant is about 500 fits. Options, by payoff: (1) run the season loops in parallel with joblib (roughly 4–6× faster, identical results); (2) cache the historical game tables (2000-26, both baseline versions) as parquet in `data/processed` (about 2 minutes saved per Most Improved notebook; the live season always loads fresh); (3) save expensive results and reload them unless asked to recompute (only with a clear recompute switch, as notebook 12's daily file does). Parquet rather than pickle: pickle can run code when loaded and breaks across pandas versions.
- **Sentiment trial** (moved here 10 November). Does public attention explain voters beyond the box score, such as Harden's 7th in 2012-13? Options: Google Trends first (history back to 2004, free, but unofficial and measures fans rather than voters); news headlines (GDELT); writers' Most Improved ladders; Reddit or X going forward only. Each source must show what people said at that date, or it leaks the result.
- **Scouting cards:** the three or four reasons behind each pick, with the closest comparisons from Phase C.
- **Basketball-Reference / CraftedNBA metrics** (VORP, BPM, WS): as extra breakout inputs, or as a check on star labels.
- **Early playoff experience** as a predictor of development, unicorns or breakouts.
- **2000-26 clusters with an era adjustment**, to separate "the role changed" from "the league changed". Partly covered by C3.
- **Route to stardom on the breakout board:** a label on each pick, or a separate view per route.
- **"Becomes a unicorn" label:** from future rarity scores, or a hand-checked list.
- **Do Pests take more charges?** A check on The Pest's description using hustle stats from 2015-16.

## Done
- **Audit 3, a sweep of every notebook:** claims made more honest (in-sample settings, strict results first, best-of-many models); notebook 12 split so the daily update takes about 20 seconds (backtests now in notebook 22); complete nights only; one day convention (13 November; [docs/AUDIT.md](docs/AUDIT.md); pull request #9).
- **Audit 2 and the freeze:** "a star left" stays on points (D43); overfitting check; live model frozen for 2026-27 (D44); markets as a benchmark (D45) (12 November; pull request #8).
- **Beyond points per game, first rules:** the live race's turning point on game score (D41) and "already clearly a star" (D42); notebook 21 (12 November; pull request #7).
- **Every stage of the predictor on the 2026-27 race** (12 November; notebook 19B; pull request #6).
- **Audit (Phase A):** every notebook relevant, opening with In brief and closing with dated findings; glossary and reading path in the README; numbers checked against outputs; shared scoring and live-race code (10 November; [docs/AUDIT.md](docs/AUDIT.md); pull request #5).
- **Already an All-Star counts against a Most Improved candidate** (9 November; notebook 17, D38; pull request #1).
- **The Ty Jerome effect:** lookalikes since 2000-01, and "back from a lost season" added to both models (10 November; notebooks 18–19, D39; pull requests #2–#3). Age × early jump, "head start" and games share were tested and rejected.
- **Calibration:** the chances are honest on the whole; big early favourites are flagged rather than corrected (10 November; notebook 20, D40; pull request #4).
- **Eight kinds of player** found and named (notebook 13, D34–D37), with the 2000-26 history.

## Parked
- **Blogging and story-led write-ups:** not for now.
- **Streamlit dashboard:** archived on 10 November (kept locally in `archive/dashboard/`, not in the repository). The live site is now Phase G, on GitHub Pages; the Streamlit app stays parked as a possible add-on for exploring.

## Decided against
- **Betting markets as a factor:** not used in the model. They are a benchmark only (D45).
