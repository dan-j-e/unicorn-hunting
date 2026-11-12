"""How a Most Improved model is scored, in one place (used by notebooks 11, 17, 18, 19 and 20).

Two tests (see the README's "Terms used throughout"):
  strict        : each season predicted by a model trained only on EARLIER seasons (skips the first `min_train`)
  leave-one-out : each season predicted by a model trained on every OTHER season

The scorecard uses the same names everywhere: winner #1, in top 3, in top 7, in top 20, median rank,
and × a blind guess (how much more chance the real winner got than an even split; geometric mean over seasons).
"""

import numpy as np
import pandas as pd

from unicorn.allstars import add_prior_allstar
from unicorn.hot_start import add_stale
from unicorn.mip import ChoiceModel
from unicorn.mip_history import IN_SEASON_FEATURES, L2, MIN_TRAIN_SEASONS, choose_turning_point, in_season_frame, with_turn

# the live race's inputs (notebook 12): box-score changes, relative change, team, age, second year, the baseline season's
# game score with a turning point (D41; on points until 12 November, D27), already an All-Star (D38), back from a lost season (D39)
LIVE_LEVEL = "base_game_score"
LIVE_TURN_CHOICES = (None, 12.5, 14, 15.5, 17, 18.5)    # same percentiles of candidates as 16-24 points; None = no turning point
LIVE_TURN = 14                                          # chosen most often in the strict test (notebook 21B); used where a fixed value is needed
LIVE_INPUTS = [c if c != "base_ppg" else LIVE_LEVEL for c in IN_SEASON_FEATURES] + ["over_turn", "prior_allstar", "stale"]
POINTS_INPUTS = IN_SEASON_FEATURES + ["over_turn", "prior_allstar", "stale"]   # the same model with the points turning point (D27 to D40)

_STRICT = {"strict", "walk_forward"}
_LOO = {"loso", "leave-one-out"}


def current_frame(games, info, winners, selections, day=None, level_col=LIVE_LEVEL, turn=LIVE_TURN):
    """Every past season's candidates at `day` days after opening night (None = season's end), with the live race's inputs.
    For the points version (D27 to D40) pass level_col="base_ppg", turn=20."""
    f = with_turn(in_season_frame(games, info, winners, day=day), level_col, turn)
    return add_stale(add_prior_allstar(f, selections))


def winner_ranks(frame, features=None, l2=L2, scheme="loso", min_train=MIN_TRAIN_SEASONS, rule=None):
    """One row per season that has an eventual winner in the pool: his rank, his chance, the pool size,
    our top pick and our top 7. `rule` ranks by a single column instead of a model (no chance is given)."""
    if scheme not in _STRICT | _LOO:
        raise ValueError(f"unknown scheme {scheme!r}")
    strict = scheme in _STRICT
    out = {}
    for i, s in enumerate(sorted(frame["season"].unique())):
        if strict and i < min_train:
            continue
        te = frame[frame["season"] == s]
        if not te["mip"].any():
            continue
        if rule is not None:
            p, score = None, te[rule]
        else:
            tr = frame[frame["season"] < s] if strict else frame[frame["season"] != s]
            p = score = ChoiceModel(features, l2).fit(tr).predict_proba(te)
        out[s] = {"rank": int(score.rank(ascending=False, method="min")[te["mip"]].iloc[0]),
                  "p": np.nan if p is None else p[te["mip"]].iloc[0], "n": len(te),
                  "top_pick": te.loc[score.idxmax(), "player_name"], "top7": list(te.loc[score.nlargest(7).index, "player_id"])}
    return pd.DataFrame(out).T


def scorecard(r):
    """Summarise winner_ranks: how often the winner was #1 / top 3 / top 7 / top 20, his median rank, and × a blind guess."""
    rk = r["rank"].astype(float)
    p, n = r["p"].astype(float), r["n"].astype(float)
    return {"seasons": len(r), "winner #1": int((rk == 1).sum()), "in top 3": int((rk <= 3).sum()), "in top 7": int((rk <= 7).sum()),
            "in top 20": int((rk <= 20).sum()), "median rank": float(rk.median()),
            "× a blind guess": float(np.exp(np.mean(np.log(p * n)))) if p.notna().all() and len(r) else np.nan}


def turning_point_ranks(frame, features, level_col, grid, l2=L2, scheme="strict", min_train=MIN_TRAIN_SEASONS):
    """Like winner_ranks, but with a turning point on `level_col` chosen inside each training set only
    (season-grouped cross-validation, as the live race does; D32). `grid` may include None (no turning point).
    The chosen turning point is returned for each season in column `k`."""
    if scheme not in _STRICT | _LOO:
        raise ValueError(f"unknown scheme {scheme!r}")
    strict = scheme in _STRICT
    out = {}
    for i, s in enumerate(sorted(frame["season"].unique())):
        if strict and i < min_train:
            continue
        te = frame[frame["season"] == s]
        if not te["mip"].any():
            continue
        tr = frame[frame["season"] < s] if strict else frame[frame["season"] != s]
        k = choose_turning_point(tr, features, level_col, grid=grid)
        m = ChoiceModel(features + ["over_turn"], l2).fit(with_turn(tr, level_col, k))
        p = m.predict_proba(with_turn(te, level_col, k))
        out[s] = {"rank": int(p.rank(ascending=False, method="min")[te["mip"]].iloc[0]), "p": p[te["mip"]].iloc[0], "n": len(te),
                  "top_pick": te.loc[p.idxmax(), "player_name"], "top7": list(te.loc[p.nlargest(7).index, "player_id"]), "k": k}
    return pd.DataFrame(out).T
