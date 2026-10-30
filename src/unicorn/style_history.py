"""Playing-style measures on 3-season rolling windows, 2000-01 → 2025-26 (notebook 13E).

A window ending in season y pools a player's totals over seasons y-2, y-1 and y (whichever he played),
then turns them into the same 15 style rates as notebook 13. Pooling totals (not averaging three rates)
weights each season by how much he played. Raw values: no era adjustment.
"""

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayershotlocations, leaguedashplayerstats

from unicorn.raw import fetch

FIRST_DATA, FIRST_WINDOW, LAST = 1998, 2000, 2025      # 1998-99 and 1999-00 feed the first window (ending 2000-01)
WINDOW = 3
MIN_MINUTES_LAST = 500                                 # played 500+ minutes in the window's last season
STYLE = ["rim_rate", "paint_non_ra_rate", "mid_rate", "fg3a_rate", "corner3_share", "fta_rate", "usg_pct", "pct_uast_fgm",
         "ast_pct", "pct_pts_fb", "oreb_pct", "dreb_pct", "blk_per100", "stl_per100", "pf_per36"]


def season_label(y):
    return f"{y}-{str(y + 1)[-2:]}"


def _lds(season, measure):
    return fetch(leaguedashplayerstats.LeagueDashPlayerStats, season=season, season_type_all_star="Regular Season",
                 measure_type_detailed_defense=measure, per_mode_detailed="Totals")["LeagueDashPlayerStats"]


def season_totals(y):
    """Totals needed for the style rates, one row per player for season y."""
    s = season_label(y)
    base = _lds(s, "Base")[["PLAYER_ID", "PLAYER_NAME", "MIN", "FGM", "FGA", "FG3A", "FTA", "STL", "BLK", "PF", "PTS"]]
    adv = _lds(s, "Advanced")[["PLAYER_ID", "POSS", "USG_PCT", "AST_PCT", "OREB_PCT", "DREB_PCT"]]
    sco = _lds(s, "Scoring")[["PLAYER_ID", "PCT_UAST_FGM", "PCT_PTS_FB"]]
    shots = fetch(leaguedashplayershotlocations.LeagueDashPlayerShotLocations, season=s, season_type_all_star="Regular Season",
                  distance_range="By Zone", per_mode_detailed="Totals")["ShotLocations"]
    zones = {"Restricted Area__FGA": "RA_FGA", "In The Paint (Non-RA)__FGA": "PAINT_FGA", "Mid-Range__FGA": "MID_FGA",
             "Corner 3__FGA": "CORNER3_FGA", "Above the Break 3__FGA": "ATB3_FGA"}
    shots = shots.rename(columns=zones)[["PLAYER_ID", *zones.values()]]
    d = base.merge(adv, on="PLAYER_ID", how="left").merge(sco, on="PLAYER_ID", how="left").merge(shots, on="PLAYER_ID", how="left")
    d[list(zones.values())] = d[list(zones.values())].fillna(0)
    # rates the endpoints give per season -> volume-weighted parts, so they can be pooled over a window
    d["USG_W"] = d["USG_PCT"] * d["POSS"]
    d["AST_W"] = d["AST_PCT"] * d["MIN"]
    d["OREB_W"] = d["OREB_PCT"] * d["MIN"]
    d["DREB_W"] = d["DREB_PCT"] * d["MIN"]
    d["UAST_W"] = d["PCT_UAST_FGM"] * d["FGM"]
    d["FB_W"] = d["PCT_PTS_FB"] * d["PTS"]
    d.columns = d.columns.str.lower()
    return d.assign(season_start=y)


def load_totals(first=FIRST_DATA, last=LAST):
    return pd.concat([season_totals(y) for y in range(first, last + 1)], ignore_index=True)


def _rates(t):
    safe = lambda a, b: a / b.where(b > 0)
    return pd.DataFrame({
        "rim_rate": safe(t["ra_fga"], t["fga"]), "paint_non_ra_rate": safe(t["paint_fga"], t["fga"]),
        "mid_rate": safe(t["mid_fga"], t["fga"]), "fg3a_rate": safe(t["fg3a"], t["fga"]),
        "corner3_share": safe(t["corner3_fga"], t["fg3a"]), "fta_rate": safe(t["fta"], t["fga"]),
        "usg_pct": safe(t["usg_w"], t["poss"]), "pct_uast_fgm": safe(t["uast_w"], t["fgm"]),
        "ast_pct": safe(t["ast_w"], t["min"]), "pct_pts_fb": safe(t["fb_w"], t["pts"]),
        "oreb_pct": safe(t["oreb_w"], t["min"]), "dreb_pct": safe(t["dreb_w"], t["min"]),
        "blk_per100": safe(100 * t["blk"], t["poss"]), "stl_per100": safe(100 * t["stl"], t["poss"]),
        "pf_per36": safe(36 * t["pf"], t["min"])}, index=t.index)


POOL = ["min", "fgm", "fga", "fg3a", "fta", "stl", "blk", "pf", "pts", "poss", "ra_fga", "paint_fga", "mid_fga", "corner3_fga",
        "usg_w", "ast_w", "oreb_w", "dreb_w", "uast_w", "fb_w"]


def rolling_windows(totals, window=WINDOW, first=FIRST_WINDOW, last=LAST, min_minutes_last=MIN_MINUTES_LAST):
    """One row per (player, window ending y): style rates from totals pooled over seasons y-window+1..y."""
    t = totals.groupby(["player_id", "season_start"], as_index=False).agg({**{c: "sum" for c in POOL}, "player_name": "last"})
    rows = []
    for y in range(first, last + 1):
        last_season = t[(t["season_start"] == y) & (t["min"] >= min_minutes_last)][["player_id", "player_name"]]
        w = t[t["season_start"].between(y - window + 1, y) & t["player_id"].isin(last_season["player_id"])]
        pooled = w.groupby("player_id")[POOL].sum()
        pooled["seasons_in_window"] = w.groupby("player_id").size()
        pooled = pooled.join(last_season.set_index("player_id")).reset_index()
        rows.append(pooled.assign(window_end=y, window=f"{season_label(y - window + 1)} → {season_label(y)}"))
    out = pd.concat(rows, ignore_index=True)
    return pd.concat([out, _rates(out)], axis=1)
