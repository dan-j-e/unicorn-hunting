# NBA Unicorn & Breakout Hunting

![Python 3.12](https://img.shields.io/badge/python-3.12-2a78d6)
![Data: NBA.com and Basketball-Reference](https://img.shields.io/badge/data-NBA.com%20%7C%20Basketball--Reference-1baf7a)
![Method: walk-forward backtesting](https://img.shields.io/badge/method-walk--forward%20backtesting-eb6834)
![Decisions logged: 48](https://img.shields.io/badge/decisions%20logged-48-eda100)

**Could we have identified future NBA breakouts, stars and "unicorns" before they became obvious, using only what was known at the time?**

This project treats scouting like backtesting an investment strategy. For every past season, it rebuilds what was knowable at that moment, ranks the players, and then scores those rankings against what actually happened. Only after a method has passed that test is it applied to current players. The Most Improved Player and playing-style work goes back to 2000-01; the breakout and star work starts in 2011-12.

> [!NOTE]
> **Live: the 2026-27 Most Improved race.** Ty Jerome leads with a 12% chance on 11 November (day 22 after opening night), ahead of Davion Mitchell and Anthony Black. His chance was 26% until the model learned that players returning from a lost season have never won: [is his lead believable?](#is-ty-jeromes-lead-believable)

![The 2026-27 Most Improved race, day by day](outputs/figures/12_daily_worm.png)

## At a glance

| Question | Short answer | Evidence |
|---|---|---|
| Are breakouts predictable a season ahead? | **Partly:** 4–6× better than random | Strict walk-forward backtest, 2014-15 → 2024-25 |
| What predicts a future star? | **Current all-round quality**, ahead of any model (10× random) | 26 future stars; two routes to stardom |
| What is a "unicorn"? | **Two kinds:** rare *combinations* of strengths (Giannis Antetokounmpo, Nikola Jokić) and *extremes* with no comparable players (Victor Wembanyama) | Rarity and strangeness scores |
| How many kinds of player are there? | **Eight** by playing style, from *Mr. Inside the Key* to *The Effective Operator* | Clustering of 5,353 player-seasons |
| Can the Most Improved Player be named from the box score? | **Often:** #1 at season's end in 7 of 21 seasons, top 3 in 11 (each season judged only from earlier ones) | 2000-01 → 2025-26 |
| What do Most Improved voters reward? | A large jump in scoring and production, a team that improves, a player who is young and **not already a star** | No winner in 26 years had been an All-Star |
| What is the best clue before the season? | **An open role:** a 20-point scorer has left the player's team | 7 of 21 winners, against 11% of candidates |
| Has the predictor improved as we learned? | **It roughly doubled in sharpness** on the seasons it was developed on: from 11× to 26× a blind guess at season's end, one tested decision at a time. 2026-27 is its first true test | [How the predictor evolved](#how-the-predictor-evolved) |

## Where things stand (13 November 2026)

- **The Most Improved model is frozen for 2026-27** ([D44](docs/DECISIONS.md)), so this season is its first genuinely out-of-sample test. Its past-season scores were measured on the seasons it was developed on, so they flatter it somewhat.
- **What holds up:** the core of the model (the baseline fix, what voters reward, the turning point, already an All-Star) improves on every resampling of the seasons ([Audit 2](docs/AUDIT.md)). The chances are honest except for big early favourites, which are flagged ([D40](docs/DECISIONS.md)).
- **What is fragile:** the latest small tweaks (D41, D42) are within noise, and the preseason model (16 inputs, 14 winners, 9 strict seasons) is the most at risk of fitting noise. Breakout lifts are the best of several models, so slightly optimistic.
- **The live race** is updated in about 20 seconds (`./scripts/update_mip_race.sh`); its backtests now live in [notebook 22](notebooks/archive/22_live_race_backtests.ipynb). Ty Jerome leads; betting markets are kept as a benchmark only ([D45](docs/DECISIONS.md)).
- **Being restructured (13 November, [D47](docs/DECISIONS.md)):** one notebook per segment: 0 Data, 1 the basic Most Improved race, 2 playing styles, 3 candidate investigations, 4 the revised race (with a separate live-race notebook). [0 Data](notebooks/0_data.ipynb), [1 The basic race](notebooks/1_mip_basic.ipynb) and [2 Playing styles](notebooks/2_play_styles.ipynb) [3 Investigations](notebooks/3_mip_investigations.ipynb) and [4 The revised race](notebooks/4_mip_race.ipynb) are done; the breakout, star and unicorn work is archived.
- **Next:** segments 1–4, then automated tests (T1–T3) and value against reputation (Phase F). The points-per-game phase closed on 13 November: points are now the illustration, and every chart that shows them says what the model uses instead. When the model reopens for 2027-28, one package tested once ([D46](docs/DECISIONS.md)): more metrics, one "established player" measure in place of five overlapping inputs, a turning point fixed before the season, and every setting chosen inside training. The latest sweep is [Audit 3](docs/AUDIT.md).

## Contents

- [Where things stand](#where-things-stand-13-november-2026) · [The project in one picture](#the-project-in-one-picture) · [How to read this project](#how-to-read-this-project)
- [Breakouts and stars](#breakouts-and-stars) · [Unicorns](#unicorns) · [Eight kinds of player](#eight-kinds-of-player)
- [Most Improved Player](#most-improved-player): [what voters reward](#what-voters-reward) · [before the season](#before-the-season) · [already an All-Star](#why-already-an-all-star-counts-against-a-player) · [how the predictor evolved](#how-the-predictor-evolved) · [beyond points per game](#beyond-points-per-game)
- [The live 2026-27 race](#the-live-2026-27-most-improved-race): [is Jerome's lead believable?](#is-ty-jeromes-lead-believable) · [are the chances honest?](#are-the-chances-honest) · [the blip test](#the-blip-test-did-alexander-walkers-leap-last)
- [How it works](#how-it-works) ([terms used throughout](#terms-used-throughout)) · [Key decisions](#key-decisions) · [Reproduce](#reproduce) · [Limitations](#limitations) · [What's next](#whats-next)

---

## The project in one picture

```mermaid
flowchart LR
    A["NBA.com<br/>box scores and game logs<br/>1998-99 → today"] --> B["Clean tables<br/>player-seasons, player-games"]
    B --> C["Inputs known<br/>at the time"]
    S["Basketball-Reference<br/>All-Star selections"] --> C
    C --> D["Models<br/>logistic, boosted trees,<br/>choice model, clusters"]
    D --> E["Walk-forward<br/>backtests"]
    V["Basketball-Reference<br/>award votes"] -. "scoring only,<br/>never training" .-> E
    E --> F["2026-27 predictions"]
    F --> G["Live race,<br/>one leaderboard per day"]
```

Every arrow runs forward in time. A prediction for a season uses only seasons, games and selections that came before it. Award votes are used only to mark predictions, never to train a model.

---

## How to read this project

The notebooks are numbered in the order the work was done, not the order a reader needs. Choose a route below. Every notebook opens with **In brief** (question, answer, decisions, where it fits), so reading just those blocks along a route gives the whole story; the [terms](#terms-used-throughout) are defined once, below.

**In ten minutes**
1. This page: [at a glance](#at-a-glance), then [the live race](#the-live-2026-27-most-improved-race).
2. [Notebook 19](notebooks/archive/19_predictor_evolution.ipynb): the Most Improved model rebuilt one decision at a time. The best single notebook for seeing how the project reasons.
3. [The eight kinds of player](docs/EIGHT_CLUSTERS.md).

**Route 1: Most Improved Player** (the main thread)

| Step | Notebook | Why read it |
|---|---|---|
| 1 | [1 Basic race](notebooks/1_mip_basic.ipynb) | How winners' seasons unfold, and the first model of what voters reward: where the reasoning starts |
| 2 | [3 Investigations](notebooks/3_mip_investigations.ipynb) | Four cases the live board raised, each tested: did Alexander-Walker's leap last, is Ty Jerome's lead believable, already a star, an open role |
| 3 | [4 The revised race](notebooks/4_mip_race.ipynb) | The current model at six checkpoints, how it got there one decision at a time, and whether its chances are honest |
| 4 | [4b The live race](notebooks/4b_live_race.ipynb) | The 2026-27 race, day by day |

The original notebooks (00–22) are in [notebooks/archive](notebooks/archive): every intermediate step, and the evidence the decision log cites.

**Route 2: Breakouts and stars** (archived on 13 November; [D47](docs/DECISIONS.md))

| Step | Notebook | Why read it |
|---|---|---|
| 1 | [0 Data](notebooks/0_data.ipynb) | The data: shrinkage, season-relative measures, and how each player has been changing |
| 2 | [05](notebooks/archive/05_breakout_hunting.ipynb) | What counts as a breakout and a star |
| 3 | [06](notebooks/archive/06_breakout_backtest.ipynb) | The backtest: which models work, honestly tested |
| 4 | [09](notebooks/archive/09_routes_to_stardom.ipynb) | Two routes to stardom |
| 5 | [08](notebooks/archive/08_breakout_board.ipynb), [07](notebooks/archive/07_current_players.ipynb) | Every past season's picks, then the 2026-27 outlook |

**Route 3: Playing styles:** [2 Playing styles](notebooks/2_play_styles.ipynb) (the eight kinds of player). The unicorn work (rare combinations and extremes) is archived in [04](notebooks/archive/04_unicorn_hunting.ipynb).

**The data:** [0 Data](notebooks/0_data.ipynb) shows which NBA.com sources can be trusted, and why some cannot, and builds every table the other notebooks read. The original data notebooks (00–03) are in the [archive](notebooks/archive).

---

## Breakouts and stars

Strict walk-forward backtest[^strict], predictions for 2014-15 → 2024-25, players aged 25 or under ([notebooks 05–09](#how-it-works)):

| Outcome | How rare | Best model | Lift over random (95% CI) |
|---|---|---|---|
| Any breakout next season | 6.9% | Boosted trees | **4.2×** (3.3–5.3) |
| Scoring breakout next season | 4.9% | Boosted trees | **6.1×** (4.9–8.0) |
| Star season within 3 years | 1.6% | Current star score | **10×** (6.7–23) |

"Best model" is the best of six to eight models compared on this same backtest. Picking the winner after the test flatters it a little, and the intervals don't allow for that choice, so read these lifts as slightly optimistic.

<details>
<summary><b>Findings, charts and Egor Dëmin</b></summary>

- **Simple is nearly as good as complex.** A 12-signal logistic regression reaches about 90% of the 197-feature model. The signals in favour are earning minutes already, rising usage and minutes, self-creation and efficiency. Those against are age, a late draft position and usage that is already high.
- **For stardom, current all-round quality beats every model.** With only about 26 future stars to learn from, extra features overfit.
- **There are two routes to stardom.** Some players break out (Shai Gilgeous-Alexander, Giannis Antetokounmpo, Nikola Jokić); others climb steadily without a single breakout season (Anthony Edwards, Devin Booker, Donovan Mitchell). Steady risers are visible early from current quality alone (8.6× random); breakout-route stars need trajectory signals (4.6–5.6×).
- **The models read trajectories, not single seasons.** Shai was ranked 37th of 229 young players after his rookie year, then 12th after his second.
- **Egor Dëmin after one season:** a typical 5.3% breakout chance for 2026-27. His rookie profile most resembles Kevin Huerter, Tyler Herro, Jamal Murray and Klay Thompson: shooters who broke out more often than average but rarely became stars.

| | |
|---|---|
| ![Backtest lift with confidence intervals](outputs/figures/06_backtest_lift_ci.png) | ![Shai Gilgeous-Alexander against LaMelo Ball](outputs/figures/03_sga_vs_lamelo.png) |
| Walk-forward lift over random, with bootstrap intervals | Shai Gilgeous-Alexander against LaMelo Ball, season by season |
| ![Dëmin comparisons](outputs/figures/07_demin_comps_trajectories.png) | ![Breakout board](outputs/figures/08_breakout_board.png) |
| Where players with a rookie season like Dëmin's went | Each season's top-10 breakout picks against what happened |

</details>

## Unicorns

Rare *combinations* of strengths (Giannis, Jokić, Kevin Durant) are distinct from *extremes* with no comparable players. Victor Wembanyama is the most extreme player in the data.

<details>
<summary><b>The unicorn map</b></summary>

![Unicorn map](outputs/figures/04_unicorn_map_2025_26.png)

2025-26: the rarity of each player's skill mix (pairs of strengths that seldom occur together) against his strangeness (distance to the most similar players).

</details>

## Eight kinds of player

**How do players play, rather than how well?** Every player-season since 2011-12 with 500+ minutes was grouped by 15 style measures: where he shoots, how he creates, how he rebounds and his box-score defence. Each measure is compared with that season's league.

> [!IMPORTANT]
> **The data drew the groups; we named them afterwards.** No names, size or position went into the clustering, and no list of expected types was written beforehand ([D31](docs/DECISIONS.md)). This stops the analysis from forcing players into categories we already believe in. Full write-up: [docs/EIGHT_CLUSTERS.md](docs/EIGHT_CLUSTERS.md).

| | Name | Best-known members | What the data says |
|---|---|---|---|
| 1 | **Mr. Inside the Key** | DeAndre Jordan, Rudy Gobert, Dwight Howard | Rim shots, offensive rebounds, blocks; no threes |
| 2 | **Windex** | Karl-Anthony Towns ('16-17), Amen Thompson, Domantas Sabonis | Rebounds at both ends, paint touches; few threes |
| 3 | **Bruiser** | Al Horford, Michael Porter Jr., Brook Lopez | Defensive rebounds, blocks, fouls; rarely creates his own shot |
| 4 | **The Pest** | Mikal Bridges ('21-22), Josh Hart, OG Anunoby | Fast breaks, corner threes, steals; low usage |
| 5 | **Give Me the Ball and Let Me Work** | James Harden, Kevin Durant, LeBron James | Self-created baskets, assists, usage; mid-range |
| 6 | **Peter Griffin's NBA Jam** | Trevor Ariza, P.J. Tucker, Toumani Camara | The most threes of any group; almost no self-creation, rim shots or free throws |
| 7 | **Kerr's Cult** | Klay Thompson, Nicolas Batum, Mikal Bridges ('24-25) | Threes and movement; few rim shots or rebounds |
| 8 | **The Effective Operator** | Damian Lillard, Stephen Curry, CJ McCollum | Self-created baskets, assists, usage; smaller, fewest rebounds |

![Eight kinds of player: who is in which](outputs/figures/2_eight_kinds_who.png)

- **Players move between kinds as their game changes.** Mikal Bridges moved from The Pest to Kerr's Cult; Karl-Anthony Towns began as a Windex before he became a shooting big.
- **2025-26 surprises:** Wembanyama is a Windex rather than a Bruiser, because his rim shots and rebounding outweigh his threes relative to the league. Draymond Green is in Kerr's Cult.

<details>
<summary><b>How many groups, and why eight</b></summary>

Playing style turned out to be mostly a continuum rather than a set of islands. To judge how many groups are real, the clustering was fitted on two random halves of the data and the two results compared (1 = identical groups).

| Groups | 3 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|
| Agreement between halves (2011-26; average of 20 pairs of halves) | 0.94 | 0.83 | 0.79 | 0.59 | 0.54 |

Three groups are rock-solid; five and six are about equally stable; beyond six the groups depend on which seasons are in the sample. *Revised 13 November:* this table said five 0.87 and six 0.76, from only six pairs of halves, which made five look like a clear peak. Eight were chosen ([D35](docs/DECISIONS.md)) because the eight fit neatly inside the five and each extra split has a clear basketball reading: stretch bigs, corner 3-and-D wings, and two different kinds of on-ball creator.

</details>

<details>
<summary><b>Back to 2000-01: how the league changed</b></summary>

The same exercise over 26 seasons, on 3-season rolling windows and with **no era adjustment**, so the league's changes show up directly ([notebook 2](notebooks/2_play_styles.ipynb), section 2D; [D36](docs/DECISIONS.md)):

- **The traditional rim big fell from 23% of players to 5%.** It was the largest group until about 2012, then collapsed by 2018.
- **The corner 3-and-D wing rose from 4% to 20%.** Bruce Bowen, Raja Bell and Shane Battier came first; Trevor Ariza and P.J. Tucker followed.
- **Usage-heavy and pick-and-pop bigs held steady at 6–9%,** from Kevin Garnett, Tim Duncan and Dirk Nowitzki to Jokić, Giannis and Towns.

![The mix over time](outputs/figures/2_mix_2000_2026.png)

These longer-run groups are less stable (0.45 agreement at eight), partly because players near a boundary switch groups as the league shifts around them.

</details>

## Most Improved Player

**Could each Most Improved Player (MIP) have been named from the numbers, and what do the votes say "improved" means?** ([notebook 1](notebooks/1_mip_basic.ipynb); every intermediate step in the archived [notebook 10](notebooks/archive/10_mip_leaps.ipynb))

The model is a **choice model** (conditional logit): in each season exactly one eligible player wins, so every player's score is turned into a share of a single 100% chance:

$$
P(\text{player } i \text{ wins season } s) \;=\; \frac{\exp\!\left(x_i^{\top}\beta\right)}{\sum_{j \,\in\, \text{eligible}(s)} \exp\!\left(x_j^{\top}\beta\right)}
$$

where $x_i$ holds the player's inputs (changes in his box-score numbers, his team's change in winning, his age and so on). The penalty on the weights is λ = 3 ([D30](docs/DECISIONS.md)).

| Test | Result |
|---|---|
| Winner ranked #1 from about 300 eligible players, each season predicted from the others (2011-12 → 2025-26) | **8 of 15 seasons** (median winner rank 1) |
| The same model trained on earlier seasons only | 5 of 10 seasons |
| Strictly earlier seasons only, game logs only, 2005-06 → 2025-26 ([notebook 15](notebooks/archive/15_mip_2000_2026.ipynb)) | #1 in **7 of 21**, top 3 in 11; median winner rank 2 |
| Our top 7 against the real voting top 7 | 3.1 of 7 in common, on average |

<details>
<summary><b>Approach</b></summary>

- **Data:** 404,000 player-games (2010-11 → 2025-26), with Hollinger game score[^gamescore] as the one-number summary of a game; game logs back to 1998-99 for the longer history.
- **Baseline:** each player's own previous season, skipping injury-shortened ones, so a healthy return is not counted as a leap.
- **Inputs:** the change in every box-score statistic, both absolute (ΔX) and relative (Δ%), plus the team's change in winning percentage, age and a second-year flag.
- **Evaluation:** real vote totals ([Basketball-Reference](https://www.basketball-reference.com/awards/)) are used only to mark predictions, never to train.

</details>

### What voters reward

- **Size beats percentage.** The absolute jump alone names the winner in 7 seasons; the relative jump alone in 4.
- **Voters reward** a jump in all-round production (odds ×1.57 per extra point of game score), in scoring (×1.39 per extra point a game), a larger offensive load, and a team that improved (×1.28 for winning 10% more games).
- **Voters discount** age (×0.88 per year), gains that come only from extra minutes, and above all second-year players: 19% of the voting top 7, but no winner in the last 15 seasons (the last was Monta Ellis in 2006-07).
- **Voters pass over players who are already stars.** No winner from 2000-01 to 2025-26 had been an All-Star before his winning season ([see below](#why-already-an-all-star-counts-against-a-player)).
- **Most winning leaps are visible early.** For 9 of 15 winners, the first 10 games already held 80% or more of the season's jump, and two more were just short (78–79%). *Corrected 13 November: this said 11 of 15, counting those two.* One huge night is not a signal: after 1,089 "eruption" games, the next seven looked like the seven before.
- **The winners the model misses crossed a milestone** rather than making the largest jump: a first 20-point season (Goran Dragić), a first star-level season (Julius Randle), or becoming the team's leading scorer (Tyrese Maxey, Paul George).

<details>
<summary><b>Charts: weights, every winner's season, and our top 7 against the real vote</b></summary>

| | |
|---|---|
| ![What voters reward](outputs/figures/1_what_voters_reward.png) | ![Winners week by week](outputs/figures/1_winners_week_by_week.png) |
| Every model weight, with 90% ranges from 500 refits | Each winner's season, week by week, against his baseline |

![Top 7 against the real vote](outputs/figures/1_top7_vs_real_vote.png)

*Our top 7 against the real voting top 7, each season predicted from the other seasons only.*

![Three views of every season, 2005-06 to 2025-26](outputs/figures/15_mip_2000_2026.png)

*Three views of every season since 2005-06, each predicted from earlier seasons only: the end of the previous season (median winner rank 51), mid-season (4) and the end of the season (2). This is the model of 30 October, before D38–D42; notebook 19 has the current mid-season and end-of-season numbers.*

</details>

### Before the season

**Who is set up to improve before a game has been played?** ([notebook 11](notebooks/archive/11_mip_preseason.ipynb))

- **Preseason form is used per 36 minutes, never as totals**, and small samples are shrunk towards zero:

  $$\text{weight of a preseason change} \;=\; \frac{\text{preseason minutes}}{\text{preseason minutes} + 150}$$

  so 50 preseason minutes count for a quarter and 150 for a half. Minute increases in preseason hold at about 60–75%, decreases mean almost nothing, and shot volume per minute is the most reliable signal.
- **Established scorers are handled by a turning point, not a rule** ([D27](docs/DECISIONS.md)). Last season's scoring counts slightly in a player's favour up to 20 points a game and against him above it, because a 25-point scorer is an MVP candidate, not an MIP one:

  $$\beta_1 \cdot \text{ppg} \;+\; \beta_2 \cdot \max(0,\ \text{ppg} - 20)$$

  Every turning point from 14 to 26 was backtested; 20 fitted best.
- **A star leaving matters more than changing teams** ([notebook 3, case 3D](notebooks/3_mip_investigations.ipynb); detail in the archived [notebook 14](notebooks/archive/14_team_changes.ipynb); [D29](docs/DECISIONS.md)). Winners changed teams no more often than anyone else (29% against 27%), but 7 of 21 had a 20-point scorer leave their team (against 11% of candidates). A yes/no input, "a 20-point scorer left and was not replaced", lifted the winner into our preseason top 7 in 7 of 14 seasons, up from 3. Finer scoring bands fitted better on paper, but they learned a shape with no basketball sense (losing a 21-point scorer "hurt", losing a 23-point scorer helped), so the simple version was kept.
- **Track record:** from about 375 candidates a season, the eventual winner was in our preseason top 7 in **5 of 9 seasons in the strict test** (median rank 7), and in 9 of 14 in the kinder leave-one-out test. 44% of top-7 picks went on to jump 3+ points a game, against 14% of all candidates.
- **The model most at risk of fitting noise:** 16 inputs learned from 14 winners, with only 9 seasons in the strict test. Each input was kept only if it helped, but one season can decide whether it did.

| | |
|---|---|
| ![Team changes against winners](outputs/figures/14_team_changes.png) | ![2026-27 preseason top 7](outputs/figures/11_mip_preseason_top7.png) |
| A star leaving, not a change of team, marks the winners | 2026-27 preseason top 7: six of the seven play for a team that lost a 20-point scorer |

**2026-27 preseason top 7:** Rui Hachimura, Brandon Miller, Cooper Flagg, Tristan da Silva, Sandro Mamukelashvili, Zaccharie Risacher and Naz Reid. Places 4 to 12 are separated by less than half a percentage point, so their order is close to a tie.

### Why "already an All-Star" counts against a player

**The problem.** In early November the live leaderboard had Alperen Sengun at #2, with Victor Wembanyama and Scottie Barnes in the top 7. All three had already been All-Stars. The scoring turning point only applies above 20 points a game, and these players sat around or below that line.

**The evidence** ([notebook 3, case 3C](notebooks/3_mip_investigations.ipynb); detail in the archived [notebook 17](notebooks/archive/17_already_a_star.ipynb)):

| | Prior All-Stars | Everyone else |
|---|---|---|
| Share of candidates | about 1 in 6 | about 5 in 6 |
| Most Improved winners, 2000-01 → 2025-26 | **0 of 26** | 26 of 26 |
| Wins the model expected *without* this input | about 2 | about 24 |

If the model without this input were right, zero wins from prior All-Stars would happen about 1 time in 10. That is suggestive rather than proof, so the input was kept only because it also improved every backtest:

| Test | Without | With |
|---|---|---|
| Preseason, strict: winner's median rank | 15 | **7** |
| Preseason, strict: winner in our top 7 | 4 of 9 | **5 of 9** |
| Live race at day 85: winner in our top 7 | 11 of 15 | **12 of 15** |
| 2000-26 history, mid-season: winner in our top 7 | 16 of 21 | **17 of 21** |

**The decision** ([D38](docs/DECISIONS.md)):
- **A penalty, not a ban.** A prior All-Star has about **a quarter of the odds** of an otherwise identical player, so a large enough jump can still rank highly. This matches the "no exclusions" approach of the turning point.
- **Only selections from before the season count.** Many winners are first selected in the year they win (Paul George, Jimmy Butler, Giannis), so using the current season's selection would leak the answer.
- **The record comes from NBA.com, looked up by player ID.** Basketball-Reference's All-Star pages provide the list of names to check, and the ID keeps same-name pairs, such as Tim Hardaway and Tim Hardaway Jr., apart.
- **Kept deliberately simple.** A count of selections, or a broader "established" measure that adds All-NBA and other awards, added nothing: no winner had been All-NBA either. More variations would mostly fit noise in 26 awards.

**What it does not explain:** James Harden finishing only 7th in 2012-13, or the discount on Cooper Flagg. Neither had a prior selection, so their cases rest on reputation from elsewhere, which is the purpose of the planned sentiment trial.

![Already a star](outputs/figures/17_already_a_star.png)

### How the predictor evolved

The current model was not designed in one step. It was built through a series of tested decisions, each made because something was wrong or missing. [Notebook 19](notebooks/archive/19_predictor_evolution.ipynb) rebuilds the predictor one decision at a time and scores every stage on the same test: every season from 2000-01 to 2025-26, each predicted only from earlier seasons.

> [!NOTE]
> **These are the seasons the model was developed on.** Each season is predicted from earlier seasons only, but the settings were not chosen that way: the penalty (λ = 3), the turning points and the elite threshold were picked by looking across all of these seasons, and each later stage was added after seeing how it did on them. So the later stages' gains are somewhat optimistic. The large early gains (stages 1–4) hold up when the seasons are resampled ([Audit 2](docs/AUDIT.md)); the small late ones may not. The first genuinely out-of-sample test is 2026-27, with the model frozen ([D44](docs/DECISIONS.md)).

![How the predictor evolved](outputs/figures/19_predictor_evolution.png)

| Stage | Decision | Why it was made | Season's end: winner in top 7 · × blind | Day 19: median winner rank · × blind |
|---|---|---|---|---|
| 0. Biggest points jump | starting point | The obvious first idea, with no model | 11 of 21 · – | 11 · – |
| 1. Choice model on box-score changes | D24 | One winner per season; every statistic weighted by what voters rewarded | 13 · 11.4× | 17 · 3.6× |
| 2. Skip injury-shortened baselines | D22 | Comebacks such as Kawhi Leonard's looked like leaps against a 9-game season | 13 · 13.7× | 16 · 4.0× |
| 3. + relative change, team, age, second year | D24 | Voters reward a jump that is large *for that player*, winning teams and youth | 15 · 19.2× | 9 · 5.1× |
| 4. + scoring turning point at 20 | D27 | Established scorers are MVP candidates, not MIP ones | 17 · 23.0× | 5 · 6.0× |
| 5. + already an All-Star | D38 | 0 of 26 winners had been an All-Star | 17 · 24.6× | 5 · 6.4× |
| 6. + back from a lost season | D39 | 0 of 26 winners were returning from a lost season | 17 · 24.9× | 5 · 6.5× |
| 7. Turning point on game score | D41 | Voters discount established all-round players, not only scorers | 17 · 24.9× | 7 · 6.6× |
| 8. + already clearly a star | D42 | Elite players who improve get MVP votes, not Most Improved | 17 · **26.1×** | 7 · **6.8×** |

- **The largest gain came from understanding voters** (stage 3), followed by the baseline fix (stage 2) and the turning point (stage 4).
- **The latest steps are smaller, as expected:** about 7% for the All-Star input and 1–2% for the lost-season input. Each was kept because it improved every test, and both matter most at the top of the list, where they remove players voters were never going to choose.
- **The preseason predictor followed the same path,** from 1.4× a blind guess on last season alone to 6.0× with everything known on opening night. Its largest steps were preseason form ([D26](docs/DECISIONS.md)) and an open role (D29).

#### Every stage on today's race

The same nine stages, each trained as the live race is and applied to 2026-27 (11 November, day 22 after opening night). Stage 8 is the live race itself.

![The 2026-27 race under each stage](outputs/figures/19_stages_live.png)

- **The stages agree on the leader, and disagree on how sure to be.** From stage 2 onwards Ty Jerome is #1 under every stage, at 24–38% until stage 5. Counting his lost 2025-26 season against him (stage 6, D39) brings him down to 8.6%; the later stages leave him at 12.3%.
- **The baseline fix (stage 2) is what puts Jerome on top.** Against his injury-shortened 2025-26 (15 games, 19.7 points) his jump is about +7 points; against his last full season (12.5 points) it is +14.
- **The voter inputs (stage 3) bring in Anthony Black,** who is young (23) and whose jump is large for him. **The turning point (stage 4) brings in Franz Wagner,** whose 20.6-point baseline sits right at it.
- **The All-Star input (stage 5) moves Victor Wembanyama** from 2nd to 6th, but only **"already clearly a star" (stage 8, D42)** takes him out of the top 12, and it moves Cooper Flagg from 4th to 10th.
- **Without the baseline fix the race would be chaotic:** under stage 1, nine different players have led in 22 days.

### Beyond points per game

**Points per game is the illustration, not the model.** Charts and tables show points because every reader knows them. The models use far more: the live race weighs changes in every box-score statistic, the preseason model uses minutes, usage, preseason production and the team's situation, and the breakout models use 197 features. [Notebook 21](notebooks/archive/21_beyond_ppg.ipynb) lists what every model and rule uses.

Where points did stand alone was in a few **rules**. Those inside a model were tested against an all-round version and kept only if it did better in the strict test; the blip test predicts nothing and was written in advance, so its all-round version is shown alongside rather than tested ([D46](docs/DECISIONS.md)):

| Rule | Defined on | Status |
|---|---|---|
| The turning point ([D27](docs/DECISIONS.md)) | Last season's points above 20 | **Tested:** game score in the live race, points kept before the season ([D41](docs/DECISIONS.md)) |
| "Already a star" (D38) | All-Star selections only | **Extended:** a baseline game score of 16+ and last season in our star tier also count against a candidate ([D42](docs/DECISIONS.md)) |
| "A 20-point scorer left" ([D29](docs/DECISIONS.md)) | The departed player's points | **Tested:** points kept; game score and usage did worse ([D43](docs/DECISIONS.md)) |
| The blip test ([D33](docs/DECISIONS.md)) | Share of the points jump kept | **Shown alongside:** game score agrees with points on 84% of verdicts, and the break is as good a guide (83% against 86%); the points verdict stays, as written in advance ([D46](docs/DECISIONS.md), notebook 16D) |
| Ty Jerome lookalikes (notebook 18) | Up 8+ points at day 19 | **Moved** to similar players at the same stage, on every metric (Phase C, [D46](docs/DECISIONS.md)) |

**The turning point, tested.** For each measure, the turning point was chosen inside each training set, from five values at the same percentiles of candidates as 16–24 points. The rule for deciding was written before the results: a measure replaces points only if it improves the strict test at most points of the season, without losing a winner from the top 7.

![The turning point on points, game score or usage](outputs/figures/21_turning_point_measures.png)

- **In the live race, game score won** at day 19 (6.3× to 6.4× a blind guess) and at season's end (23.4× to 24.4×), and lost narrowly at day 85. By the rule, it replaces points (D41).
- **Before the season, points stayed.** Nothing beat it, and usage was worse.
- **The differences are small, and that is the finding.** Baseline points and game score correlate at 0.955. Voters discount *established* players, whether their standing comes from scoring or from all-round production; the rule was never really about points.

**Already clearly a star, tested.** The game-score turning point turned out to *neutralise* an elite level rather than count against it, so a star with a big jump (Victor Wembanyama this season) could still rank highly. Since 2000-01, 75 candidates had a baseline game score of 22+; none finished in the top 5 of the vote. Three options were tested ([notebook 21C–21D](notebooks/archive/21_beyond_ppg.ipynb)):

| Option | Strict test, same seasons (2012-13 → 2025-26) | Leave-one-out |
|---|---|---|
| A baseline game score of 16+ (threshold chosen inside training) | +4.3% | +3.9% |
| Last season in our star tier (notebook 05) | +2.4% | +4.5% |
| **Both** | **+6.4%** | **+7.8%** |

- **Both are now in the live race (D42).** Each cuts a player's odds to about a third, alongside "already an All-Star".
- **The evidence is modest.** The previous model already expected only about 0.2 wins from elite-baseline players, so this sharpens the model rather than correcting a large error. At mid-season the winner lands in the top 3 slightly less often.
- **The question came from the live board (Wembanyama and Flagg ranking high), but the answer came from the test.** The decision rule was written before the results; when its first tie-break turned out to compare 9 seasons with 21, it was replaced before the deciding test ran, not after.

## The live 2026-27 Most Improved race

> [!TIP]
> **Last updated 11 November 2026 (day 22 after opening night). The model is frozen until the season ends ([D44](docs/DECISIONS.md)),** so 2026-27 is a genuine out-of-sample test; the race still updates daily. Run `./scripts/update_mip_race.sh`, or re-run [notebook 12](notebooks/4b_live_race.ipynb), to add the newest days.

| Rank | Player | Chance | Points a game (baseline season) |
|---|---|---|---|
| 1 | **Ty Jerome** | 12.3% | 26.2 (12.5) |
| 2 | Davion Mitchell | 6.3% | 16.5 (9.3) |
| 3 | Anthony Black | 6.3% | 17.8 (15.0) |
| 4 | Franz Wagner | 5.7% | 23.5 (20.6) |
| 5 | Ajay Mitchell | 3.3% | 18.5 (13.6) |
| 6 | Brandin Podziemski | 3.0% | 17.0 (13.8) |
| 7 | Kyshawn George | 2.7% | 18.5 (14.8) |

*Points are shown for readability; the model uses changes in every box-score statistic (see [what voters reward](#what-voters-reward)).* **Established stars have dropped back** since "already clearly a star" was added (D42, [see below](#beyond-points-per-game)): Cooper Flagg is 10th, because his rookie season was already at a game score of 16.3, and Victor Wembanyama 17th, because he trips all three established-star inputs. Of the preseason top 7 (notebook 11), Flagg is still the closest.

- **A leaderboard for every day, with no leakage.** Day *n* uses only games up to day *n*, scored by a model trained on past seasons cut at the same day. Each day is saved once and never recomputed.
- **Everyone is a candidate,** including previous winners, established scorers, prior All-Stars and players returning from a lost season, each handled by an input rather than by exclusion.
- **The turning point is on the baseline season's game score, and chosen by the data each day** ([D41](docs/DECISIONS.md), [D32](docs/DECISIONS.md)), from no turning point or game score 12.5–18.5 (the same share of players as 16–24 points), using past seasons only. It is frozen at the All-Star break so that the board does not jump late in the season. It has moved between none, 14 and 15.5 (about an 18- to 20-point scorer), and was 15.5 on 11 November. Until 12 November it was on points ([why it moved](#beyond-points-per-game)).

| | |
|---|---|
| ![Daily worm chart](outputs/figures/12_daily_worm.png) | ![Three snapshots](outputs/figures/12_three_snapshots.png) |
| Our rank for everyone who has been in the top 7, day by day | End of 2025-26, end of preseason and today, with the reasons |

<details>
<summary><b>How much to trust the race: backtests (notebook 22)</b></summary>

- **How early is too early?** At day 2 the eventual winner was in our top 7 in 5 of 15 past seasons; by day 60, in 11 of 15; by day 90, in 13 (leave-one-out, so slightly kind).
- **Five-season strict backtest (2021-22 → 2025-26):** the winner was in our end-of-previous-season top 7 once, in our preseason top 7 three times, and in our mid-January top 7 in **4 of 5 seasons** (median rank 2).
- **Before the season, a new role is the clue.** Lauri Markkanen and Dyson Daniels were traded to teams that had just lost their star, and the preseason list found both. Nickeil Alexander-Walker's and Tyrese Maxey's leaps were not visible before the season.

![Five-season backtest](outputs/figures/22_backtest_five_seasons.png)

</details>

### Is Ty Jerome's lead believable?

> [!WARNING]
> **Not at the 26% the model first gave him.** Players with Jerome's profile have rarely won, and big early favourites in general have won only about 1 time in 6 ([see below](#are-the-chances-honest)). Since 10 November the model counts his lost 2025-26 season against him ([D39](docs/DECISIONS.md)), which brought his chance down to about 8%; with the later changes (D41, D42) it is 12.3% on 11 November.

**Have there been Ty Jeromes before?** Every player since 2000-01 who looked like him at the same point of the season (day 19), and how his season ended ([notebook 3, case 3B](notebooks/3_mip_investigations.ipynb); detail in the archived [notebook 18](notebooks/archive/18_ty_jerome_effect.ipynb)):

| Up 8+ points a game at day 19 | Players | Jump kept by season's end | Top 3 | Won |
|---|---|---|---|---|
| **Aged 27+, bench role the season before** (the strict lookalikes) | 14 | 65% | 0 | 0 |
| Aged under 27, bench role the season before | 53 | 79% | 6 | 3 |
| Aged 27+, any role | 31 | **58%** | 1 | **1** |
| The 12 players closest to Jerome | 12 | 61% | 1 | 0 |

- **There has never been an older hot start this large.** Jerome's +14.1 points is the biggest day-19 jump by any player aged 27 or over in 26 seasons; the next were Norman Powell (+11.6, 2024-25) and AJ Price (+11.4, 2014-15).
- **Older early leaders have a poor record.** Three day-19 leaders were 27 or older (Jarrett Jack, Norman Powell and Austin Reaves); none won, and Powell received no votes. Across all day-19 top 3s, the 7 players aged 27+ won no awards, while the 71 younger players won 9.
- **It can happen, and it did last season.** Nickeil Alexander-Walker was 27 and up 8.2 points at this point, and he kept the whole jump.
- **Jerome's own record adds caution:**
  - **His baseline is stale.** It is 2024-25 (12.5 points), because 2025-26 was injury-shortened. In those 15 games he averaged 19.7, so part of the leap had already happened.
  - **Availability is a pattern.** He played 2 games in 2023-24 and 15 in 2025-26, and has missed 2 of Memphis's first 10 this season.
  - **One night lifts his average.** Without his 45-point opener he averages 24.0, not 26.6.

![The Ty Jerome effect](outputs/figures/18_ty_jerome_effect.png)

*Every player up 8+ points a game at day 19, 2000-01 → 2025-26. Colour shows age, a star-shaped marker shows a player who already scored 20+ points the season before, and a ring marks a winner.*

**Conclusion:** Jerome is a genuine candidate but an unlikely winner. If he keeps the typical 58% of his jump, he will finish near 20.7 points a game: still a large leap, but one that voters have rewarded only once for a player of his age.

**Teaching the model.** Four candidate inputs were then tested at five points of the season, in both tests ([notebook 18C](notebooks/archive/18_ty_jerome_effect.ipynb)):

| Input | Tests where the fit improved (of 10) | Result |
|---|---|---|
| Older hot starts count for less (age × early jump) | 0 | Rejected: the existing age penalty already covers it |
| **Back from a lost season** (last season was lost or injury-shortened) | **10** | **Adopted** ([D39](docs/DECISIONS.md)) |
| How much of the jump already showed in that short season | 6, by tiny amounts | Rejected: adds nothing beyond the lost-season input |
| Share of the team's games played | 2 | Rejected |

So the "Ty Jerome effect" is less about age than about **returning from a lost season**, which voters appear to treat as a return rather than an improvement. None of the 26 winners was in that position, against about 1.2 expected. That count alone is weak evidence (a 30% chance by luck), so the input was adopted because it improved the fit at every point of the season, in both tests.

### Are the chances honest?

When the race gives a player a 20% chance, do such players win about one time in five? [Notebook 20](notebooks/archive/20_calibration.ipynb) checks every out-of-sample chance from 2000-01 to 2025-26, at ten points of each season.

![Are the chances honest?](outputs/figures/20_calibration.png)

- **On the whole, yes.** Players given 1–3% won about 2% of the time; 3–10%, about 6–8%; 10–25%, about 15–19%.
- **A general correction would make things worse.** The standard fix, *temperature scaling* (dividing every score by $T$ before the softmax, so that $T > 1$ spreads the chances out), asks for $T$ between 0.86 and 1.02, close to no change. Applied honestly, learned without the season it is tested on, it lowers the fit at every point of the season.
- **The one real exception is the big early favourite.** Nineteen players have been given 25% or more between days 7 and 30. The model expected about 7.5 of them to win, and only 3 did (Zach Randolph, Ja Morant, Tyrese Maxey); luck alone would give this few about 1 time in 50. Most were young, high-usage scorers whose early jump faded, such as Cam Thomas and Eric Bledsoe.
- **The decision ([D40](docs/DECISIONS.md)): flag it, do not correct it.** A correction fitted to 19 cases would be close to fitting noise. Instead, the live race prints a note whenever an early chance exceeds 25%. No player is above that line today.

### The blip test: did Alexander-Walker's leap last?

*From [notebook 3, case 3A](notebooks/3_mip_investigations.ipynb), which prints the final verdict after the All-Star break.*

Last season's winner, Nickeil Alexander-Walker, went from 9.4 to 20.8 points a game. Will the jump last, or was it a one-season spike?

**Why we examined him.**
- **His was the leap our models did not see coming.** Before 2025-26 he ranked 44th on the previous season's numbers and 26th after preseason, the least warning of any of the last five winners.
- **He is back in the race,** because previous winners stay in the pool. He sits around 35th: not because he is slipping, but because a second leap on top of the first is rare.
- **The question kept coming up, so it was given a fixed answer in advance.** The rule was written down on 30 October ([D33](docs/DECISIONS.md)), before the result was known, so the verdict cannot be adjusted to fit what happens.

The measure is the share of the leap kept:

$$
\text{share kept} \;=\; \frac{\text{points a game this season} - 9.4}{20.8 - 9.4}
$$

| Verdict | Share kept | Points a game |
|---|---|---|
| **Real** | 80% or more | about 18.5+ |
| **Partly real** | 50–80% | about 15.1–18.5 |
| **Blip** | under 50% | under about 15.1 |
| **Not enough games** | fewer than 25 games by the All-Star break | decided at season's end, same cut-offs |

- **Why these lines:** they separate the 14 past winners into clear groups. Nine kept 80%+ the following season, two kept most of it (Markkanen, Daniels) and three fell back sharply (Dragić, Oladipo, Randle).
- **Why the All-Star break is early enough:** for all 14 past winners, the verdict at the break matched the verdict over the full season.
- **So far (12 games, to 11 November):** 21.9 points a game, 110% kept. On track for "real", but it is early.
- **Alongside, not the verdict:** on game score he has kept 91% (7.5 → 15.3 → 14.6). Across 541 past leaps, game score and points give the same verdict about five times in six ([notebook 16D](notebooks/archive/16_do_leaps_last.ipynb), [D46](docs/DECISIONS.md)).

<details>
<summary><b>Backtest: the blip test on 609 leaps since 2000-01, and its victims</b></summary>

The test is not specific to Alexander-Walker, so it was run on 609 leaps from 2000-01 to 2024-25: every MIP vote-getter who jumped 3+ points a game, and everyone who jumped 5+, voted for or not ([notebook 16](notebooks/archive/16_do_leaps_last.ipynb)).

- **It does what it claims.** The verdict at the break matched the full season for **86%** of the 541 leaps with enough games, and most misses were within 10 points of a cut-off. "Real" at the break never became "blip" by season's end.
- **Its victims are about the longer run.** The test looks one season ahead. Two seasons on:
  - **About 1 blip in 5 comes back** (25 leaps). The best-known is **Julius Randle**, the 2020-21 winner: 7% kept at the next break, then an All-NBA season the year after. Russell Westbrook's case is instructive: his leap came while Kevin Durant was injured; his scoring fell when Durant returned and rose again when Durant left.
  - **About 1 "real" in 6 collapses later** (48 leaps), mostly through injury: Brandon Roy, Darius Garland, Isaiah Thomas.
- **Points per 36 minutes is a weak hint, not a rule.** Blips who kept their scoring rate came back 44% of the time, against 27% for those whose rate fell, but this rests on only 18 players, so the test stays as written.

![Blip test backtest](outputs/figures/16_do_leaps_last.png)

</details>

---

## How it works

| Notebook | What it does |
|---|---|
| `0_data` | Where the data comes from and the traps found; builds every table the other notebooks read (player-seasons, shrinkage, season-relative measures, trajectories with a leakage test, position and star-score inputs, game logs, All-Star selections) |
| `1_mip_basic` | **Segment 1.** The basic Most Improved race: how winners' seasons unfold, what early form to trust, the biggest points jump, the first choice model and what voters reward, and the misses |
| `2_play_styles` | **Segment 2.** Playing styles: how many kinds, the eight named kinds and who is in each, players moving between kinds, and 2000-01 → 2025-26 with no era adjustment ([write-up](docs/EIGHT_CLUSTERS.md)) |
| `3_mip_investigations` | **Segment 3.** Four cases the live board raised, each tested: did Alexander-Walker's leap last (the blip test), is Ty Jerome's lead believable (back from a lost season), already a star (All-Star and elite level), an open role (a 20-point scorer left). Full detail in the archived notebooks 14, 16, 17, 18 and 21 |
| `4_mip_race` | **Segment 4.** The revised race: the current model at six checkpoints (after the previous season, preseason, day 15, day 30, the All-Star break, season's end), how it evolved one decision at a time, whether its chances are honest, and 2026-27 at each checkpoint |
| `4b_live_race` | The live 2026-27 race, one leaderboard per day; three snapshots with reasons. Updated by `./scripts/update_mip_race.sh` |
| `archive/` | All 23 original notebooks (00–22), kept as the detailed record: every intermediate step, and the evidence the decision log cites. The breakout, star and unicorn work (04–09) lives only here ([D47](docs/DECISIONS.md)) |

### Terms used throughout

Each notebook opens with **In brief** (the question, the answer, the decisions it rests on, and where it fits) and closes with its **findings**. These terms mean the same thing everywhere.

**Testing**

| Term | Meaning |
|---|---|
| **Strict test** (walk-forward) | Each season is predicted by a model trained only on *earlier* seasons, exactly as it could have been used at the time. The test we trust most. |
| **Leave-one-out** (leave-one-season-out) | Each season is predicted by a model trained on every *other* season, later ones included. It uses more data, so it is steadier, but kinder than the strict test. We report both. |
| **× random** (breakouts) | How many times more often our top picks break out than players picked at random. Also called *lift*. |
| **× a blind guess** (Most Improved) | How much more chance the model gave the real winner than an even split across every candidate, averaged over seasons (geometric mean). 1× means no better than guessing. |
| **Calibration** | Whether the chances are honest: players given 10% should win about one time in ten (notebook 20). |
| **Day *N*** | Days after opening night: opening night is day 0, day 19 is about three weeks in, day 85 is about mid-January. Used the same way everywhere, including the live race's daily file. |

**Most Improved**

| Term | Meaning |
|---|---|
| **Baseline season** | The season a player's improvement is measured from: their most recent earlier season covering at least a third of the games ([D22](docs/DECISIONS.md)). Injury-shortened seasons are skipped. |
| **Choice model** (conditional logit) | Every candidate in a season competes for one award, so the chances add up to 100%. Each input gets a weight learned from past winners ([D24](docs/DECISIONS.md)). |
| **Penalty λ** | How strongly the choice model's weights are held back towards zero, so it does not chase a handful of winners. λ = 3 ([D30](docs/DECISIONS.md)). |
| **Turning point** | Last season's level counts for a candidate up to a point and against them above it: established players are MVP material, not Most Improved. Before the season it is on points (20 a game, [D27](docs/DECISIONS.md)); in the live race on the baseline season's game score (14, [D41](docs/DECISIONS.md)). |
| **Already an All-Star** | Picked for an All-Star game in any *earlier* season. Counts against a candidate ([D38](docs/DECISIONS.md)). |
| **Already clearly a star** | A baseline game score of 16+, or a baseline season in our star tier. Each counts against a candidate in the live race ([D42](docs/DECISIONS.md)). |
| **Back from a lost season** | The baseline season is older than last season, because last season was lost to injury. Counts against a candidate ([D39](docs/DECISIONS.md)). |
| **The blip test** | The share of a scoring leap kept at the next All-Star break: 80% or more is real, 50–80% partly real, under 50% a blip ([D33](docs/DECISIONS.md)). |

**Measures**

| Term | Meaning |
|---|---|
| **Game score** | A one-number summary of a box-score line: points, rebounds, assists, steals and blocks, less missed shots, turnovers and fouls. |
| **Usage** | The share of the team's possessions a player finishes while on the court. |
| **True shooting** | Points per shooting attempt, counting threes and free throws. |
| **Per 36** | A rate scaled to 36 minutes, so that bench and starting minutes compare fairly. |
| **Season-relative** (z-score) | A measure compared with that season's rotation players (500+ minutes), in standard deviations. It removes the league's drift, such as the rise of the three. |
| **Shrinkage** | Pulling a percentage from a small sample towards the average, by an amount that depends on the number of attempts ([D11](docs/DECISIONS.md)). |
| **Breakout** | A season well above the player's own previous three, in all-round production (beyond normal growth for their age), role or scoring ([D17](docs/DECISIONS.md)). |
| **Star score, star season, star tier** | The star score is our own six-part all-round measure, half-adjusted for body size. Two cut-offs on it: a **star season** is the top 5% of a season (with 1,500+ minutes), used for "star within 3 years" (notebooks 05–07); the **star tier** is the top 10%, about 19 players a season, used for the routes to stardom (09) and "already clearly a star" ([D17](docs/DECISIONS.md), [D21](docs/DECISIONS.md), [D42](docs/DECISIONS.md)). |
| **Unicorn** | Either a rare *combination* of strengths, or an *extreme* with no comparable players ([D16](docs/DECISIONS.md)). |
| **Cluster stability** | How closely two random halves of the data agree on the clusters (adjusted Rand index: 1 is identical, 0 is chance). |

> [!IMPORTANT]
> **Anti-leakage rules.** Every result above follows these.
> - Features for season *t* use seasons up to *t* only; notebook 03 checks this by deleting later seasons and confirming that nothing changes.
> - A training example is used only once its outcome was known at prediction time.
> - Preprocessing is fitted inside each fold, and model settings (such as the scoring turning point) are chosen from earlier seasons only.
> - Award votes are used only to mark predictions, never to train.
> - Live leaderboards are saved on the day they are made and never recomputed; rules such as the blip test are written down before the answer is known.

<details>
<summary><b>Data traps found along the way</b></summary>

- NBA.com's `PlayerIndex` returns *current* heights and positions for past seasons, which would leak future information.
- The 2019 switch to measured heights made 56% of players shorter overnight.
- The bio endpoint gives some players the wrong draft record.
- NBA.com's PIE rating over-represents big men among "stars" by about 2×.
- Same-name players (Tim Hardaway and Tim Hardaway Jr.) must be matched by ID, not by name.

</details>

## Key decisions

All 48 decisions, each with its evidence, are logged in [docs/DECISIONS.md](docs/DECISIONS.md). The ones that most shape the results:

| # | Decision | Why |
|---|---|---|
| D24 | A choice model with one winner per season | The award has exactly one winner, so chances should share a single 100% |
| D27 | Established scorers handled by a turning point at 20 points, not excluded | Keeps every player in the pool; 20 fitted best of every point from 14 to 26 |
| D29 | "A 20-point scorer left and was not replaced" as a preseason input | 7 of 21 winners against 11% of candidates; finer bands fitted noise |
| D30 | Penalty λ = 3 | Chosen on fit; a weaker penalty looked better only by tuning on 14 winners |
| D31 | No expected archetypes written down before clustering | Avoids forcing players into types we already believe in |
| D32 | The live race's turning point chosen by the data each day, frozen at the All-Star break | The same leak-free method as the 2000-26 backtest; stops late swings |
| D41 | The live race's turning point on game score, not points; preseason keeps points | Won the strict test at 2 of 3 points of the season by a rule set before the results; voters discount established all-round players, not just scorers |
| D42 | "Already clearly a star" (baseline game score 16+, last season in our star tier) counts against a candidate | Both together beat either alone on the same seasons (+6.4% strict); elite stars who improve get MVP votes, not Most Improved |
| D44 | The live model frozen until the end of 2026-27 | The core gains are robust; the recent tweaks are small or noise, and several were prompted by the live board ([audit](docs/AUDIT.md)) |
| D45 | Betting markets as a benchmark, never an input | Weekly snapshots scored against our chances at season's end |
| D33 | The blip test written down before the answer is known | The verdict cannot be adjusted with hindsight |
| D35 | Eight playing-style clusters | Less stable than five, but every split has a basketball meaning |
| D38 | "Already an All-Star" counts against a candidate | 0 of 26 winners; improved every backtest |
| D39 | "Back from a lost season" counts against a candidate | 0 of 26 winners; the only hot-start input that improved every test |
| D40 | No recalibration of chances; big early favourites flagged instead | Chances are honest on the whole; the one exception rests on 19 cases |

## Reproduce

```bash
git clone https://github.com/dan-j-e/unicorn-hunting.git && cd unicorn-hunting
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .                 # makes `import unicorn` available
python -m unicorn.download       # about 733 NBA.com requests; 40 minutes the first time; resumable
```

Then run `0_data` first: it builds every table the other notebooks read. After that, the notebooks run in any order. Raw responses are cached in `data/raw/`, so re-runs make no API calls. Notebook 0 also builds the game logs (back to 1998-99) and the All-Star selections; the Most Improved notebooks fetch the Basketball-Reference award pages (all cached).

**To update the live Most Improved race:** `./scripts/update_mip_race.sh` re-runs notebook 12 with the newest games and prints today's top 7.

<details>
<summary><b>Project structure</b></summary>

```
notebooks/        numbered research pipeline (00 → 22), saved with outputs
src/unicorn/      reusable code
  raw, download              cached NBA.com access and the full download list
  player_season, columns     clean tables and the data dictionary
  features, trajectories     shrinkage, season-relative scaling, leakage-safe trends
  position, unicorn          position spectrum and unicorn scores
  labels, backtest, comps    breakout and star labels, walk-forward engine, comparables
  gamelogs, mip, bref        game-level data, the Most Improved model, voting results
  preseason                  preseason game logs and the pre-opening-night view of each player
  mip_history, leaps         Most Improved 2000-26 backtest; the blip test
  established                'already clearly a star' inputs (D42)
  mip_eval                   how every Most Improved model is scored (strict and leave-one-out)
  live_race                  the live race's game table and candidates on any day
  allstars                   prior All-Star selections, matched by player ID
  hot_start                  hot-start inputs, including 'back from a lost season'
  calibration                temperature scaling and out-of-sample scores
  archetypes, style_history  playing-style clusters; 3-season style windows 2000-26
  board, stats, plotting     breakout board, statistics helpers, chart style
scripts/          update_mip_race.sh: refresh the live race in one command; audit_gains.py: are the model's gains real?
benchmarks/       weekly betting-market snapshots, scored against our chances at season's end (never a model input)
docs/             DECISIONS.md (decision log), EIGHT_CLUSTERS.md (the eight kinds of player), AUDIT.md (the project audit)
outputs/          figures and tables
data/             raw and processed data (not in git; rebuilt from code)
```

</details>

## Limitations

> [!CAUTION]
> - **Box-score data only.** There is no play-by-play, lineup, injury, contract or scouting data, and on-court net rating mixes player and team quality.
> - **The Most Improved scores are partly in-sample.** Each past season is predicted from earlier seasons, but the model's settings and later inputs were chosen by looking at those same seasons. 2026-27, with the model frozen, is the first clean test.
> - **Few positive cases.** About 26 future stars, 28 production breakouts and 15–26 Most Improved winners (depending on the period) mean wide uncertainty around every result.
> - **Voters are not only box-score readers.** Prior All-Star selections are now in the model, but wider reputation and narrative (the reason Harden finished 7th in 2012-13) are not.
> - **Big early favourites are over-rated.** Chances are honest on the whole, but players given 25%+ before about day 45 have won only about 1 time in 6; the live race flags them.
> - **"Star" is our own definition** (six equally weighted pillars), so one-dimensional scorers rarely qualify, by design.
> - **One rookie season is thin evidence.** Predictions for second-year players are far better informed than for rookies.

## What's next

The full list, with options and priorities, is in [TODO.md](TODO.md).

- [x] Count "already an All-Star" against Most Improved candidates ([D38](docs/DECISIONS.md))
- [x] Investigate the Ty Jerome effect ([notebook 3, case 3B](notebooks/3_mip_investigations.ipynb))
- [x] Test hot-start inputs: only "back from a lost season" helped ([D39](docs/DECISIONS.md))
- [x] Show how the predictor evolved, one decision at a time ([notebook 19](notebooks/archive/19_predictor_evolution.ipynb))
- [x] Check whether the chances are honest: they are, except for big early favourites, which are now flagged ([D40](docs/DECISIONS.md))
- [x] Audit the project: relevant, easy to understand and educational throughout ([what changed](docs/AUDIT.md))
- [x] Run every stage of the predictor on today's race ([notebook 19B](notebooks/archive/19_predictor_evolution.ipynb))
- [x] Audit 2: are the recent gains real? The model frozen for 2026-27 (D44); markets as a benchmark only (D45)
- [x] Audit 3: every notebook swept; claims made more honest; the daily update cut to about 20 seconds ([docs/AUDIT.md](docs/AUDIT.md))
- [x] Make points per game the illustration, not the model: the turning point (D41), "already clearly a star" (D42) and "a star left" (D43) tested; the blip test shown on game score; captions say what each model uses; the lookalikes move to similar players (D46)
- [ ] Tests and automatic checks on every pull request
- [ ] Value or reputation? Our own measure of what a player is worth, against what a casual fan sees
- [ ] Find similar players at the same career stage, with era adjustment, and follow how their seasons and careers turned out
- [ ] Track the 2026-27 breakout predictions as the season unfolds
- [ ] Does changing your game pay off? Moves between the eight kinds, and the growth paths open to rookies
- [ ] A live site on GitHub Pages
- [ ] When the model reopens (2027-28): one package tested once, with its rule written first (D46)
- [ ] Later: a sentiment trial and scouting cards

[^strict]: **Strict** or **walk-forward**: each season is predicted by a model trained only on earlier seasons, exactly as it could have been at the time. **Leave-one-season-out**, used where noted, predicts each season from all the others, including later ones; it uses more data but is less faithful to what was knowable.
[^gamescore]: **Game score** (John Hollinger) combines a player's points, shooting, rebounds, assists, steals, blocks, fouls and turnovers into a single number for one game. About 10 is an average game; 40 is an exceptional one.
