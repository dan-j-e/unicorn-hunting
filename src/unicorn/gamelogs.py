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
METRICS = ["game_score", "pts", "min", "volume", "ast", "reb", "stl", "blk"]
BASELINE_MIN_SHARE = 0.33  # a baseline season needs >= 33% of that season's games (skips injury-shortened seasons)


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


def season_baselines(g, min_share=BASELINE_MIN_SHARE):
    """Per player-season per-game averages; each season's baseline = the player's most recent previous
    season in which he played at least `min_share` of that season's games (so a 9- or 25-game injury
    season is never the comparison point). Season length = most games played by any team that season."""
    agg = g.groupby(["player_id", "season_start"]).agg(
        games=("game_id", "size"), **{m: (m, "mean") for m in METRICS},
        pts_sum=("pts", "sum"), tsa_sum=("tsa", "sum"), team_count=("team_id", "nunique")).reset_index()
    agg["ts_pct"] = agg["pts_sum"] / (2 * agg["tsa_sum"]).replace(0, np.nan)
    agg = agg.drop(columns=["pts_sum", "tsa_sum"]).sort_values(["player_id", "season_start"])
    by = agg.groupby("player_id")
    agg["seasons_before"] = by.cumcount()  # seasons played before this one (within 2010-11 →)
    base_cols = ["season_start", "games", *METRICS, "ts_pct"]
    season_len = g.groupby("season_start").apply(lambda d: d.groupby("team_id")["game_id"].nunique().max(), include_groups=False)
    qualifying = agg[base_cols].where(agg["games"] >= min_share * agg["season_start"].map(season_len))
    prev = qualifying.groupby(agg["player_id"]).shift().groupby(agg["player_id"]).ffill().add_prefix("base_")
    return pd.concat([agg, prev], axis=1)


def build_game_table(g=None, baseline_min_share=BASELINE_MIN_SHARE):
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
    base = season_baselines(g, baseline_min_share)
    keep = ["player_id", "season_start", "seasons_before"] + [c for c in base.columns if c.startswith("base_")]
    return g.merge(base[keep], on=["player_id", "season_start"], how="left"), base, asb.reset_index()


def mip_candidates(games, player_season, min_prior_seasons=2, games_rule="half", levels=None, season_stats=True):
    """One row per player-season: improvement ("delta") vs his most recent previous season, plus eligibility.

    Eligibility: >= `min_prior_seasons` previous NBA seasons (official roster experience), a baseline
    season, and enough games. games_rule="half" (default): at least half the season's games, every
    season. games_rule="65": the 65-game award rule from 2023-24 (20+ min games count, up to two
    15-20 min games also count) and half-season before.

    Deltas: points, rebounds, assists, minutes, game score and true shooting from game logs; usage
    and start rate from the season table (previous season played; missing for 2011-12).
    Relative deltas: log ratio of this season to the baseline (1 -> 11 ppg counts far more than 21 -> 31).
    Levels: this season's game score/ppg, the baseline game score, optional `levels` (player_id,
    season_start, star_score) with its previous-season value, "became a starter", and age.

    Pass a subset of `games` (e.g. before the All-Star break) for a mid-season view, with
    season_stats=False so season-long stats (usage, start rate, star score) are not used.
    """
    g = games
    key = [g["player_id"], g["season_start"]]
    award_games = ((g["min"] >= 20).groupby(key).sum()
                   + np.minimum(2, ((g["min"] >= 15) & (g["min"] < 20)).groupby(key).sum()))
    c = g.groupby(["player_id", "season_start", "season"]).agg(
        player_name=("player_name", "last"), team=("team_abbreviation", "last"), games=("game_id", "size"),
        ppg=("pts", "mean"), rpg=("reb", "mean"), apg=("ast", "mean"), spg=("stl", "mean"), bpg=("blk", "mean"), mpg=("min", "mean"),
        game_score=("game_score", "mean"), pts_sum=("pts", "sum"), tsa_sum=("tsa", "sum"),
        base_season_start=("base_season_start", "first"), base_ppg=("base_pts", "first"), base_rpg=("base_reb", "first"),
        base_apg=("base_ast", "first"), base_spg=("base_stl", "first"), base_bpg=("base_blk", "first"),
        base_mpg=("base_min", "first"), base_game_score=("base_game_score", "first"), base_games=("base_games", "first"),
        base_ts=("base_ts_pct", "first"), seasons_before=("seasons_before", "first")).reset_index()
    c["ts"] = c["pts_sum"] / (2 * c["tsa_sum"]).replace(0, np.nan)
    c = c.drop(columns=["pts_sum", "tsa_sum"])
    c["award_games"] = c.set_index(["player_id", "season_start"]).index.map(award_games)
    season_len = g.groupby("season").apply(lambda d: d.groupby("team_id")["game_id"].nunique().max(), include_groups=False)
    c["season_games"] = c["season"].map(season_len)

    # season-level stats (usage, start rate, defensive rating) this season and in the SAME baseline season
    cols = ["usg_pct", "start_rate", "def_rating"]
    cur = player_season[["player_id", "season_start", "exp", *cols]]
    prev = player_season[["player_id", "season_start", *cols]].rename(
        columns={"season_start": "base_season_start", **{k: f"{k}_prev" for k in cols}})
    c = c.merge(cur, on=["player_id", "season_start"], how="left").merge(prev, on=["player_id", "base_season_start"], how="left")
    c["prior_seasons"] = c["exp"].fillna(c["seasons_before"])
    half = c["games"] >= c["season_games"] / 2
    enough_games = np.where(c["season_start"] >= 2023, c["award_games"] >= 65, half) if games_rule == "65" else half
    c["eligible"] = (c["prior_seasons"] >= min_prior_seasons) & c["base_ppg"].notna() & enough_games
    for stat in ["ppg", "rpg", "apg", "spg", "bpg", "mpg", "game_score", "ts"]:
        c[f"{stat}_delta"] = c[stat] - c[f"base_{stat}"]
    c["usg_delta"] = c["usg_pct"] - c["usg_pct_prev"]
    c["def_rating_delta"] = c["def_rating"] - c["def_rating_prev"]   # negative = better defence
    c["start_rate_delta"] = c["start_rate"] - c["start_rate_prev"]
    c["ppg_rel"] = np.log((c["ppg"] + 2) / (c["base_ppg"] + 2))
    c["game_score_rel"] = np.log((c["game_score"].clip(lower=-4) + 5) / (c["base_game_score"].clip(lower=-4) + 5))
    c["became_starter"] = ((c["start_rate"] >= 0.5) & (c["start_rate_prev"] < 0.5)).astype(float)
    c = c.merge(player_season[["player_id", "season_start", "age"]], on=["player_id", "season_start"], how="left")
    if levels is not None:
        lv = levels.sort_values(["player_id", "season_start"])[["player_id", "season_start", "star_score"]].copy()
        lv["base_star_score"] = lv.groupby("player_id")["star_score"].shift()
        c = c.merge(lv, on=["player_id", "season_start"], how="left")
    if not season_stats:
        c[["usg_delta", "start_rate_delta", "became_starter", "def_rating_delta"]] = np.nan
    return c
