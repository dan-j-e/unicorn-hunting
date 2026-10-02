"""Outcome labels for breakout and star analysis.

Labels describe what happened in a season *relative to the player's own past*, so
they deliberately use the season being labelled. When a model predicts from season t,
the label is taken from t+1 (or t+1..t+3): labels are outcomes, never features.

The age curve that defines "normal improvement" is frozen from the first training
window (2011-12 → 2016-17) so later seasons cannot shape earlier labels.
"""

import numpy as np
import pandas as pd

# Most Improved Player winners (player_id), for validation only.
# Source: https://en.wikipedia.org/wiki/NBA_Most_Improved_Player_Award (checked 2026-10-02)
MIP_WINNERS = {
    "2011-12": 201583, "2012-13": 202331, "2013-14": 201609, "2014-15": 202710, "2015-16": 203468,
    "2016-17": 203507, "2017-18": 203506, "2018-19": 1627783, "2019-20": 1627742, "2020-21": 203944,
    "2021-22": 1629630, "2022-23": 1628374, "2023-24": 1630178, "2024-25": 1630700, "2025-26": 1629638,
}

SEASON_GAMES = {"2011-12": 66, "2019-20": 72, "2020-21": 72}  # shortened seasons; others 82
CURVE_WINDOW_END = 2016  # last season_start used to fit the "normal improvement" age curve

# Thresholds (candidates; see notebook 05)
REAL_SEASON_MIN = 1200   # minutes, scaled to an 82-game season
PRODUCTION_EXCESS = 1.0  # PIE z above own past, beyond what is normal for his age
PRODUCTION_LEVEL = 0.5   # ...and ending at least this far above an average rotation player
ROLE_MPG = 6.0           # minutes per game above own past
ROLE_USG = 0.5           # usage z above own past
SCORING_PPG = 5.0        # points per game above own past
SCORING_LEVEL = 15.0     # ...and at least this many points per game
EFFICIENCY_FLOOR = -0.5  # shrunk TS% z may not drop more than this vs own past
STAR_PIE_PCTL = 0.95     # top 5% of that season's rotation players by PIE
STAR_MIN = 1500


def _past_rate(df, num, den, window=3):
    """Ratio of sums over the previous `window` seasons played (excluding the current one)."""
    by = df["player_id"]
    roll = lambda s: s.groupby(by, sort=False).rolling(window, min_periods=1).sum().reset_index(level=0, drop=True)
    n, d = roll(df[num]), roll(df[den])
    return (n / d).groupby(by, sort=False).shift()


def add_labels(df, real_season_min=REAL_SEASON_MIN):
    """Breakout labels; `real_season_min` = minutes (scaled to 82 games) a breakout season needs."""
    df = df.sort_values(["player_id", "season_start"]).reset_index(drop=True)
    df["min_scaled"] = df["min"] * 82 / df["season"].map(SEASON_GAMES).fillna(82)
    df["ppg"] = df["pts"] / df["gp"]
    df["ppg_vs_past"] = df["ppg"] - _past_rate(df, "pts", "gp")
    df["mip"] = [MIP_WINNERS.get(s) == p for s, p in zip(df["season"], df["player_id"])]

    curve_rows = (df["season_start"] <= CURVE_WINDOW_END) & (df["min"] >= 500) & df["pie_z_vs_past"].notna()
    age = np.floor(df["age"]).clip(19, 34)
    curve = df[curve_rows].groupby(age[curve_rows])["pie_z_vs_past"].mean()
    df["pie_excess_vs_age"] = df["pie_z_vs_past"] - age.map(curve)

    real = df["min_scaled"] >= real_season_min
    efficient = df["ts_pct_shr_z_vs_past"] >= EFFICIENCY_FLOOR
    df["breakout_production"] = real & (df["pie_excess_vs_age"] >= PRODUCTION_EXCESS) & (df["pie_z"] >= PRODUCTION_LEVEL)
    df["breakout_role"] = (real & (df["min_per_game_vs_past"] >= ROLE_MPG)
                           & (df["usg_pct_z_vs_past"] >= ROLE_USG) & efficient)
    df["breakout_scoring"] = real & (df["ppg_vs_past"] >= SCORING_PPG) & (df["ppg"] >= SCORING_LEVEL) & efficient
    df["breakout_any"] = df[["breakout_production", "breakout_role", "breakout_scoring"]].any(axis=1)

    df["star_season_pie"] = (df["min_scaled"] >= STAR_MIN) & (df["pie_pctl"] >= STAR_PIE_PCTL)
    return df


STAR_PILLARS = {
    # pillar -> (columns, weights); all season-relative z-scores, clipped to +-4
    "scoring": (["pts_per36_z", "ts_pct_shr_z"], [1, 1]),
    "creation": (["ast_pct_z", "tm_tov_pct_z"], [1, -0.5]),
    "rebounding": (["oreb_pct_z", "dreb_pct_z"], [1, 1]),
    "defense": (["stl_per100_z", "blk_per100_z", "def_rating_z"], [1, 1, -1]),
    "impact": (["pie_z", "net_rating_z"], [1, 1]),
    "trust": (["min_per_game_z"], [1]),  # how much the coach plays him
}
SIZE_ADJUSTMENT = 0.5  # 0 = raw pillars, 1 = fully relative to players of the same body size
STAR_SCORE_PCTL = 0.95


def add_star_score(df, size_adjustment=SIZE_ADJUSTMENT):
    """Our own star metric: mean of six pillars, partly judged relative to players of the same size.

    Uses only the season itself (no reputation, awards, draft slot or future). Each pillar is
    blended between its raw value and its value relative to body size (`position_body`), with the
    size relationship fitted per season on rotation players. A star season is the top 5% of
    eligible player-seasons (>= 1,500 scaled minutes) that season.
    """
    df = df.copy()
    pillars = pd.DataFrame({
        p: sum(w * df[c].clip(-4, 4) for c, w in zip(cols, ws)) / sum(abs(w) for w in ws)
        for p, (cols, ws) in STAR_PILLARS.items()
    })
    size = df["position_body"]
    adjusted = pd.DataFrame(index=df.index, columns=pillars.columns, dtype=float)
    for _, idx in df.groupby("season").groups.items():
        ref = idx[(df.loc[idx, "min"] >= 500) & size[idx].notna()]
        design = lambda rows: np.column_stack([np.ones(len(rows)), size[rows], size[rows] ** 2])
        for p in pillars:
            beta = np.linalg.lstsq(design(ref), pillars.loc[ref, p], rcond=None)[0]
            adjusted.loc[idx, p] = pillars.loc[idx, p] - design(idx) @ beta
    blended = (1 - size_adjustment) * pillars + size_adjustment * adjusted
    for p in blended:
        df[f"pillar_{p}"] = blended[p]
    df["star_score"] = blended.mean(axis=1)
    eligible = df["min_scaled"] >= STAR_MIN
    df["star_pctl"] = df[eligible].groupby("season")["star_score"].rank(pct=True)
    df["star_season"] = eligible & (df["star_pctl"] >= STAR_SCORE_PCTL)
    return df


def add_future(df, cols, horizon=1, name="next"):
    """For each column, whether it is True in any of the next `horizon` *calendar* seasons.

    A season the player did not play counts as False (out of the league = no breakout).
    Also adds `observable_{name}{horizon}`: False when the window runs past the last
    season in the data, so those rows can be excluded rather than counted as negatives.
    """
    key = df.set_index(["player_id", "season_start"])
    for c in cols:
        hits = np.zeros(len(df), dtype=bool)
        for k in range(1, horizon + 1):
            idx = pd.MultiIndex.from_arrays([df["player_id"], df["season_start"] + k])
            hits |= key[c].reindex(idx).fillna(False).astype(bool).to_numpy()
        df[f"{c}_{name}{horizon}"] = hits
    df[f"observable_{name}{horizon}"] = df["season_start"] + horizon <= df["season_start"].max()
    return df


STAR_TIER_PCTL = 0.90  # "star tier": top 10% of eligible players by star score (~19 a season)
STEADY_MIN_RISE = 0.10  # a steady riser must climb at least this many percentile points


def add_star_routes(df, horizon=3, tier=STAR_TIER_PCTL, min_rise=STEADY_MIN_RISE):
    """Two routes into the star tier within `horizon` seasons, for players not yet in it.

    star_tier_next{h}   reaches the star tier in one of the next h calendar seasons
    route_breakout      ...and had at least one breakout season on the way (up to and including arrival)
    route_steady        ...with NO breakout season on the way and a rise of >= `min_rise` percentile points
    """
    df = df.copy()
    df["star_tier"] = df["star_pctl"].fillna(0) >= tier
    key = df.set_index(["player_id", "season_start"])
    reached = np.zeros(len(df), dtype=bool)
    broke_out = np.zeros(len(df), dtype=bool)
    arrival_pctl = np.full(len(df), np.nan)
    for k in range(1, horizon + 1):
        idx = pd.MultiIndex.from_arrays([df["player_id"], df["season_start"] + k])
        tier_k = key["star_tier"].reindex(idx).fillna(False).astype(bool).to_numpy()
        brk_k = key["breakout_any"].reindex(idx).fillna(False).astype(bool).to_numpy()
        pct_k = key["star_pctl"].reindex(idx).to_numpy()
        not_yet = ~reached
        broke_out |= not_yet & brk_k                 # breakouts count up to (and including) the arrival season
        arrive = not_yet & tier_k
        arrival_pctl[arrive] = pct_k[arrive]
        reached |= tier_k
    # Starting level = most recent known star percentile (injury-shortened seasons have none); past-only
    start = df.sort_values("season_start").groupby("player_id")["star_pctl"].ffill().reindex(df.index).fillna(0).to_numpy()
    eligible = ~df["star_tier"].to_numpy()
    df[f"star_tier_next{horizon}"] = eligible & reached
    df["route_breakout"] = eligible & reached & broke_out
    df["route_steady"] = eligible & reached & ~broke_out & (arrival_pctl - start >= min_rise)
    return df
