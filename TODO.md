# To do

Goal for this phase: make the Most Improved model fit how voters really behave, then finish the player archetypes. The analytical decisions are made deliberately, one step at a time.

**How to read the ranks** (1 = first or best):
- **Priority:** the order to do it in, allowing for what depends on what and what's time-sensitive while the 2026-27 race is live.
- **Usefulness:** how much it should improve the project if it works, ignoring effort.

| Item | Priority | Usefulness | Effort |
|---|---|---|---|
| ~~[Already-established flag](#1-already-established-flag)~~ **done (D38)** | 1 | 1 | Small |
| ~~[Hot-start and age test](#2-hot-start-and-age-test-the-ty-jerome-effect)~~ **done (D39)** | 2 | 3 | Small |
| [Early-season calibration](#3-early-season-calibration) | 3 | 2 | Small |
| [Sentiment trial](#4-sentiment-trial) | 4 | 4 (uncertain) | Medium |
| [Similar players](#5-similar-players-at-the-same-career-stage) | 5 | 5 | Medium |
| [Movement between the eight kinds](#6-movement-between-the-eight-kinds) | 6 | 6 | Medium |
| [Scouting cards](#7-scouting-cards) | 7 | 7 | Medium |
| [Basketball-Reference / CraftedNBA metrics](#8-basketball-reference--craftednba-metrics) | 8 | 8 | Medium |
| [Early playoff experience](#9-early-playoff-experience) | 9 | 9 | Medium |
| [2000-26 clusters with an era adjustment](#10-2000-26-clusters-with-an-era-adjustment) | 10 | 10 | Small |
| [Route to stardom on the breakout board](#11-route-to-stardom-on-the-breakout-board) | 11 | 11 | Small |
| ["Becomes a unicorn" label](#12-becomes-a-unicorn-label) | 12 | 12 | Medium |
| [Do Pests take more charges?](#13-do-pests-take-more-charges) | 13 | 13 | Small |

## The 2026-27 Most Improved model

### 1. Already-established flag · *done 9 November: notebook 17, decision D38*
**What:** count having already been recognised as a star against a player.
**Why:** 0 of 26 winners had been an All-Star before their winning season, and only 5 of the 105 who finished 2nd–5th. The scoring turning point misses this: Alperen Sengun (20.4 last season, two All-Star selections) is #2 on the 2 November board. Still needed: the share of all candidates who were prior All-Stars.
**Won't catch:** Cooper Flagg or James Harden in 2012-13 (7th in the vote), who had no prior selection.

**Options:**
- **A. Any prior All-Star selection, yes/no.** *Recommended start:* simple, with the clearest evidence.
- B. Number or recency of selections. It might separate long-ago All-Stars from recent ones, but there are few cases.
- C. Broader "established" measure: adds All-NBA and major awards. Adds little so far (All-NBA: 0 winners, 2 of 105).
- D. Hard exclusion. Not recommended: the same approach was replaced by the turning point (D27).

**Rule:** only selections from before that season count. Many winners first make the team in the year they win, so using that season's selection would leak the answer.

### 2. Hot-start and age test (the Ty Jerome effect) · *done 11 November: notebooks 18 and 19, decision D39. Only 'back from a lost season' helped; age × jump, head start and games share were rejected*
**What:** test whether the model should believe a hot start less, especially from an older player.
**Why:** of 51 players up 10+ points at this stage, the typical one kept 65% of the jump by season's end, and 2 won. Of the 18 aged 27+, the typical one kept 52%; only 2 got any votes and none finished in the top 3. Ty Jerome is 29.

**Options (test separately; they can be combined):**
- **A. Age × early jump interaction.** *Recommended start.*
- B. Shrink early jumps towards the baseline, depending on games played.
- C. Stale-baseline flag. Jerome's baseline is 2024-25, two seasons old.
- D. Availability: games missed so far. Also confirm whether the 65-game rule covers MIP.

### 3. Early-season calibration
**What:** make the displayed chances honest. This changes the percentages, not the order.
**Why:** day-14 leaders averaged a 19% chance, but only 3 of 26 won (12%). The two at 25% or more (Eric Bledsoe, Cam Thomas) both lost. Jerome's 39% is too high.
**When:** after items 1 and 2, because it has to be fitted to the final model.

**Options:**
- **A. A scaling factor for each day of the season, learned from past seasons.** *Recommended:* simple, with little to overfit.
- B. A stronger penalty (λ) early in the season. Note this would revisit D30, which confirmed λ = 3.
- C. Show ranks only until a set date, such as day 30. Simplest, but hides the size of a lead.

### 4. Sentiment trial
**What:** test whether public attention explains voters beyond the box score, such as Harden's 7th in 2012-13.
**Test:** does a jump in attention improve the model once the box-score numbers are in? If not, drop it.
**Rule:** each source must show what people were saying at that date, or it leaks the result.

**Options:**
- **A. Google Trends.** *Recommended first:* history back to 2004, free. But access is unofficial, and it measures fans rather than voters.
- B. News headlines (GDELT): about a decade of history. Noisy, and tone is hard to read.
- C. Writers' MIP ladders: closest to voters, but patchy and hard to collect.
- D. Reddit or X: poor access to old posts, so usable going forward only.

## Player archetypes

Done so far in notebook 13: eight clusters chosen and named (13D, D35, D37), plus the 2000-26 history (13E, D36). Write-up: [docs/EIGHT_CLUSTERS.md](docs/EIGHT_CLUSTERS.md).

### 5. Similar players at the same career stage
**What:** for any current player, find the most similar historical players at the same stage (e.g. Egor Dëmin's rookie year against past rookie years).

**Options:**
- **A. Nearest neighbours on the 15 style measures, same career year.** *Recommended start.*
- B. Style plus quality (points, efficiency), so comparisons are also about how good a player is.
- C. Three-season windows (13E) instead of single seasons: steadier, but unavailable for young players.

### 6. Movement between the eight kinds
**What:** how players move between clusters as they develop, and which moves lead to stardom.

**Options:**
- **A. Table of moves from one cluster to another, by age.** *Recommended start.*
- B. Link moves to the star and breakout labels.
- C. Feed moves into the breakout and MIP models as inputs, if B finds a signal.

### 7. Scouting cards
**What:** for each candidate, the 3–4 reasons pushing his chances up or down, his cluster, closest comparisons, and what he'd need to do next. Needs item 5.

**Options:**
- **A. Coefficient × value** for the logistic and MIP models. *Recommended:* direct and easy to explain.
- B. SHAP-style contributions, for the tree models.

## Later

### 8. Basketball-Reference / CraftedNBA metrics
Add VORP, BPM, WS and similar. **Options:** a few all-in-one metrics as extra breakout inputs, or as a check on star labels only.

### 9. Early playoff experience
Does it predict development, unicorns or breakouts? **Options:** a simple yes/no for playoff minutes by a given age, or the size of the player's playoff role.

### 10. 2000-26 clusters with an era adjustment
Separates "the role changed" from "the league changed". **Options:** compare within each window's seasons, or against a rolling multi-season average.

### 11. Route to stardom on the breakout board
**Options:** a label on each pick (breakout or steady climb), or a separate view for each route.

### 12. "Becomes a unicorn" label
**Options:** define it from future rarity scores, or from a hand-checked list of players.

### 13. Do Pests take more charges?
A check on The Pest's description, using NBA.com hustle stats from 2015-16. **Options:** The Pest against all other clusters, or against other wings only. Not a clustering input.

## Scheduled
- **All-Star break (February):** re-run notebook 12. It prints Alexander-Walker's blip test verdict (set in advance, D33) and freezes the live race's turning point (D32). Then update the README.
- **Whenever you like:** `./scripts/update_mip_race.sh` updates the live race. Its README lines and notebook findings are updated by hand.

## Parked
- **Blogging and story-led write-ups:** not for now. This includes the "Could we have seen Shai coming?" piece.
- **Streamlit dashboard** (`dashboard/app.py`): works, but not a focus.

## Decided against
- **Betting markets as a factor:** not used in the model.
