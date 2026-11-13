"""Do scoring leaps last? The blip test (decision D33), applied to every big leap since 2000-01.

A leap: a season (y) at least MIN_LEAP points a game above the season before (y-1).
Share of the leap kept, at any later point = (points a game then - points in y-1) / (points in y - points in y-1).
  real        : REAL or more kept
  partly real : BLIP to REAL
  blip        : under BLIP
  no verdict  : fewer than MIN_GAMES games at that point

Shown alongside, never deciding (D46): the same share and verdicts on game score, for the same leaps
(chosen on points). A game-score leap under SMALL_GAME_SCORE_LEAP makes its share unstable, so it is marked.
"""

import numpy as np
import pandas as pd

REAL, BLIP, MIN_GAMES = 0.80, 0.50, 25
MIN_LEAP, BIG_LEAP = 3.0, 5.0            # every voted leap of 3+ points; every leap of 5+ points, voted or not
MIN_GAMES_BEFORE, MIN_GAMES_LEAP = 20, 40
SMALL_GAME_SCORE_LEAP = 2.0            # game-score leaps below this are marked (D46)


def verdict(share, games):
    if pd.isna(share) or pd.isna(games) or games < MIN_GAMES:
        return "no verdict"
    return "real" if share >= REAL else ("partly real" if share >= BLIP else "blip")


def leap_table(games, votes, winners, first=2000, last=2024):
    """One row per leap season y (first..last): scoring before, in the leap, at the next All-Star break,
    over the next full season and two seasons later, with the verdict at each point."""
    full = games.groupby(["player_id", "season_start"]).agg(
        ppg=("pts", "mean"), gp=("game_id", "size"), mins=("min", "sum"), pts=("pts", "sum"), name=("player_name", "last"),
        gs=("game_score", "mean"))
    pre = games[~games["after_all_star"]].groupby(["player_id", "season_start"]).agg(
        ppg_b=("pts", "mean"), gp_b=("game_id", "size"), min_b=("min", "sum"), pts_b=("pts", "sum"), gs_b=("game_score", "mean"))
    S = full.join(pre)
    get = lambda pid, y, col: S[col].get((pid, y), np.nan)
    vote_rank = votes.dropna(subset=["player_id"]).set_index(["season", "player_id"])["vote_rank"]

    rows = []
    for (pid, y), r in S.iterrows():
        if not first <= y <= last:
            continue
        before = get(pid, y - 1, "ppg")
        if pd.isna(before) or get(pid, y - 1, "gp") < MIN_GAMES_BEFORE or r["gp"] < MIN_GAMES_LEAP:
            continue
        leap = r["ppg"] - before
        season = f"{y}-{str(y + 1)[-2:]}"
        vr = vote_rank.get((season, pid), np.nan)
        if leap < MIN_LEAP or (leap < BIG_LEAP and pd.isna(vr)):
            continue
        kept = lambda v: (v - before) / leap
        gs_before = get(pid, y - 1, "gs")
        gs_leap = r["gs"] - gs_before
        gs_kept = lambda v: (v - gs_before) / gs_leap
        rows.append({"player_id": pid, "player": r["name"], "season": season, "vote rank": vr, "winner": winners.get(season) == pid,
                     "points before": before, "points in the leap": r["ppg"], "leap": leap,
                     "kept at the break": kept(get(pid, y + 1, "ppg_b")), "games by the break": get(pid, y + 1, "gp_b"),
                     "kept next season": kept(get(pid, y + 1, "ppg")), "games next season": get(pid, y + 1, "gp"),
                     "kept two seasons on": kept(get(pid, y + 2, "ppg")), "games two seasons on": get(pid, y + 2, "gp"),
                     "per 36 kept at the break": (get(pid, y + 1, "pts_b") / get(pid, y + 1, "min_b")) / (r["pts"] / r["mins"]),
                     "game score before": gs_before, "game score in the leap": r["gs"], "game-score leap": gs_leap,
                     "small game-score leap": gs_leap < SMALL_GAME_SCORE_LEAP,
                     "game score kept at the break": gs_kept(get(pid, y + 1, "gs_b")),
                     "game score kept next season": gs_kept(get(pid, y + 1, "gs")),
                     "game score kept two seasons on": gs_kept(get(pid, y + 2, "gs"))})
    L = pd.DataFrame(rows)
    for point in ["at the break", "next season", "two seasons on"]:
        games_col = "games by the break" if point == "at the break" else f"games {point}"
        L[f"verdict {point}"] = [verdict(s, g) for s, g in zip(L[f"kept {point}"], L[games_col])]
        L[f"game-score verdict {point}"] = [verdict(s, g) for s, g in zip(L[f"game score kept {point}"], L[games_col])]
    return L.sort_values(["season", "leap"], ascending=[True, False]).reset_index(drop=True)
