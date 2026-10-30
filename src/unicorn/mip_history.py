"""Most Improved Player, 2000-01 → 2025-26: three views of each season, backtested walk-forward.

  end of previous season : last season's level, role, momentum, age (known the day the previous season ends)
  mid-season             : the race at day DAY_MID after opening night (games up to then only)
  end of season          : the full season's changes

Game logs only (usage and start rate do not exist before 2011-12), so these models are a little
simpler than notebooks 10-12. Every season is predicted by a model trained only on earlier seasons;
the scoring turning point is chosen inside each training window from earlier seasons only.
"""

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerbiostats

from unicorn.bref import all_mip_voting, attach_player_ids
from unicorn.gamelogs import BASELINE_MIN_SHARE, GAMELOG_SEASONS, build_game_table, load_game_logs, mip_candidates
from unicorn.mip import AGE, GAMELOG_DEFENSE, GAMELOG_DELTAS, RELATIVE, SECOND_YEAR, TEAM, ChoiceModel
from unicorn.raw import PROJECT_ROOT, fetch

FIRST_START, LAST_START = 2000, 2025                 # seasons predicted: 2000-01 → 2025-26
OLD_SEASONS = [f"{y}-{str(y + 1)[-2:]}" for y in range(1999, 2010)]   # 1999-00 supplies 2000-01's baselines
DAY_MID = 85
L2 = 3.0
TURN_GRID = (16, 18, 20, 22, 24)
MIN_TRAIN_SEASONS = 5

PREV_FEATURES = ["ppg_last", "mpg_last", "gspg_last", "rpg_last", "apg_last", "team_win_pct_last",
                 "momentum_game_score", "late_surge_last", "age", "second_year"]
IN_SEASON_FEATURES = GAMELOG_DELTAS + GAMELOG_DEFENSE + RELATIVE + TEAM + AGE + SECOND_YEAR + ["base_ppg"]


def season_label(y):
    return f"{y}-{str(y + 1)[-2:]}"


def load_games():
    games, _, _ = build_game_table(load_game_logs(OLD_SEASONS + GAMELOG_SEASONS))
    games["day"] = (games["game_date"] - games.groupby("season")["game_date"].transform("min")).dt.days
    return games


def player_info():
    """Age and experience (NBA seasons before this one) per player-season: bio endpoint to 2010-11, player-season table after."""
    rows = []
    for y in range(1999, 2011):
        b = next(iter(fetch(leaguedashplayerbiostats.LeagueDashPlayerBioStats, season=season_label(y)).values()))
        b.columns = b.columns.str.lower()
        rows.append(pd.DataFrame({"player_id": b["player_id"], "season_start": y, "age": b["age"],
                                  "exp": y - pd.to_numeric(b["draft_year"], errors="coerce")}))
    ps = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "player_season.parquet")
    info = pd.concat([*rows, ps[["player_id", "season_start", "age", "exp"]]], ignore_index=True)
    info = info.drop_duplicates(["player_id", "season_start"], keep="last")
    return info.assign(usg_pct=np.nan, start_rate=np.nan, def_rating=np.nan)


def voting(games):
    votes = attach_player_ids(all_mip_voting(first_year=FIRST_START + 1, last_year=LAST_START + 1), games)
    winners = {r.season: int(r.player_id) for r in votes[votes["vote_rank"] == 1].itertuples()}
    return votes, winners


def end_of_previous_frame(games, info, winners):
    """One row per (player, season y) for every player who played in y-1: what was known when y-1 ended."""
    g = games.sort_values("game_date")
    s = g.groupby(["player_id", "season_start"]).agg(
        games=("game_id", "size"), ppg=("pts", "mean"), mpg=("min", "mean"), gspg=("game_score", "mean"),
        rpg=("reb", "mean"), apg=("ast", "mean"), team=("team_id", "last"), name=("player_name", "last")).reset_index()
    half = g.groupby(["player_id", "season_start", "after_all_star"])["game_score"].mean().unstack()
    s = s.merge((half[True] - half[False]).rename("late_surge").reset_index(), on=["player_id", "season_start"], how="left")
    tg = g.drop_duplicates(["team_id", "game_id"])
    win = tg.assign(w=tg["wl"].eq("W")).groupby(["team_id", "season_start"])["w"].mean()
    s["team_win_pct"] = [win.get(k) for k in zip(s["team"], s["season_start"])]
    season_len = g.groupby("season_start").apply(lambda d: d.groupby("team_id")["game_id"].nunique().max(), include_groups=False)
    s["qualifies"] = s["games"] >= BASELINE_MIN_SHARE * s["season_start"].map(season_len)

    q = s[s["qualifies"]].sort_values("season_start")
    q = q.assign(gspg_prevq=q.groupby("player_id")["gspg"].shift())          # the qualifying season before it
    played = s[["player_id", "season_start", "name"]].sort_values("season_start")      # played in y-1
    base = pd.merge_asof(played, q.drop(columns="name").rename(columns={"season_start": "base_start"}), left_on="season_start",
                         right_on="base_start", by="player_id", direction="backward")   # latest qualifying season <= y-1
    base = base.dropna(subset=["base_start"])
    f = pd.DataFrame({"player_id": base["player_id"], "player_name": base["name"], "season_start": base["season_start"] + 1,
                      "ppg_last": base["ppg"], "mpg_last": base["mpg"], "gspg_last": base["gspg"], "rpg_last": base["rpg"],
                      "apg_last": base["apg"], "team_win_pct_last": base["team_win_pct"],
                      "momentum_game_score": (base["gspg"] - base["gspg_prevq"]).fillna(0.0),
                      "late_surge_last": base["late_surge"].fillna(0.0)})
    i = info.set_index(["player_id", "season_start"])
    prev_key = list(zip(f["player_id"], f["season_start"] - 1))
    f["age"] = [i["age"].get(k, np.nan) + 1 for k in prev_key]
    f["second_year"] = [float(i["exp"].get(k, np.nan) == 0) for k in prev_key]          # just finished his rookie season
    f["age"] = f["age"].fillna(f["age"].median())
    return _label(f[f["season_start"].between(FIRST_START, LAST_START)], winners)


def in_season_frame(games, info, winners, day=None):
    """Eligible candidates using games up to `day` days after each opener (None = the whole season)."""
    g = games if day is None else games[games["day"] <= day]
    c = mip_candidates(g, info, min_prior_seasons=1, season_stats=False)
    c = c[c["eligible"] & c["season_start"].between(FIRST_START, LAST_START)].copy()
    c["second_year"] = (c["prior_seasons"] == 1).astype(float)
    c["age"] = c["age"].fillna(c["age"].median())
    return _label(c, winners)


def _label(f, winners):
    f = f.copy()
    f["season"] = f["season_start"].map(season_label)
    f["mip"] = [winners.get(s) == p for s, p in zip(f["season"], f["player_id"])]
    return f.reset_index(drop=True)


def _with_turn(df, level_col, k):
    return df.assign(over_turn=(df[level_col] - k).clip(lower=0))


def choose_turning_point(train, features, level_col, grid=TURN_GRID, folds=5):
    """Pick the turning point by cross-validation over the training seasons only (season-grouped folds)."""
    seasons = sorted(train["season"].unique())
    groups = np.array_split(np.array(seasons), min(folds, len(seasons)))
    best, best_ll = None, -np.inf
    for k in grid:
        d = _with_turn(train, level_col, k)
        ll = 0.0
        for test_seasons in groups:
            te = d[d["season"].isin(test_seasons)]
            p = ChoiceModel(features + ["over_turn"], L2).fit(d[~d["season"].isin(test_seasons)]).predict_proba(te)
            ll += np.log(p[te["mip"]].clip(lower=1e-12)).sum()
        if ll > best_ll:
            best, best_ll = k, ll
    return best


def walk_forward(frame, features, level_col):
    """Each season from the (MIN_TRAIN_SEASONS+1)th on, predicted by a model trained only on earlier seasons."""
    seasons = sorted(frame["season"].unique())
    out, picks = [], []
    for s in seasons[MIN_TRAIN_SEASONS:]:
        train, test = frame[frame["season"] < s], frame[frame["season"] == s]
        k = choose_turning_point(train, features, level_col)
        m = ChoiceModel(features + ["over_turn"], L2).fit(_with_turn(train, level_col, k))
        p = m.predict_proba(_with_turn(test, level_col, k))
        rank = p.rank(ascending=False, method="first")
        w = test["mip"]
        out.append({"season": s, "turning point used": k, "candidates": len(test),
                    "winner's rank": int(rank[w].iloc[0]) if w.any() else np.nan,
                    "winner's chance": float(p[w].iloc[0]) if w.any() else np.nan})
        top = test.assign(chance=p, rank=rank.astype(int)).nsmallest(7, "rank")
        picks.append(top[["season", "rank", "player_id", "player_name", "chance", "mip"]])
    return pd.DataFrame(out).set_index("season"), pd.concat(picks, ignore_index=True)
