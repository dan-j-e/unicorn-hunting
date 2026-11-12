"""The live 2026-27 Most Improved race: the game table and the candidates on any day (notebooks 12 and 17).

`race(day)` gives every season's eligible candidates using only games up to `day` days after that season's
opener, so past seasons cut at the same day can train the model for today.
"""

import pandas as pd
from nba_api.stats.endpoints import leaguegamelog

from unicorn.allstars import add_prior_allstar
from unicorn.gamelogs import BASELINE_MIN_SHARE, GAMELOG_SEASONS, build_game_table, load_game_logs, mip_candidates
from unicorn.hot_start import add_stale
from unicorn.labels import MIP_WINNERS
from unicorn.raw import PROJECT_ROOT, fetch

LIVE, LIVE_START = "2026-27", 2026
FIRST_SEASON = 2011          # past seasons used to train the live race (game logs from 2010-11 give 2011-12's baselines)


def live_games(refresh=False, baseline_min_share=BASELINE_MIN_SHARE):
    """Game logs 2010-11 → today with `day` = days after each season's opener. refresh=True downloads the newest live games.
    baseline_min_share=0.0 gives the original baseline (simply the previous season, before D22), for notebook 19's early stages."""
    if refresh:
        fetch(leaguegamelog.LeagueGameLog, refresh=True, season=LIVE, player_or_team_abbreviation="P", season_type_all_star="Regular Season")
    games, _, _ = build_game_table(load_game_logs(GAMELOG_SEASONS + [LIVE]), baseline_min_share=baseline_min_share)
    games["day"] = (games["game_date"] - games.groupby("season")["game_date"].transform("min")).dt.days
    return games


def player_table_with_live_season(ps=None):
    """The player-season table plus a 2026-27 row per player: age and experience rolled forward from his latest season."""
    if ps is None:
        ps = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "player_season.parquet")
    latest = ps[ps["season_start"] < LIVE_START].sort_values("season_start").groupby("player_id").tail(1)
    gap = LIVE_START - latest["season_start"]
    return pd.concat([ps, latest[["player_id"]].assign(season_start=LIVE_START, age=latest["age"] + gap, exp=latest["exp"] + gap)],
                     ignore_index=True)


def race(games, ps_live, day, selections):
    """Eligible candidates in every season from 2011-12, using only games up to `day` days after that season's opener.
    Previous winners stay in the pool (flagged); already an All-Star (D38) and back from a lost season (D39) are added."""
    first_win = {pid: int(s[:4]) for s, pid in sorted(MIP_WINNERS.items(), reverse=True)}
    c = mip_candidates(games[games["day"] <= day], ps_live, min_prior_seasons=1, season_stats=False)
    c["second_year"] = (c["prior_seasons"] == 1).astype(float)
    c["mip"] = [MIP_WINNERS.get(s) == p for s, p in zip(c["season"], c["player_id"])]
    c["previous_winner"] = [first_win.get(p, 9999) < y for p, y in zip(c["player_id"], c["season_start"])]
    c = add_stale(add_prior_allstar(c, selections))
    return c[c["eligible"] & (c["season_start"] >= FIRST_SEASON)].reset_index(drop=True)
