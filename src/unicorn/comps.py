"""Historical comparables ("comps"): the past player-seasons most similar to a given one.

Similarity uses the same 18 profile features as the backtested NearestComps model
(`unicorn.backtest.COMP_FEATURES`), standardized on the comparison pool.
"""

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from unicorn.backtest import COMP_FEATURES


def find_comps(df, player_id, season, pool, k=10, features=COMP_FEATURES):
    """Return the k pool rows closest to (player_id, season), with distance and similarity rank.

    `pool` is a boolean mask over df defining eligible comparison seasons (e.g. rookie
    seasons old enough to have observed outcomes). The target player is excluded.
    """
    target = df[(df["player_id"] == player_id) & (df["season"] == season)]
    if len(target) != 1:
        raise ValueError(f"expected one row for player {player_id} in {season}, found {len(target)}")
    candidates = df[pool & (df["player_id"] != player_id)]
    imputer = SimpleImputer(strategy="median").fit(candidates[features])
    scaler = StandardScaler().fit(imputer.transform(candidates[features]))
    X = scaler.transform(imputer.transform(candidates[features]))
    x = scaler.transform(imputer.transform(target[features]))
    dist, idx = NearestNeighbors(n_neighbors=k).fit(X).kneighbors(x)
    comps = candidates.iloc[idx[0]].copy()
    comps["distance"] = dist[0]
    comps["similarity_rank"] = np.arange(1, k + 1)
    return comps


def career_after(df, comps, years=3):
    """What happened to each comp in the following `years` seasons (calendar), from his comp season."""
    rows = []
    for _, c in comps.iterrows():
        later = df[(df["player_id"] == c["player_id"]) & (df["season_start"] > c["season_start"])
                   & (df["season_start"] <= c["season_start"] + years)]
        rows.append({
            "after_seasons_played": len(later),
            "after_any_breakout": bool(later["breakout_any"].any()),
            "after_star_season": bool(later["star_season"].any()),
            "after_best_star_pctl": later["star_pctl"].max(),
            "after_best_ppg": later["ppg"].max(),
            "after_best_min_per_game": later["min_per_game"].max(),
        })
    return comps.join(pd.DataFrame(rows, index=comps.index))
