"""Derived position spectrum (decision D5).

Three estimates of a player's position on the same 1 (G) → 5 (C) scale:
  position_num    listed on that season's roster
  position_body   predicted from height and weight
  position_style  predicted from how he plays (season-relative stats only, no body measures)

Each season's models are fitted on rotation players (>= 500 min, roster-listed position)
from that season and earlier only, so the spectrum is safe for walk-forward use.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV

STYLE_FEATURES = [
    "ast_pct_z", "oreb_pct_z", "dreb_pct_z", "blk_per100_z", "stl_per100_z",
    "fg3a_rate_z", "rim_rate_z", "mid_rate_z", "paint_non_ra_rate_z", "fta_rate_z",
    "usg_pct_z", "tm_tov_pct_z", "pf_per36_z", "pct_uast_fgm_z", "pct_pts_fb_z",
]
BODY_FEATURES = ["height_in_z", "weight_lb_z"]
FIT_MIN = 500
ALPHAS = np.logspace(-2, 3, 20)


def _design(df, cols):
    # ~0.5% of rows (players with zero FGA) lack shot-profile z-scores: treat as league average
    return df[cols].fillna(0.0).to_numpy()


def _fit(train, cols):
    return RidgeCV(alphas=ALPHAS).fit(_design(train, cols), train["position_num"])


def add_position_spectrum(df, holdout=False):
    """Add position_body, position_style and the gaps between the three spectra.

    holdout=False: season t uses models fitted on seasons <= t (what's known at the end of t).
    holdout=True:  season t uses seasons < t only. Used to measure honest out-of-sample accuracy.
    """
    df = df.copy()
    fit_rows = (df["position_source"] == "roster") & (df["min"] >= FIT_MIN) & df["position_num"].notna()
    for out, cols in [("position_body", BODY_FEATURES), ("position_style", STYLE_FEATURES)]:
        df[out] = np.nan
        for season in sorted(df["season_start"].unique()):
            past = df["season_start"] < season if holdout else df["season_start"] <= season
            train = df[fit_rows & past]
            if train.empty:
                continue
            rows = df["season_start"] == season
            df.loc[rows, out] = np.clip(_fit(train, cols).predict(_design(df[rows], cols)), 1, 5)
    df["style_vs_listed"] = df["position_style"] - df["position_num"]  # >0: plays bigger than listed
    df["style_vs_body"] = df["position_style"] - df["position_body"]   # <0: big body, small style
    return df


def style_coefficients(df, season_start=None):
    """Standardized coefficients of the style model (fitted on seasons <= season_start)."""
    season_start = season_start or df["season_start"].max()
    fit_rows = ((df["position_source"] == "roster") & (df["min"] >= FIT_MIN)
                & df["position_num"].notna() & (df["season_start"] <= season_start))
    model = _fit(df[fit_rows], STYLE_FEATURES)
    return pd.Series(model.coef_, index=STYLE_FEATURES).sort_values()
