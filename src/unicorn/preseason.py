"""Pre-season view: what is known about each player before a season starts.

One row per (player, upcoming season t), built only from seasons before t plus the preseason of t:
  * baseline season = most recent regular season < t covering >= 33% of the games (as in gamelogs)
  * last-season level, momentum (vs the season before; after vs before the All-Star break)
  * preseason form per 36 minutes relative to the baseline, shrunk by preseason minutes
  * preseason minute INCREASES only (decreases are mostly veterans resting)
"""

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import leaguegamelog

from unicorn.gamelogs import BASELINE_MIN_SHARE, add_game_metrics
from unicorn.raw import fetch

PRESEASON_SEASONS = [f"{y}-{str(y + 1)[-2:]}" for y in range(2012, 2027)]  # 2011-12 had a 2-game lockout preseason
SHRINK_MINUTES = 150  # preseason change is multiplied by minutes / (minutes + SHRINK_MINUTES); see notebook 10.1
RATES = ["pts", "game_score", "volume"]


def load_preseason(seasons=PRESEASON_SEASONS, regular=None, refresh_latest=False):
    """Preseason game logs. Games dated on/after the regular-season opener are dropped
    (2019-20's 'preseason' includes the July 2020 bubble scrimmages)."""
    frames = []
    for s in seasons:
        g = fetch(leaguegamelog.LeagueGameLog, refresh=(refresh_latest and s == seasons[-1]), season=s,
                  player_or_team_abbreviation="P", season_type_all_star="Pre Season")["LeagueGameLog"]
        frames.append(g.assign(season=s))
    pre = pd.concat(frames, ignore_index=True)
    pre.columns = pre.columns.str.lower()
    pre["game_date"] = pd.to_datetime(pre["game_date"])
    pre["season_start"] = pre["season"].str[:4].astype(int)
    pre = add_game_metrics(pre)
    if regular is not None:
        opener = regular.groupby("season")["game_date"].min()
        keep = pre["game_date"] < pre["season"].map(opener).fillna(pd.Timestamp.max)
        pre = pre[keep]
    return pre.reset_index(drop=True)


def _per36(g, by):
    a = g.groupby(by).agg(games=("game_id", "size"), minutes=("min", "sum"), pts=("pts", "sum"),
                          game_score=("game_score", "sum"), volume=("volume", "sum"), tsa=("tsa", "sum"),
                          team_id=("team_id", "last"), player_name=("player_name", "last")).reset_index()
    a["mpg"] = a["minutes"] / a["games"]
    for r in RATES:
        a[f"{r}36"] = 36 * a[r] / a["minutes"].where(a["minutes"] > 0)
    a["ts"] = a["pts"] / (2 * a["tsa"].where(a["tsa"] > 0))
    return a


def preseason_frame(pre, regular, player_season, shrink_minutes=SHRINK_MINUTES):
    """One row per (player, season_start = upcoming season) with everything known before opening night."""
    P = _per36(pre, ["player_id", "season_start"])
    R = _per36(regular, ["player_id", "season_start"])
    season_len = regular.groupby("season_start").apply(lambda d: d.groupby("team_id")["game_id"].nunique().max(), include_groups=False)
    R["qualifies"] = R["games"] >= BASELINE_MIN_SHARE * R["season_start"].map(season_len)
    R["ppg"], R["gspg"] = R["pts"] / R["games"], R["game_score"] / R["games"]

    # after- vs before-All-Star-break game score within each regular season (late-season surge)
    half = regular.groupby(["player_id", "season_start", "after_all_star"])["game_score"].mean().unstack()
    R = R.merge((half[True] - half[False]).rename("late_surge").reset_index(), on=["player_id", "season_start"], how="left")
    team_games = regular.drop_duplicates(["team_id", "game_id"])
    team_win = team_games.assign(win=team_games["wl"].eq("W")).groupby(["team_id", "season_start"])["win"].mean().rename("team_win_pct")
    R = R.merge(team_win.reset_index(), on=["team_id", "season_start"], how="left")

    # baseline = most recent qualifying regular season strictly before t
    q = R[R["qualifies"]].sort_values("season_start")
    rows = pd.merge_asof(P.sort_values("season_start"), q.add_suffix("_last").rename(columns={"player_id_last": "player_id", "season_start_last": "base_season_start"}),
                         left_on="season_start", right_on="base_season_start", by="player_id", allow_exact_matches=False, direction="backward")
    rows = rows.dropna(subset=["base_season_start"]).copy()
    rows["base_season_start"] = rows["base_season_start"].astype(int)

    # momentum: baseline season vs the qualifying season before it
    prev = q[["player_id", "season_start", "gspg", "ppg"]].rename(columns={"season_start": "s2", "gspg": "gspg_prev", "ppg": "ppg_prev"})
    rows = pd.merge_asof(rows.sort_values("base_season_start"), prev.sort_values("s2"), left_on="base_season_start", right_on="s2",
                         by="player_id", allow_exact_matches=False, direction="backward")
    rows["momentum_game_score"] = (rows["gspg_last"] - rows["gspg_prev"]).fillna(0.0)
    rows["late_surge_last"] = rows["late_surge_last"].fillna(0.0)

    # season-table context at the baseline season, rolled forward to t
    ps = player_season[["player_id", "season_start", "age", "exp", "usg_pct", "start_rate"]].rename(
        columns={"season_start": "base_season_start", "age": "age_base", "exp": "exp_base", "usg_pct": "usg_last", "start_rate": "start_rate_last"})
    rows = rows.merge(ps, on=["player_id", "base_season_start"], how="left")
    gap = rows["season_start"] - rows["base_season_start"]
    rows["age"] = rows["age_base"] + gap
    rows["prior_seasons"] = rows["exp_base"] + gap  # NBA seasons before t (exp_base = seasons before the baseline season)
    rows["second_year"] = (rows["prior_seasons"] == 1).astype(float)
    rows["new_team"] = (rows["team_id"] != rows["team_id_last"]).astype(float)

    # preseason form per 36 vs baseline, shrunk by preseason minutes; centred within season so the
    # league-wide gap between preseason and regular-season numbers drops out
    weight = rows["minutes"] / (rows["minutes"] + shrink_minutes)
    rows["pre_reliability"] = weight
    for r in RATES + ["ts"]:
        col = f"{r}36" if r != "ts" else "ts"
        raw = rows[col] - rows[f"{col}_last"]
        raw = raw - raw.groupby(rows["season_start"]).transform("median")
        rows[f"pre_{r}_change"] = (raw * weight).fillna(0.0)
    # minutes: increases only (a rested veteran's low minutes say nothing about his role)
    rows["pre_minutes_up"] = (rows["mpg"] - rows["mpg_last"]).clip(lower=0)
    rows["pre_minutes_change_raw"] = rows["mpg"] - rows["mpg_last"]
    return rows.rename(columns={"minutes": "pre_minutes", "games": "pre_games", "mpg": "pre_mpg"})


LAST_SEASON = ["ppg_last", "mpg_last", "gspg_last", "usg_last", "ts_last", "start_rate_last", "team_win_pct_last"]
MOMENTUM = ["momentum_game_score", "late_surge_last"]
PROFILE = ["age", "second_year", "new_team"]
PRE_FORM = ["pre_pts_change", "pre_game_score_change", "pre_volume_change", "pre_ts_change"]
PRE_MINUTES = ["pre_minutes_up"]
# Leaner set used for the prediction: drops inputs that duplicate others (game score ~ points + minutes,
# preseason points ~ preseason shot volume), which otherwise get large opposite-sign weights
LAST_SEASON_LEAN = ["mpg_last", "ppg_last", "usg_last", "team_win_pct_last"]
PRE_FORM_LEAN = ["pre_game_score_change", "pre_volume_change", "pre_ts_change"]
LEAN = LAST_SEASON_LEAN + PROFILE + MOMENTUM + PRE_FORM_LEAN


def regular_rates(regular):
    """Regular-season per-game and per-36 numbers per (player, season): what actually happened."""
    return _per36(regular, ["player_id", "season_start"])


def add_pool_flags(frame, winners):
    """Season label, the MIP flag and whether the player had already won the award before that season."""
    f = frame.copy()
    f["season"] = f["season_start"].map(lambda y: f"{y}-{str(y + 1)[-2:]}")
    f["mip"] = [winners.get(s) == p for s, p in zip(f["season"], f["player_id"])]
    first_win = pd.Series({pid: int(s[:4]) for s, pid in sorted(winners.items(), reverse=True)})
    f["previous_winner"] = f["player_id"].map(first_win).lt(f["season_start"]).fillna(False).astype(bool)
    return f
