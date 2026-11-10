"""Inputs for the 'Ty Jerome effect' (notebook 18, D39): should the model trust a hot start less?

  older_jump   : the early points jump, counted only for players aged 27 or older (A)
  age_x_jump   : the same idea on a smooth scale: (age - 26) x points jump, floored at 0 (A, variant)
  stale        : 1 if the baseline season is older than last season (last season was injury-shortened) (B)
  head_start   : how much of the jump already showed last season, when last season was skipped as the
                 baseline but had 10+ games: last season's points - baseline points (B)
  games_share  : games played / his team's games so far (C)

All use only games up to the day in question, plus earlier seasons.
"""

import numpy as np
import pandas as pd

OLDER_AGE = 27
HEAD_START_MIN_GAMES = 10


def add_hot_start_inputs(frame, games, day=None):
    """frame: candidates from mip_candidates (one row per player-season); games: game logs with a 'day' column."""
    f = frame.copy()
    f["older_jump"] = np.where(f["age"] >= OLDER_AGE, f["ppg_delta"], 0.0)
    f["age_x_jump"] = (f["age"] - (OLDER_AGE - 1)).clip(lower=0) * f["ppg_delta"]
    season = games.groupby(["player_id", "season_start"]).agg(prev_games=("game_id", "size"), prev_ppg=("pts", "mean"))
    prev = season.reindex(list(zip(f["player_id"], f["season_start"] - 1)))
    f["stale"] = (f["base_season_start"] < f["season_start"] - 1).astype(float)
    usable = (f["stale"] == 1) & (prev["prev_games"].to_numpy() >= HEAD_START_MIN_GAMES)
    f["head_start"] = np.where(usable, prev["prev_ppg"].to_numpy() - f["base_ppg"], 0.0)
    g = games if day is None else games[games["day"] <= day]
    team_games = g.drop_duplicates(["team_id", "game_id"]).groupby(["team_id", "season_start"])["game_id"].nunique()
    f["games_share"] = f["games"] / pd.Series(list(zip(f["team_id"], f["season_start"]))).map(team_games).to_numpy()
    return f


def add_stale(frame):
    """stale = 1 if the baseline season is older than last season (last season was lost or injury-shortened; D39).
    Works on any frame with season_start and base_season_start (live race, preseason, history)."""
    return frame.assign(stale=(frame["base_season_start"] < frame["season_start"] - 1).astype(float))
