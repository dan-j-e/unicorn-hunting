"""Player trajectories: how each feature has moved over a player's past seasons.

Every column computed for season t uses only that player's seasons <= t (rows are
sorted by season and all windows look backwards), so the table is safe for
walk-forward backtesting. `notebooks/03` verifies this by recomputing on data
truncated at a cutoff season and checking the earlier rows are unchanged.

Comparisons are against the player's previous season *played* (decision D13),
with `seasons_missed` recording any gap in between.
"""

import numpy as np
import pandas as pd

WINDOW = 3  # seasons played, including the current one

# Shooting percentages are weighted by their own attempts; everything else by minutes.
ATTEMPT_WEIGHTS = {
    "fg3_pct": lambda d: d["fg3a"],
    "ft_pct": lambda d: d["fta"],
    "rim_fg_pct": lambda d: d["ra_fga"],
    "ts_pct": lambda d: d["fga"] + 0.44 * d["fta"],
}


def weight_for(col, df):
    base = col.removesuffix("_z").removesuffix("_shr")
    return ATTEMPT_WEIGHTS.get(base, lambda d: d["min"])(df)


def _rolling_sum(s, by, window):
    return s.groupby(by, sort=False).rolling(window, min_periods=1).sum().reset_index(level=0, drop=True)


def add_career_context(df):
    """Career-to-date context known at the end of each season."""
    g = df.groupby("player_id", sort=False)
    df["seasons_played"] = g.cumcount() + 1  # within the 2011-12+ window
    prev_start = g["season_start"].shift()
    df["seasons_missed"] = df["season_start"] - prev_start - 1  # NaN for a player's first observed season
    df["career_min_to_date"] = g["min"].cumsum()  # within the 2011-12+ window
    df["entry_age"] = df["age"] - df["exp"]  # age when he entered the league (exp = prior NBA seasons)
    return df


def add_trajectories(df, cols, window=WINDOW):
    """For each column c add, per player and using only seasons <= t:

    c_prev     value in the previous season played
    c_delta    c - c_prev
    c_roll3    weighted mean over the last `window` seasons played (incl. t)
    c_slope3   weighted least-squares trend per season over the same window (needs >= 2 seasons)
    c_vs_past  c minus the weighted mean of up to `window` previous seasons (excl. t): how
               unusual this season is relative to the player's own recent history
    """
    df = df.sort_values(["player_id", "season_start"]).reset_index(drop=True)
    df = add_career_context(df)
    by = df["player_id"]
    x = (df["season_start"] - 2000).astype(float)  # centred for numerical stability
    new = {}
    for c in cols:
        y = df[c].astype(float)
        w = weight_for(c, df).astype(float).where(y.notna(), 0.0).fillna(0.0)
        yw = (y * w).fillna(0.0)
        has = y.notna().astype(float)

        prev = y.groupby(by, sort=False).shift()
        new[f"{c}_prev"] = prev
        new[f"{c}_delta"] = y - prev

        sw, swy = _rolling_sum(w, by, window), _rolling_sum(yw, by, window)
        new[f"{c}_roll{window}"] = (swy / sw).where(sw > 0)

        swx, swxx, swxy = (_rolling_sum(w * x, by, window), _rolling_sum(w * x * x, by, window),
                           _rolling_sum(x * yw, by, window))
        n_obs = _rolling_sum(has, by, window)
        denom = sw * swxx - swx ** 2
        new[f"{c}_slope{window}"] = ((sw * swxy - swx * swy) / denom).where((n_obs >= 2) & (denom.abs() > 1e-9))

        # Previous `window` seasons (excl. t) = the window sums shifted back one season played
        p_sw, p_swy = sw.groupby(by, sort=False).shift(), swy.groupby(by, sort=False).shift()
        new[f"{c}_vs_past"] = y - (p_swy / p_sw).where(p_sw > 0)
    return pd.concat([df, pd.DataFrame(new, index=df.index)], axis=1)
