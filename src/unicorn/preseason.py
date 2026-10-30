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
SHRINK_MINUTES = 150  # preseason change is multiplied by minutes / (minutes + SHRINK_MINUTES); see notebook 11
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


# Scoring turning point (decision D27, revised 30 Oct 2026): instead of excluding established scorers, the model
# gets last season's points plus the points above a turning point, so it can learn "more is better up to here,
# then established scorers are MVP material, not MIP". 20 fitted best of 14-26 in notebook 11.
TURNING_POINT = 20
TURN = ["ppg_over_turn"]
STAR_LEFT_PPG = 20
TEAM_CHANGE = ["star_left"]   # a 20+ point scorer left his team over the summer (notebook 14; decision D29)
USED = LEAN + TURN + TEAM_CHANGE   # the preseason model used from 30 Oct 2026


def add_turning_point(frame, ppg_col="ppg_last", k=TURNING_POINT, name="ppg_over_turn"):
    f = frame.copy()
    f[name] = (f[ppg_col] - k).clip(lower=0)
    return f


def preseason_opportunity(pre, regular):
    """Share of the player's (preseason) team's previous-season minutes that left over the summer, net of arrivals.

    Known at preseason time only: rosters are read from preseason games, never from the regular season.
      left    = players on the team at the end of t-1 seen with another team in preseason t (their minutes for that team)
      arrived = players seen with the team in preseason t who played elsewhere in t-1 (all their t-1 minutes), not the player himself
    Players not seen in preseason are not counted either way. Divided by the team's total t-1 minutes (240 a game).
    """
    end = regular.sort_values("game_date").groupby(["player_id", "season_start"])["team_id"].last().rename("from").reset_index()
    min_for = regular.groupby(["player_id", "season_start", "team_id"])["min"].sum()
    end["min_for_team"] = [min_for.get(k, 0) for k in zip(end["player_id"], end["season_start"], end["from"])]
    total_prev = regular.groupby(["player_id", "season_start"])["min"].sum()
    team_total = regular.groupby(["team_id", "season_start"])["min"].sum()
    now = pre.sort_values("game_date").groupby(["player_id", "season_start"])["team_id"].last().rename("to").reset_index()
    rows = []
    for t, cur in now.groupby("season_start"):
        e = end[end["season_start"] == t - 1].merge(cur[["player_id", "to"]], on="player_id", how="left")
        gone = e[e["to"].notna() & (e["to"] != e["from"])].groupby("from")["min_for_team"].sum()
        c = cur.merge(e[["player_id", "from"]], on="player_id", how="left")
        c["min_prev"] = [total_prev.get((p, t - 1), 0) for p in c["player_id"]]
        newcomer = c["from"].notna() & (c["from"] != c["to"])
        arrived_team = c[newcomer].groupby("to")["min_prev"].sum()
        own = np.where(newcomer, c["min_prev"], 0)
        tot = np.array([team_total.get((tm, t - 1), np.nan) for tm in c["to"]])
        c["opportunity"] = (c["to"].map(gone).fillna(0) - (c["to"].map(arrived_team).fillna(0) - own)) / tot
        rows.append(c[["player_id", "season_start", "opportunity"]])
    return pd.concat(rows, ignore_index=True)


def add_star_left(frame, pre, regular, threshold=STAR_LEFT_PPG):
    """star_left = 1 if a player who averaged `threshold`+ points for the player's (preseason) team last season
    has been seen with another team in preseason, AND no `threshold`+ scorer from another team has joined it.
    Known before opening night; a star who is merely absent from preseason (injury, holdout) is not counted.
    "Not replaced" fitted slightly better than the plain flag (notebook 11, decision D29), and none of the
    winners' teams had brought in a 20-point scorer."""
    end = regular.sort_values("game_date").groupby(["player_id", "season_start"]).agg(team=("team_id", "last"), ppg=("pts", "mean")).reset_index()
    pre_team = pre.sort_values("game_date").groupby(["player_id", "season_start"])["team_id"].last()
    end["pre_team_next"] = [pre_team.get((p, s + 1)) for p, s in zip(end["player_id"], end["season_start"])]
    moved = end[(end["ppg"] >= threshold) & end["pre_team_next"].notna() & (end["pre_team_next"] != end["team"])]
    lost = set(zip(moved["team"], moved["season_start"] + 1))
    gained = set(zip(moved["pre_team_next"], moved["season_start"] + 1))
    f = frame.copy()
    keys = list(zip(f["team_id"], f["season_start"]))
    f["star_left_any"] = [float(k in lost) for k in keys]
    f["star_arrived"] = [float(k in gained) for k in keys]
    f["star_left"] = f["star_left_any"] * (1 - f["star_arrived"])
    return f
