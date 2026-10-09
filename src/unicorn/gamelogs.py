"""Game-level data: every player's every regular-season game, with rolling form and a baseline.

Baseline = the player's per-game averages in his most recent previous season played
(known before the current season starts, so it is leakage-safe).
"""

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import leaguegamelog

from unicorn.raw import fetch

GAMELOG_SEASONS = [f"{y}-{str(y + 1)[-2:]}" for y in range(2010, 2026)]  # 2010-11 only provides baselines
ROLLING_WINDOWS = (3, 5, 7)
METRICS = ["game_score", "pts", "min", "volume", "ast", "reb"]


def load_game_logs(seasons=GAMELOG_SEASONS):
    frames = []
    for s in seasons:
        g = fetch(leaguegamelog.LeagueGameLog, season=s, player_or_team_abbreviation="P",
                  season_type_all_star="Regular Season")["LeagueGameLog"]
        frames.append(g.assign(season=s))
    g = pd.concat(frames, ignore_index=True)
    g.columns = g.columns.str.lower()
    g["game_date"] = pd.to_datetime(g["game_date"])
    g["season_start"] = g["season"].str[:4].astype(int)
    return g


def add_game_metrics(g):
    g = g.copy()
    g["min"] = g["min"].astype(float)
    # Hollinger game score: one number for a game's all-round box-score production
    g["game_score"] = (g["pts"] + 0.4 * g["fgm"] - 0.7 * g["fga"] - 0.4 * (g["fta"] - g["ftm"]) + 0.7 * g["oreb"]
                       + 0.3 * g["dreb"] + g["stl"] + 0.7 * g["ast"] + 0.7 * g["blk"] - 0.4 * g["pf"] - g["tov"])
    g["tsa"] = g["fga"] + 0.44 * g["fta"]                  # true-shooting attempts
    g["volume"] = g["tsa"] + g["tov"]                     # possessions used (shots + turnovers)
    return g


def all_star_breaks(g):
    """Per season: the longest gap between game dates from 1 Feb to 31 Mar (the All-Star break).

    Requiring both ends of the gap inside the window excludes the 2019-20 Covid suspension.
    """
    rows = []
    for s, d in g.groupby("season"):
        dates = np.sort(d["game_date"].unique())
        y = int(s[:4]) + 1
        lo, hi = np.datetime64(f"{y}-02-01"), np.datetime64(f"{y}-03-31")
        best = (0, None, None)
        for a, b in zip(dates[:-1], dates[1:]):
            if lo <= a and b <= hi and (b - a) > np.timedelta64(best[0], "D"):
                best = ((b - a) // np.timedelta64(1, "D"), a, b)
        rows.append({"season": s, "last_game_before": pd.Timestamp(best[1]), "first_game_after": pd.Timestamp(best[2]),
                     "gap_days": best[0]})
    return pd.DataFrame(rows)


def season_baselines(g):
    """Per player-season per-game averages; then each season's baseline = most recent previous season played."""
    agg = g.groupby(["player_id", "season_start"]).agg(
        games=("game_id", "size"), **{m: (m, "mean") for m in METRICS},
        pts_sum=("pts", "sum"), tsa_sum=("tsa", "sum"), team_count=("team_id", "nunique")).reset_index()
    agg["ts_pct"] = agg["pts_sum"] / (2 * agg["tsa_sum"]).replace(0, np.nan)
    agg = agg.drop(columns=["pts_sum", "tsa_sum"]).sort_values(["player_id", "season_start"])
    by = agg.groupby("player_id")
    agg["seasons_before"] = by.cumcount()  # seasons played before this one (within 2010-11 →)
    base_cols = ["season_start", "games", *METRICS, "ts_pct"]
    prev = by[base_cols].shift().add_prefix("base_")
    return pd.concat([agg, prev], axis=1)


def build_game_table(g=None):
    """Game-level table with metrics, week of season, All-Star break flag, trade flag, rolling form and baseline."""
    g = add_game_metrics(load_game_logs() if g is None else g)
    g = g.sort_values(["player_id", "game_date", "game_id"]).reset_index(drop=True)
    starts = g.groupby("season")["game_date"].transform("min")
    g["week"] = (g["game_date"] - starts).dt.days // 7 + 1
    asb = all_star_breaks(g).set_index("season")
    g["after_all_star"] = g["game_date"] >= g["season"].map(asb["first_game_after"])
    ps = g.groupby(["player_id", "season_start"])
    g["game_number"] = ps.cumcount() + 1
    g["traded_in_season"] = ps["team_id"].transform(lambda t: (t != t.iloc[0]).cummax())
    for m in ["game_score", "pts", "min"]:
        for w in ROLLING_WINDOWS:
            g[f"{m}_roll{w}"] = ps[m].transform(lambda s, w=w: s.rolling(w, min_periods=w).mean())
    base = season_baselines(g)
    keep = ["player_id", "season_start", "seasons_before"] + [c for c in base.columns if c.startswith("base_")]
    return g.merge(base[keep], on=["player_id", "season_start"], how="left"), base, asb.reset_index()


def mip_candidates(games, player_season, min_prior_seasons=2):
    """One row per player-season: improvement vs his most recent previous season, plus MIP eligibility.

    Eligibility: >= `min_prior_seasons` previous NBA seasons (official roster experience), a baseline
    season, and enough games: the 65-game award rule from 2023-24 (a game counts at 20+ min; up to two
    15-20 min games also count), and before that, at least half of the season's games as a stand-in.
    """
    g = games
    key = [g["player_id"], g["season_start"]]
    award_games = ((g["min"] >= 20).groupby(key).sum()
                   + np.minimum(2, ((g["min"] >= 15) & (g["min"] < 20)).groupby(key).sum()))
    c = g.groupby(["player_id", "season_start", "season"]).agg(
        player_name=("player_name", "last"), team=("team_abbreviation", "last"), games=("game_id", "size"),
        ppg=("pts", "mean"), game_score=("game_score", "mean"), mpg=("min", "mean"),
        base_season_start=("base_season_start", "first"), base_ppg=("base_pts", "first"),
        base_game_score=("base_game_score", "first"), base_mpg=("base_min", "first"),
        seasons_before=("seasons_before", "first")).reset_index()
    c["award_games"] = c.set_index(["player_id", "season_start"]).index.map(award_games)
    season_len = g.groupby("season").apply(lambda d: d.groupby("team_id")["game_id"].nunique().max(), include_groups=False)
    c["season_games"] = c["season"].map(season_len)
    c = c.merge(player_season[["player_id", "season_start", "exp"]], on=["player_id", "season_start"], how="left")
    c["prior_seasons"] = c["exp"].fillna(c["seasons_before"])
    enough_games = np.where(c["season_start"] >= 2023, c["award_games"] >= 65, c["games"] >= c["season_games"] / 2)
    c["eligible"] = (c["prior_seasons"] >= min_prior_seasons) & c["base_ppg"].notna() & enough_games
    c["ppg_delta"] = c["ppg"] - c["base_ppg"]
    c["game_score_delta"] = c["game_score"] - c["base_game_score"]
    c["mpg_delta"] = c["mpg"] - c["base_mpg"]
    return c
