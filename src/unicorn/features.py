"""Player-season feature transforms: reliability shrinkage and season-relative scaling.

Both transforms use only data from the same season, which is fully known at the end
of that season, so they are safe for end-of-season walk-forward predictions.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import betaln

# Shooting percentages to shrink: name -> (successes, trials) as functions of the frame.
# TS% is not strictly binomial (successes = PTS/2 over true-shooting attempts); treated as
# a quasi-binomial, which is the standard practical approximation.
SHRINK = {
    "fg3_pct": (lambda d: d["fg3m"], lambda d: d["fg3a"]),
    "ft_pct": (lambda d: d["ftm"], lambda d: d["fta"]),
    "rim_fg_pct": (lambda d: d["ra_fgm"], lambda d: d["ra_fga"]),
    "ts_pct": (lambda d: d["pts"] / 2, lambda d: d["fga"] + 0.44 * d["fta"]),
}

REFERENCE_MIN = 500  # season-relative scales are anchored on rotation players


def position_group(position_num):
    """Coarse prior groups from listed position: guard (G, G-F), forward (F-G, F, F-C), big (C-F, C)."""
    return pd.cut(position_num, bins=[0, 2.0, 3.5, 5.0], labels=["guard", "forward", "big"]).astype("object")


def fit_beta_binomial(k, n):
    """MLE of a Beta(alpha, beta) prior for success rates given successes k out of n trials."""
    k, n = np.asarray(k, float), np.asarray(n, float)
    keep = n > 0
    k, n = np.minimum(k[keep], n[keep]), n[keep]  # TS% can exceed 1 on tiny samples
    p = k.sum() / n.sum()
    x0 = np.log([p * 20, (1 - p) * 20])

    def nll(log_ab):
        a, b = np.exp(log_ab)
        return -(betaln(k + a, n - k + b) - betaln(a, b)).sum()

    a, b = np.exp(minimize(nll, x0, method="Nelder-Mead", options={"xatol": 1e-6, "fatol": 1e-6}).x)
    return a, b


def shrink_percentages(df, group_col="prior_group"):
    """Add <stat>_shr columns: posterior means under a season × position-group beta prior.

    Players with no listed position use the season-wide prior. Also adds <stat>_prior_n
    (alpha + beta), the prior's weight in attempts, as a reliability reference.
    """
    df = df.copy()
    df[group_col] = position_group(df["position_num"]).fillna("all")
    for stat, (succ, trials) in SHRINK.items():
        k, n = succ(df).clip(lower=0), trials(df)
        k = np.minimum(k, n)
        shr = pd.Series(np.nan, index=df.index)
        prior_n = pd.Series(np.nan, index=df.index)
        for season, idx in df.groupby("season").groups.items():
            season_prior = fit_beta_binomial(k[idx], n[idx])
            for grp, gidx in df.loc[idx].groupby(group_col).groups.items():
                a, b = season_prior if grp == "all" else fit_beta_binomial(k[gidx], n[gidx])
                shr[gidx] = (k[gidx] + a) / (n[gidx] + a + b)
                prior_n[gidx] = a + b
        df[f"{stat}_shr"] = shr
        df[f"{stat}_prior_n"] = prior_n
    return df


def season_relative(df, cols, ref_min=REFERENCE_MIN):
    """Add <col>_z and <col>_pctl, scaled within each season against players with >= ref_min minutes.

    Every player (including low-minute ones) is placed on the rotation players' scale,
    so the scale itself is not distorted by small-sample noise.
    """
    df = df.copy()
    new = {}
    for season, g in df.groupby("season"):
        ref = g[g["min"] >= ref_min]
        for c in cols:
            r = ref[c].dropna().to_numpy()
            new.setdefault(f"{c}_z", pd.Series(np.nan, index=df.index))[g.index] = (g[c] - r.mean()) / r.std(ddof=1)
            sorted_r = np.sort(r)
            pctl = np.searchsorted(sorted_r, g[c].to_numpy(), side="right") / len(sorted_r)
            new.setdefault(f"{c}_pctl", pd.Series(np.nan, index=df.index))[g.index] = np.where(g[c].isna(), np.nan, pctl)
    return pd.concat([df, pd.DataFrame(new)], axis=1)
