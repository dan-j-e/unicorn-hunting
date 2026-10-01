"""Data dictionary for player_season: the role of every column.

Roles
-----
identifier  : keys and labels, never modelled
context     : describes circumstances (team, sample, provenance); used for filtering/stratifying
reliability : sample-size denominators; used for thresholds and shrinkage weights
total       : raw counting stats; inputs to derived rates, not features themselves
feature     : candidate predictor (a rate or physical/biographical attribute)
impact      : all-in-one / on-off measures; a feature when lagged, a candidate outcome when future
redundant   : measures the same thing as a kept feature (|Spearman| >= ~0.9, step 2C)

The feature/redundant split comes from notebook 02 step 2C (redundancy estimated on
2011-12 → 2016-17, stable in 2019-20 → 2025-26). Rule: when undecided, keep the
column as a feature. Final selection happens inside each walk-forward window.
"""

import pandas as pd

ROLES = {
    "identifier": ["player_id", "player_name", "season", "season_start", "team_id", "team_abbreviation"],
    "context": ["team_count", "w", "l", "pace", "country", "college", "birth_date", "undrafted",
                "position_listed", "position", "position_source", "age_source", "draft_year", "draft_round",
                "draft_number"],
    "reliability": ["gp", "gs", "min", "poss", "fga", "fg3a", "fta", "ra_fga"],
    "total": ["fgm", "fg3m", "ftm", "oreb", "dreb", "reb", "ast", "tov", "stl", "blk", "blka", "pf", "pfd",
              "pts", "dd2", "td3", "pts_paint", "pts_2nd_chance", "pts_fb", "pts_off_tov",
              "ra_fgm", "paint_non_ra_fgm", "paint_non_ra_fga", "mid_fgm", "mid_fga", "corner3_fgm",
              "corner3_fga", "atb3_fgm", "atb3_fga", "backcourt_fgm", "backcourt_fga"],
    "feature": [
        # body & biography
        "age", "exp", "height_in", "weight_lb", "position_num", "draft_pick_filled",
        # role & scoring volume (pts_per36 kept alongside usg_pct + ts_pct; decide later)
        "min_per_game", "start_rate", "usg_pct", "pts_per36",
        # scoring efficiency
        "ts_pct", "fg3_pct", "ft_pct", "rim_fg_pct",
        # shot profile
        "fg3a_rate", "fta_rate", "fta_per36", "rim_rate", "paint_non_ra_rate", "mid_rate", "corner3_share",
        "pct_uast_fgm", "pct_pts_fb",
        # playmaking & ball security
        "ast_pct", "tm_tov_pct",
        # rebounding
        "oreb_pct", "dreb_pct",
        # defensive activity & fouling
        "stl_per100", "blk_per100", "pf_per36",
    ],
    "impact": ["pie", "net_rating", "off_rating", "def_rating", "def_ws", "plus_minus"],
    "redundant": {
        # column: (kept feature it duplicates, early-window Spearman rho)
        "efg_pct": ("ts_pct", 0.91), "fg_pct": ("ts_pct", None),
        "fga_per36": ("usg_pct", 0.96),
        "pct_fga": ("usg_pct", 0.97), "pct_pts": ("usg_pct", 0.95), "pct_fta": ("fta_rate", None),
        "pfd_per36": ("fta_rate", 0.81),
        "fg3a_per36": ("fg3a_rate", 0.93), "pct_pts_paint": ("rim_rate", 0.92),
        "ast_per36": ("ast_pct", 0.99), "ast_ratio": ("ast_pct", 0.87), "ast_tov": ("ast_pct / tm_tov_pct", 0.87),
        "pct_ast": ("ast_pct", None), "tov_per36": ("tm_tov_pct", None),
        "reb_pct": ("oreb_pct + dreb_pct", 0.97), "reb_per36": ("oreb_pct + dreb_pct", 0.97),
        "oreb_per36": ("oreb_pct", None), "dreb_per36": ("dreb_pct", None), "pct_reb": ("reb_pct", None),
        "pct_stl": ("stl_per100", 0.94), "stl_per36": ("stl_per100", None),
        "pct_blk": ("blk_per100", 0.98), "blk_per36": ("blk_per100", None),
        "pct_tov": ("tm_tov_pct", None), "pct_uast_2pm": ("pct_uast_fgm", None),
        "pct_uast_3pm": ("pct_uast_fgm", None), "pct_pts_2pt_mr": ("mid_rate", None),
    },
}


# Columns created by unicorn.features, recognised by suffix.
TRANSFORM_SUFFIXES = {"_shr": "shrunk", "_prior_n": "reliability", "_z": "season_relative", "_pctl": "season_relative"}

# Features that get season-relative versions: everything except attributes that are
# already comparable across seasons (age, experience, draft slot, position scale),
# plus shrunk percentages and rate-type impact measures.
NOT_RELATIVE = {"age", "exp", "draft_pick_filled", "position_num"}


def relative_columns():
    shrunk = ["fg3_pct_shr", "ft_pct_shr", "rim_fg_pct_shr", "ts_pct_shr"]
    impact_rates = ["pie", "net_rating", "off_rating", "def_rating"]
    return [c for c in ROLES["feature"] if c not in NOT_RELATIVE] + shrunk + impact_rates


def dictionary(df):
    """One row per column of df with its role (and, for redundant columns, what it duplicates)."""
    rows = []
    for role, cols in ROLES.items():
        for c in cols:
            dup, rho = cols[c] if role == "redundant" else (None, None)
            rows.append({"column": c, "role": role, "duplicates": dup, "rho": rho})
    # Columns added by unicorn.features (only present in the features table)
    if "prior_group" in df.columns:
        rows.append({"column": "prior_group", "role": "context", "duplicates": None, "rho": None})
    for c in df.columns:
        role = next((r for s, r in TRANSFORM_SUFFIXES.items() if c.endswith(s)), None)
        if role:
            rows.append({"column": c, "role": role, "duplicates": None, "rho": None})
    out = pd.DataFrame(rows)
    unassigned = sorted(set(df.columns) - set(out["column"]))
    out = pd.concat([out, pd.DataFrame({"column": unassigned, "role": "UNASSIGNED"})], ignore_index=True)
    out["in_table"] = out["column"].isin(df.columns)
    return out


def features():
    return list(ROLES["feature"])
