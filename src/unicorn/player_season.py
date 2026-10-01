"""Build the consolidated player-season tables from the raw cache.

One row per (player_id, season): traded players are already consolidated by
LeagueDashPlayerStats (decision D1). No rows are dropped for low minutes;
reliability columns (min, poss, fga, fta, fg3a) are kept for later weighting.
"""

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import (
    commonteamroster,
    drafthistory,
    leaguedashplayerbiostats,
    leaguedashplayershotlocations,
    leaguedashplayerstats,
)
from nba_api.stats.static import teams

from unicorn.download import SEASONS
from unicorn.raw import fetch

AGE_REFERENCE = "02-01"  # exact age on Feb 1 of the season (mid-season convention)

# Columns kept from each measure type, renamed to snake_case.
# Percentages are NOT taken from Base: they are recomputed from makes/attempts so 0/0 -> NaN.
BASE_COLS = ["PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION", "TEAM_COUNT", "AGE",
             "GP", "W", "L", "MIN", "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA",
             "OREB", "DREB", "REB", "AST", "TOV", "STL", "BLK", "BLKA", "PF", "PFD", "PTS",
             "PLUS_MINUS", "DD2", "TD3"]
ADVANCED_COLS = ["POSS", "PACE", "USG_PCT", "AST_PCT", "AST_RATIO", "TM_TOV_PCT",
                 "OREB_PCT", "DREB_PCT", "REB_PCT", "OFF_RATING", "DEF_RATING", "NET_RATING", "PIE"]
USAGE_COLS = ["PCT_FGA", "PCT_FTA", "PCT_PTS", "PCT_AST", "PCT_REB", "PCT_STL", "PCT_BLK", "PCT_TOV"]
SCORING_COLS = ["PCT_UAST_FGM", "PCT_UAST_2PM", "PCT_UAST_3PM", "PCT_PTS_PAINT", "PCT_PTS_FB", "PCT_PTS_2PT_MR"]
MISC_COLS = ["PTS_PAINT", "PTS_2ND_CHANCE", "PTS_FB", "PTS_OFF_TOV"]
DEFENSE_COLS = ["DEF_WS"]
SHOT_ZONES = {"Restricted Area": "ra", "In The Paint (Non-RA)": "paint_non_ra", "Mid-Range": "mid",
              "Corner 3": "corner3", "Above the Break 3": "atb3", "Backcourt": "backcourt"}
PER36 = ["pts", "reb", "oreb", "dreb", "ast", "stl", "blk", "tov", "fga", "fg3a", "fta"]

# Listed position -> numeric scale for the derived-position work (D5). G=1 … C=5.
POSITION_SCALE = {"G": 1.0, "G-F": 2.0, "F-G": 2.5, "F": 3.0, "F-C": 3.5, "C-F": 4.0, "C": 5.0}


def _lds(season, season_type, measure, **extra):
    return fetch(leaguedashplayerstats.LeagueDashPlayerStats, season=season,
                 season_type_all_star=season_type, measure_type_detailed_defense=measure,
                 per_mode_detailed="Totals", **extra)["LeagueDashPlayerStats"]


def _join(left, right, cols, how="left"):
    return left.merge(right[["PLAYER_ID", *cols]], on="PLAYER_ID", how=how, validate="one_to_one")


def _stats_one_season(season, season_type):
    df = _lds(season, season_type, "Base")[BASE_COLS]
    df = _join(df, _lds(season, season_type, "Advanced"), ADVANCED_COLS)
    df = _join(df, _lds(season, season_type, "Usage"), USAGE_COLS)
    df = _join(df, _lds(season, season_type, "Scoring"), SCORING_COLS)
    df = _join(df, _lds(season, season_type, "Misc"), MISC_COLS)
    df = _join(df, _lds(season, season_type, "Defense"), DEFENSE_COLS)

    starts = _lds(season, season_type, "Base", starter_bench_nullable="Starters")
    df = _join(df, starts.rename(columns={"GP": "GS"}), ["GS"])
    df["GS"] = df["GS"].fillna(0).astype(int)  # absent from the Starters query = 0 starts

    shots = fetch(leaguedashplayershotlocations.LeagueDashPlayerShotLocations, season=season,
                  season_type_all_star=season_type, distance_range="By Zone",
                  per_mode_detailed="Totals")["ShotLocations"]
    zone_cols = {f"{zone}__{stat}": f"{short.upper()}_{stat}" for zone, short in SHOT_ZONES.items() for stat in ["FGM", "FGA"]}
    shots = shots.rename(columns=zone_cols)
    df = _join(df, shots, list(zone_cols.values()))
    df[list(zone_cols.values())] = df[list(zone_cols.values())].fillna(0)  # missing = no attempts

    df.insert(1, "SEASON", season)
    return df


def _bio_one_season(season):
    bio = fetch(leaguedashplayerbiostats.LeagueDashPlayerBioStats, season=season,
                per_mode_simple="Totals")["LeagueDashPlayerBioStats"]
    # Draft fields are NOT taken from bio: it appears to match draft records by name
    # (e.g. Walker Russell Jr. carries his father's 1982 pick). See _add_draft.
    bio = bio[["PLAYER_ID", "PLAYER_HEIGHT_INCHES", "PLAYER_WEIGHT", "COUNTRY", "COLLEGE"]].copy()
    bio["PLAYER_WEIGHT"] = pd.to_numeric(bio["PLAYER_WEIGHT"], errors="coerce")
    return bio.rename(columns={"PLAYER_HEIGHT_INCHES": "HEIGHT_IN", "PLAYER_WEIGHT": "WEIGHT_LB"})


def _add_draft(df):
    """Draft year/round/pick from DraftHistory, keyed on player ID. Absent = undrafted."""
    dh = fetch(drafthistory.DraftHistory)["DraftHistory"]
    # A handful of historical players were drafted more than once; the last draft is the binding one.
    dh = dh.sort_values("SEASON").drop_duplicates("PERSON_ID", keep="last")
    dh = dh.rename(columns={"PERSON_ID": "PLAYER_ID", "SEASON": "DRAFT_YEAR",
                            "ROUND_NUMBER": "DRAFT_ROUND", "OVERALL_PICK": "DRAFT_NUMBER"})
    dh["DRAFT_YEAR"] = dh["DRAFT_YEAR"].astype(int)
    df = df.merge(dh[["PLAYER_ID", "DRAFT_YEAR", "DRAFT_ROUND", "DRAFT_NUMBER"]],
                  on="PLAYER_ID", how="left", validate="many_to_one")
    df["UNDRAFTED"] = df["DRAFT_NUMBER"].isna()
    return df


def load_rosters():
    """All roster snapshots, one row per (season, player). Coaches table excluded."""
    frames = []
    for season in SEASONS:
        for team in teams.get_teams():
            r = fetch(commonteamroster.CommonTeamRoster, team_id=team["id"], season=season)["CommonTeamRoster"]
            frames.append(r.assign(SEASON=season))
    ros = pd.concat(frames, ignore_index=True)
    ros["POSITION"] = ros["POSITION"].replace("", np.nan)
    ros["BIRTH_DATE"] = pd.to_datetime(ros["BIRTH_DATE"], format="%b %d, %Y")
    ros["EXP"] = pd.to_numeric(ros["EXP"].replace("R", "0"), errors="coerce")
    # A player can appear on two snapshot rosters (seen once, 2015-16); keep one deterministically.
    return ros.sort_values(["SEASON", "PLAYER_ID", "TeamID"]).drop_duplicates(["SEASON", "PLAYER_ID"])


def _add_listed_position(df, rosters):
    pos = rosters[["SEASON", "PLAYER_ID", "POSITION", "EXP"]]
    df = df.merge(pos, on=["SEASON", "PLAYER_ID"], how="left", validate="one_to_one")
    df = df.rename(columns={"POSITION": "POSITION_LISTED"})
    # Fill gaps ONLY from the player's most recent earlier season (never later -> no leakage).
    df = df.sort_values(["PLAYER_ID", "SEASON"])
    df["POSITION"] = df.groupby("PLAYER_ID")["POSITION_LISTED"].ffill()
    df["POSITION_SOURCE"] = np.select(
        [df["POSITION_LISTED"].notna(), df["POSITION"].notna()], ["roster", "prior_season"], "missing")
    df["POSITION_NUM"] = df["POSITION"].map(POSITION_SCALE)
    return df


def _add_age(df, rosters):
    # Birth date is a fixed fact, so taking it from any season's roster is not leakage.
    birth = rosters.dropna(subset=["BIRTH_DATE"]).drop_duplicates("PLAYER_ID").set_index("PLAYER_ID")["BIRTH_DATE"]
    df["BIRTH_DATE"] = df["PLAYER_ID"].map(birth)
    ref = pd.to_datetime(df["SEASON"].str[:4].astype(int).add(1).astype(str) + "-" + AGE_REFERENCE)
    exact = (ref - df["BIRTH_DATE"]).dt.days / 365.25
    df["AGE_SOURCE"] = np.where(exact.notna(), "birth_date", "nba_integer")
    df["AGE"] = exact.fillna(df["AGE"])  # fallback: NBA's integer age
    return df


def _add_derived(df):
    def safe(num, den):
        return np.where(den > 0, num / den.where(den > 0), np.nan)

    df["FG_PCT"] = safe(df["FGM"], df["FGA"])
    df["FG3_PCT"] = safe(df["FG3M"], df["FG3A"])
    df["FT_PCT"] = safe(df["FTM"], df["FTA"])
    df["EFG_PCT"] = safe(df["FGM"] + 0.5 * df["FG3M"], df["FGA"])
    df["TS_PCT"] = safe(df["PTS"], 2 * (df["FGA"] + 0.44 * df["FTA"]))
    df["FG3A_RATE"] = safe(df["FG3A"], df["FGA"])
    df["FTA_RATE"] = safe(df["FTA"], df["FGA"])
    df["RIM_RATE"] = safe(df["RA_FGA"], df["FGA"])
    df["MIN_PER_GAME"] = safe(df["MIN"], df["GP"])
    df["START_RATE"] = safe(df["GS"], df["GP"])
    for stat in PER36:
        df[f"{stat.upper()}_PER36"] = safe(36 * df[stat.upper()], df["MIN"])
    return df


def build_player_seasons(season_type="Regular Season"):
    """Clean player-season table. Bio/position/age are added for the regular season only."""
    df = pd.concat([_stats_one_season(s, season_type) for s in SEASONS], ignore_index=True)

    if season_type == "Regular Season":
        bio = pd.concat([_bio_one_season(s).assign(SEASON=s) for s in SEASONS], ignore_index=True)
        df = df.merge(bio, on=["SEASON", "PLAYER_ID"], how="left", validate="one_to_one")
        df = _add_draft(df)
        rosters = load_rosters()
        df = _add_listed_position(df, rosters)
        df = _add_age(df, rosters)

    df = _add_derived(df)
    df["SEASON_START"] = df["SEASON"].str[:4].astype(int)
    df.columns = df.columns.str.lower()
    return df.sort_values(["season", "player_id"]).reset_index(drop=True)

