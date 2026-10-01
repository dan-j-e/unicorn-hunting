"""Unicorn scores (decision D16). Both compare a player only with that season's players.

unicorn_score  (b) rare combination of strengths. For every pair of traits, measure how
               often rotation players are strong (top 20%) in both. If the traits were
               unrelated that would be 4%. A player earns the excess rarity (above 4%) of
               every pair he is strong in; common pairs (size + rebounding) add nothing.
               Being #1 at a single skill does not make a unicorn.

strangeness    (a) unusual in any direction: mean distance to the player's 5 most similar
               rotation players that season, in season-relative z-score space. Handles a
               league made of distinct player types (a traditional centre has many
               near-twins; Wembanyama has none). Strange-but-not-good players score too.
"""

import itertools

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

REFERENCE_MIN = 500

# label -> season-relative base column. Higher = more of the trait, except turnovers,
# which is inverted to "ball security" for the strengths score.
TRAITS = {
    "size": "height_in", "off. rebounding": "oreb_pct", "def. rebounding": "dreb_pct",
    "rim protection": "blk_per100", "steals": "stl_per100", "finishing": "rim_fg_pct_shr",
    "passing": "ast_pct", "self-creation": "pct_uast_fgm", "3pt volume": "fg3a_rate",
    "3pt accuracy": "fg3_pct_shr", "FT touch": "ft_pct_shr", "usage": "usg_pct",
    "efficiency": "ts_pct_shr", "FT drawing": "fta_rate", "ball security": "tm_tov_pct",
}
INVERTED = {"ball security"}


def _strength_pctl(df):
    out = pd.DataFrame(index=df.index)
    for label, base in TRAITS.items():
        p = df[f"{base}_pctl"]
        out[label] = 1 - p if label in INVERTED else p
    return out


def pair_rarity(df, strong=0.8, smoothing=25):
    """Per season: share of rotation players strong in both traits of each pair (smoothed toward chance)."""
    chance = (1 - strong) ** 2
    pairs = list(itertools.combinations(TRAITS, 2))
    rows = []
    for season, g in df.groupby("season"):
        ref = _strength_pctl(g[g["min"] >= REFERENCE_MIN]) >= strong
        for a, b in pairs:
            both = (ref[a] & ref[b]).sum()
            rows.append({"season": season, "trait_a": a, "trait_b": b, "share_both": both / len(ref),
                         "share_smoothed": (both + smoothing * chance) / (len(ref) + smoothing)})
    out = pd.DataFrame(rows)
    out["excess_rarity"] = np.clip(-np.log10(out["share_smoothed"]) + np.log10(chance), 0, None)
    return out


def add_unicorn_score(df, strong=0.8, smoothing=25):
    df = df.copy()
    rarity = pair_rarity(df, strong, smoothing)
    pct = _strength_pctl(df) >= strong
    score = pd.Series(0.0, index=df.index)
    contributions = []
    for season, r in rarity.groupby("season"):
        idx = df.index[df["season"] == season]
        contrib = pd.DataFrame({f"{a} + {b}": pct.loc[idx, a] & pct.loc[idx, b] for a, b in zip(r["trait_a"], r["trait_b"])})
        contrib = contrib * r["excess_rarity"].to_numpy()[None, :]
        score[idx] = contrib.sum(axis=1)
        contributions.append(contrib)
    contrib = pd.concat(contributions).reindex(df.index)
    df["unicorn_score"] = score
    df["unicorn_pairs"] = [", ".join(row[row > 0].sort_values(ascending=False).index[:3]) for _, row in contrib.iterrows()]
    return df


def add_strangeness(df, k=5, clip=5.0):
    df = df.copy()
    labels = list(TRAITS)
    cols = [f"{TRAITS[t]}_z" for t in labels]
    df["strangeness"] = np.nan
    df["strange_traits"] = ""
    for season, g in df.groupby("season"):
        X = g[cols].fillna(0.0).clip(-clip, clip).to_numpy()
        is_ref = (g["min"] >= REFERENCE_MIN).to_numpy()
        R, ref_ids = X[is_ref], g["player_id"].to_numpy()[is_ref]
        dist, idx = NearestNeighbors(n_neighbors=k + 1).fit(R).kneighbors(X)
        # drop the player himself if he is in the reference set, keep k neighbours
        dist = np.where(ref_ids[idx] == g["player_id"].to_numpy()[:, None], np.nan, dist)
        order = np.argsort(np.isnan(dist), axis=1, kind="stable")[:, :k]
        dist, idx = np.take_along_axis(dist, order, 1), np.take_along_axis(idx, order, 1)
        gaps = np.abs(X[:, None, :] - R[idx]).mean(axis=1)
        df.loc[g.index, "strangeness"] = dist.mean(axis=1)
        df.loc[g.index, "strange_traits"] = [", ".join(labels[a] for a in np.argsort(-row)[:3]) for row in gaps]
    rot = df["min"] >= REFERENCE_MIN
    df["strangeness_pctl"] = np.nan
    for season, g in df[rot].groupby("season"):
        ref = np.sort(g["strangeness"].to_numpy())
        rows = df["season"] == season
        df.loc[rows, "strangeness_pctl"] = np.searchsorted(ref, df.loc[rows, "strangeness"], side="right") / len(ref)
    return df
