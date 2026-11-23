"""Segment 5 (rookies): one table per pool, with the 15 style measures (D57).

A pool is everyone who played in one setting: a year's summer leagues (all combined, D56), a preseason,
or a regular season (optionally split by team stint, D51). Style is the box score plus shot diet (D49 revised).

Combining leagues or games: counts are added up; rates that NBA.com gives as percentages are rebuilt from
weighted parts and divided by the summed weight (D57):
  * team-context rates (usage, assist %, offensive and defensive rebound %) are weighted by possessions;
  * shares with an exact denominator are pooled exactly: self-created makes by field goals made,
    fast-break points by points.
The same 15 rates as segment 2's play-style groups (`unicorn.style_history.STYLE`).
"""

import pandas as pd
from nba_api.stats.endpoints import leaguedashplayershotlocations, leaguedashplayerstats, leaguegamelog

from unicorn.raw import fetch
from unicorn.style_history import STYLE

# NBA.com league codes for the summer leagues (league 13 has no 2015 data; Orlando, 14, last ran before 2026)
SUMMER_LEAGUES = {"13": "California", "14": "Orlando", "15": "Las Vegas", "16": "Utah"}
SHOT_ZONE_MEASURES = ["rim_rate", "paint_non_ra_rate", "mid_rate", "corner3_share"]   # dropped in the box-score-only check (D49)
BOX_ONLY = [c for c in STYLE if c not in SHOT_ZONE_MEASURES]
ZONES = {"Restricted Area__FGA": "ra_fga", "In The Paint (Non-RA)__FGA": "paint_fga", "Mid-Range__FGA": "mid_fga",
         "Corner 3__FGA": "corner3_fga", "Above the Break 3__FGA": "atb3_fga"}
COUNTS = ["min", "fgm", "fga", "fg3a", "fta", "stl", "blk", "pf", "pts", "poss", *[z for z in ZONES.values()],
          "usg_w", "ast_w", "oreb_w", "dreb_w", "uast_w", "fb_w", "tov_w"]


def _one(season, **kw):
    """Totals for one league or season type (optionally one team), one row per player."""
    g = fetch(leaguegamelog.LeagueGameLog, season=season, player_or_team_abbreviation="P",
              **{k: v for k, v in kw.items() if k in ("league_id", "season_type_all_star", "date_to_nullable")})["LeagueGameLog"]
    dash = {k.replace("league_id", "league_id_nullable"): v for k, v in kw.items()}
    if "team_id_nullable" in dash:
        g = g[g["TEAM_ID"].astype(str) == dash["team_id_nullable"]]
    box = g.groupby("PLAYER_ID").agg(player_name=("PLAYER_NAME", "last"), games=("GAME_ID", "nunique"),
                                     **{c.lower(): (c, "sum") for c in ["MIN", "FGM", "FGA", "FG3A", "FTA", "STL", "BLK", "PF", "PTS"]})
    lds = lambda m: fetch(leaguedashplayerstats.LeagueDashPlayerStats, season=season, measure_type_detailed_defense=m,
                          per_mode_detailed="Totals", **dash)["LeagueDashPlayerStats"].set_index("PLAYER_ID")
    adv = lds("Advanced")[["POSS", "USG_PCT", "AST_PCT", "OREB_PCT", "DREB_PCT", "TM_TOV_PCT"]]
    sco = lds("Scoring")[["PCT_UAST_FGM", "PCT_PTS_FB"]]
    shots = fetch(leaguedashplayershotlocations.LeagueDashPlayerShotLocations, season=season, distance_range="By Zone",
                  per_mode_detailed="Totals", **dash)["ShotLocations"].set_index("PLAYER_ID").rename(columns=ZONES)[list(ZONES.values())]
    d = box.join(adv).join(sco).join(shots)
    d[list(ZONES.values())] = d[list(ZONES.values())].fillna(0)
    d["poss"] = d.pop("POSS")
    d["usg_w"], d["ast_w"] = d["USG_PCT"] * d["poss"], d["AST_PCT"] * d["poss"]
    d["oreb_w"], d["dreb_w"] = d["OREB_PCT"] * d["poss"], d["DREB_PCT"] * d["poss"]
    d["uast_w"], d["fb_w"] = d["PCT_UAST_FGM"] * d["fgm"], d["PCT_PTS_FB"] * d["pts"]
    d["tov_w"] = d["TM_TOV_PCT"] * d["poss"]   # for the position model (D5) only; not one of the 15 style measures
    d.index.name = "player_id"
    return d[["player_name", "games", *COUNTS]]


def rates(t):
    """The 15 style rates from pooled totals."""
    safe = lambda a, b: a / b.where(b > 0)
    return pd.DataFrame({
        "rim_rate": safe(t["ra_fga"], t["fga"]), "paint_non_ra_rate": safe(t["paint_fga"], t["fga"]),
        "mid_rate": safe(t["mid_fga"], t["fga"]), "fg3a_rate": safe(t["fg3a"], t["fga"]),
        "corner3_share": safe(t["corner3_fga"], t["fg3a"]), "fta_rate": safe(t["fta"], t["fga"]),
        "usg_pct": safe(t["usg_w"], t["poss"]), "pct_uast_fgm": safe(t["uast_w"], t["fgm"]),
        "ast_pct": safe(t["ast_w"], t["poss"]), "pct_pts_fb": safe(t["fb_w"], t["pts"]),
        "oreb_pct": safe(t["oreb_w"], t["poss"]), "dreb_pct": safe(t["dreb_w"], t["poss"]),
        "blk_per100": safe(100 * t["blk"], t["poss"]), "stl_per100": safe(100 * t["stl"], t["poss"]),
        "pf_per36": safe(36 * t["pf"], t["min"]), "tm_tov_pct": safe(t["tov_w"], t["poss"])}, index=t.index)[[*STYLE, "tm_tov_pct"]]


def _finish(parts):
    t = pd.concat(parts)
    t.index = t.index.astype(int)
    names = t.groupby(level=0)["player_name"].last()
    t = t.groupby(level=0)[["games", *COUNTS]].sum()
    t.insert(0, "player_name", names)
    return pd.concat([t, rates(t)], axis=1)


def summer_pool(season):
    """Every summer league held in `season` (e.g. "2026-27" = July 2026), combined (D56)."""
    parts = []
    for lid, name in SUMMER_LEAGUES.items():
        part = _one(season, league_id=lid)
        if len(part):
            parts.append(part.assign(leagues=name))
    leagues = pd.concat(parts)["leagues"]
    leagues = leagues.groupby(leagues.index.astype(int)).agg(", ".join)
    return _finish([p.drop(columns="leagues") for p in parts]).join(leagues)


def preseason_pool(season):
    return _finish([_one(season, season_type_all_star="Pre Season")])


def regular_pool(season, through=None):
    """A regular season, one row per player (all teams combined). `through` (a date) cuts it at that night,
    for the season in progress; the cut is part of the cache key, so a dated snapshot never changes."""
    kw = {"season_type_all_star": "Regular Season"}
    if through is not None:
        kw["date_to_nullable"] = pd.Timestamp(through).strftime("%m/%d/%Y")
    return _finish([_one(season, **kw)])


def regular_stints(season):
    """A completed regular season split by team stint (D51): one row per (player, team)."""
    g = fetch(leaguegamelog.LeagueGameLog, season=season, player_or_team_abbreviation="P",
              season_type_all_star="Regular Season")["LeagueGameLog"]
    parts = []
    for tid in sorted(g["TEAM_ID"].unique()):
        t = _finish([_one(season, season_type_all_star="Regular Season", team_id_nullable=str(tid))])
        parts.append(t.assign(team_id=tid).reset_index())
    return pd.concat(parts, ignore_index=True).set_index(["player_id", "team_id"])
