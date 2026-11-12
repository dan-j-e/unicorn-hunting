"""'Already clearly a star' inputs for the Most Improved models (notebook 21C-21D; decision D42).

Two inputs, both about the player's BASELINE season, so both are known on opening night:
  elite_level     1 if the baseline season's game score was 16 or more (the threshold chosen inside every
                  training window in notebook 21), else 0
  base_star_tier  1 if the baseline season was in our star tier (top 10% by star score, notebook 05), else 0.
                  Star scores exist from 2011-12, so earlier baseline seasons count as 0.

Both count against a candidate: voters reward improvement, not stars who got even better (they get MVP votes).
"""

from functools import lru_cache

import pandas as pd

from unicorn.labels import STAR_TIER_PCTL, add_labels, add_star_score
from unicorn.raw import PROJECT_ROOT

ELITE_GAME_SCORE = 16
STAR_INPUTS = ["elite_level", "base_star_tier"]


@lru_cache(maxsize=1)
def load_star_tiers():
    """Star tier (1.0 / 0.0) for every player-season from 2011-12, indexed by (player_id, season_start)."""
    uni = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "player_season_unicorn.parquet")
    s = add_star_score(add_labels(uni))
    tier = (s["star_pctl"].fillna(0) >= STAR_TIER_PCTL).astype(float)
    return pd.Series(tier.to_numpy(), index=pd.MultiIndex.from_arrays([s["player_id"].astype(int), s["season_start"].astype(int)]))


def add_established(frame, tiers=None, threshold=ELITE_GAME_SCORE):
    """Add elite_level and base_star_tier, from the baseline season (columns base_game_score, base_season_start)."""
    tiers = load_star_tiers() if tiers is None else tiers
    base = frame["base_season_start"]
    key = [(int(p), int(b)) if pd.notna(b) else None for p, b in zip(frame["player_id"], base)]   # no baseline season: not established
    return frame.assign(elite_level=(frame["base_game_score"] >= threshold).astype(float),
                        base_star_tier=[tiers.get(k, 0.0) if k else 0.0 for k in key])
