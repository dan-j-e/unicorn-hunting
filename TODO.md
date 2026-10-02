# To do

Goal for this phase: turn a working pipeline into something **explainable and worth showing**. The analytical decisions are made deliberately, one step at a time.

## Next up

### 1. Player archetypes (clustering) + "who is similar to who"
- Cluster player-seasons into recognisable **archetypes** (e.g. creator big, 3-and-D wing, rim-runner, on-ball scorer). Use style features, not quality, so a good and a bad rim-runner share a type.
- Name the archetypes. **Before clustering, write down the archetypes you expect**, then compare them with what the data finds.
- **Similarity:** for any current player, find the most similar historical players *at the same career stage* (e.g. Dëmin's rookie year vs past rookie years), within and across archetypes.
- **Movement:** how players move between archetypes as they develop, and which moves lead to stardom.
- Decisions for you: which features define style; per-season vs career-stage; how many archetypes; hard clusters vs soft (mixtures).

### 2. Explain every pick ("scouting cards")
- For each breakout or star candidate: the 3–4 signals pushing his chances up or down, in basketball language; his archetype; closest historical comps; what he'd need to do next season.
- Method options: per-player feature contributions (SHAP-style for trees, or coefficients × values for the 12-signal logistic).

### 3. One story people would read
- A short visual piece around a single question, e.g. *"Could we have seen Shai coming?"*. Cover what he looked like each year, when the data caught on, the steady-climb counterexample (Edwards), and the misses (2023-24's 0-for-10).
- About 5–6 charts, a few hundred words, explainable in 3 minutes.
- Visual style informed by item 4.

### 4. Style reference: halfpast*noon
- [halfpastnoon.com](https://halfpastnoon.com/) · [YouTube](https://www.youtube.com/@halfpast-noon) · [TikTok](https://www.tiktok.com/@halfpast.noon). A "social-media-enabled basketball magazine": real stories plus real numbers, clean minimal graphic design.
- **You:** pick 3–5 of their pieces you like (links or screenshots). Together: list what makes them work (one idea per graphic, how numbers are framed, typography, colour, captions) and apply it to items 1–3.

## Later (from earlier sessions)
- Early playoff experience → development / unicorn / breakout.
- "Becomes a unicorn" outcome label.
- Basketball-Reference / CraftedNBA metrics (VORP, BPM, WS…).
- Track the 2026-27 predictions as the season plays out.
- Breakout board: add a "route to stardom" view.

## Parked
- Streamlit dashboard (`dashboard/app.py`): works, but not a focus.
