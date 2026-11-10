# To do

**Goal for this phase:** make the project clear, educational and honest about its metrics, then build "similar players at the same stage of their career". The analytical decisions are made deliberately, one step at a time.

## Current plan

Work through the three phases in order. Tick each box when it is done, and record any decision in [docs/DECISIONS.md](docs/DECISIONS.md).

### Phase A — Audit what we have

The aim: every notebook, chart and section is **relevant**, **easy to understand** and **educational** for a reader who did not build it.

- [x] **A1. Relevance** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). List every notebook (00–20), figure and README section. For each, decide: keep as is, update, merge, or move to `archive/`. Flag anything superseded by a later decision (for example, notebook 10's model before D27, D38 and D39).
- [x] **A2. Easy to understand** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). Every notebook opens with the question, a plain summary of the answer, and its decisions; and closes with findings. Use the same terms everywhere ("strict", "leave-one-out", "× a blind guess", "baseline season"), with a glossary in the README.
- [x] **A3. Educational** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). Every method choice is explained in words, with a link to its decision; a "how to read this project" path in the README (which notebooks to read, in what order, and why).
- [x] **A4. Accuracy** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). Every number in the README and in each notebook's findings matches that notebook's latest output. Findings carry the date they were written.
- [x] **A5. Code** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). Shared logic lives in `src/unicorn/`, not copied between notebooks (for example, the live-race candidate builder appears in notebooks 12, 17, 18 and 19). Consistent names.
- [x] **A6. Record** (done 10 November; see [docs/AUDIT.md](docs/AUDIT.md)). Write the audit results down (what changed and why), and update the README.

### Phase B — Points per game is the illustration, not the model

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

- [ ] **B1. Inventory.** Confirm and extend the table above for every model and rule, and add it to the README.
- [ ] **B2. Test all-round versions of the PPG-defined rules.** For each rule above, test the same idea on an all-round measure (game score, or a combination of production measures) and keep whichever does better in the strict test:
  - the turning point on last season's game score;
  - "a star left", measured by usage or game score rather than points;
  - the blip test and leaps on game score;
  - lookalikes on an all-round jump.
- [ ] **B3. Test more metrics in the Most Improved models.** Usage, shot profile and the other style measures from notebook 13, and box-score defence. Note: some only exist from 2011-12, which shortens the test.
- [ ] **B4. Say it plainly.** A README section and a line in chart captions: "PPG is shown for readability; the model uses these inputs: …". Each model lists its inputs in plain words.
- [ ] **B5. Record** the results as decisions.

### Phase C — Similar players at the same career stage

**The question:** for each 2026-27 candidate at a given point in time, which past players looked most like him at the same stage of their careers? How did *their* season finish, and how did their careers turn out?

- [ ] **C1. Define the stage and the point in time.** Options: same NBA season number (second season, third…), same age, or both; at a given day of the season (as in the live race) or at season's end.
- [ ] **C2. Choose the measures.** All metrics, not PPG alone: production (box-score rates), style (notebook 13's 15 measures), role (minutes, usage, starts) and efficiency.
- [ ] **C3. Adjust for era.** Use notebook 13's findings (confirmed 10 November: notebook 13 only): compare each measure with its own season's league (13D), and use the 2000-26 history (13E) to see how roles shifted.
- [ ] **C4. Method.** Nearest neighbours for each candidate, and clusters of similar players at each stage.
- [ ] **C5. Outcomes.** For each group of lookalikes: how the rest of that season went (jump kept, Most Improved votes) and how the career went (next one to three seasons, star and breakout labels, peak, moves between the eight kinds).
- [ ] **C6. Apply it** to the 2026-27 candidates, and show it in the live race.
- [ ] **C7. Record** the decisions and update the README.

## Scheduled
- **All-Star break (February):** re-run notebook 12. It prints Alexander-Walker's blip test verdict (set in advance, D33) and freezes the live race's turning point (D32). Then update the README.
- **Whenever you like:** `./scripts/update_mip_race.sh` updates the live race. Its README lines and notebook findings are updated by hand.

## Later
- **Sentiment trial** (moved here 10 November). Does public attention explain voters beyond the box score, such as Harden's 7th in 2012-13? Options: Google Trends first (history back to 2004, free, but unofficial and measures fans rather than voters); news headlines (GDELT); writers' Most Improved ladders; Reddit or X going forward only. Each source must show what people said at that date, or it leaks the result.
- **Tests and automatic checks:** leakage tests and GitHub Actions, so every pull request shows a green tick.
- **Movement between the eight kinds:** how players move between clusters as they develop, and which moves lead to stardom. Partly covered by C5.
- **Scouting cards:** the three or four reasons behind each pick, with the closest comparisons from Phase C.
- **Basketball-Reference / CraftedNBA metrics** (VORP, BPM, WS): as extra breakout inputs, or as a check on star labels.
- **Early playoff experience** as a predictor of development, unicorns or breakouts.
- **2000-26 clusters with an era adjustment**, to separate "the role changed" from "the league changed". Partly covered by C3.
- **Route to stardom on the breakout board:** a label on each pick, or a separate view per route.
- **"Becomes a unicorn" label:** from future rarity scores, or a hand-checked list.
- **Do Pests take more charges?** A check on The Pest's description using hustle stats from 2015-16.

## Done
- **Audit (Phase A):** every notebook relevant, opening with In brief and closing with dated findings; glossary and reading path in the README; numbers checked against outputs; shared scoring and live-race code (10 November; [docs/AUDIT.md](docs/AUDIT.md); pull request #5).
- **Already an All-Star counts against a Most Improved candidate** (9 November; notebook 17, D38; pull request #1).
- **The Ty Jerome effect:** lookalikes since 2000-01, and "back from a lost season" added to both models (10 November; notebooks 18–19, D39; pull requests #2–#3). Age × early jump, "head start" and games share were tested and rejected.
- **Calibration:** the chances are honest on the whole; big early favourites are flagged rather than corrected (10 November; notebook 20, D40; pull request #4).
- **Eight kinds of player** found and named (notebook 13, D34–D37), with the 2000-26 history.

## Parked
- **Blogging and story-led write-ups:** not for now.
- **Streamlit dashboard:** archived on 10 November (kept locally in `archive/dashboard/`, not in the repository). To revisit some time.

## Decided against
- **Betting markets as a factor:** not used in the model.
