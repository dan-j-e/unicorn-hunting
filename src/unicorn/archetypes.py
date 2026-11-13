"""Playing-style clusters: fitting, numbering, examples, stability and the two standard charts (notebook 13)."""

import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture

from unicorn.plotting import DIVERGING, FIG_DIR, INK, INK2, MUTED, SERIES8, SURFACE

GROUPS = {
    "where he shoots": ["rim_rate", "paint_non_ra_rate", "mid_rate", "fg3a_rate", "corner3_share", "fta_rate"],
    "how he creates": ["usg_pct", "pct_uast_fgm", "ast_pct", "pct_pts_fb"],
    "rebounding": ["oreb_pct", "dreb_pct"],
    "defence (box score)": ["blk_per100", "stl_per100", "pf_per36"],
}
FEATURES = [c for g in GROUPS.values() for c in g]
SHORT = {"rim_rate": "rim shots", "paint_non_ra_rate": "paint (not rim)", "mid_rate": "mid-range", "fg3a_rate": "threes",
         "corner3_share": "corner threes", "fta_rate": "free throws", "usg_pct": "usage", "pct_uast_fgm": "self-created makes",
         "ast_pct": "assists", "pct_pts_fb": "fast breaks", "oreb_pct": "offensive boards", "dreb_pct": "defensive boards",
         "blk_per100": "blocks", "stl_per100": "steals", "pf_per36": "fouls"}


def mixture(k, seed=0):
    return GaussianMixture(k, covariance_type="diag", n_init=3, random_state=seed)


def style_axes(X, features=FEATURES):
    """Two main directions of the style space, oriented: inside to the right (rim shots), on-ball up (usage)."""
    Xc = X - X.mean(axis=0)
    _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
    if Vt[0, features.index("rim_rate")] < 0: Vt[0] *= -1
    if Vt[1, features.index("usg_pct")] < 0: Vt[1] *= -1
    return Xc @ Vt[:2].T


def stability(X, k, groups=None, repeats=6, make=mixture):
    """Fit on two random halves (split by `groups`, e.g. player, so one player's windows stay together); agreement on all rows."""
    rng, out = np.random.default_rng(1), []
    ids = np.unique(groups) if groups is not None else np.arange(len(X))
    for r in range(repeats):
        half = set(rng.choice(ids, len(ids) // 2, replace=False))
        a = np.isin(groups if groups is not None else np.arange(len(X)), list(half))
        out.append(adjusted_rand_score(make(k, r).fit(X[a]).predict(X), make(k, r + 50).fit(X[~a]).predict(X)))
    return np.mean(out)


def how_many(X, k_range, groups=None, repeats=6):
    """Stability (both methods), separation and fit for each number of clusters. More `repeats` = a steadier stability estimate."""
    kmeans = lambda k, seed: KMeans(k, n_init=10, random_state=seed)
    rows = []
    for k in k_range:
        gm = mixture(k).fit(X)
        lab = gm.predict(X)
        rows.append({"clusters": k, "stability (soft mixture)": stability(X, k, groups, repeats), "stability (k-means)": stability(X, k, groups, repeats, make=kmeans),
                     "separation": silhouette_score(X, lab, sample_size=3000, random_state=0), "fit (BIC)": gm.bic(X)})
    return pd.DataFrame(rows).set_index("clusters")


def fit_clusters(X, k, pc, rows, minutes_col="min", min_minutes=1500, n=10):
    """Fit k clusters; number them 1..k from most inside to most perimeter.
    Returns main cluster, membership, and per cluster the best-known (most minutes, 90%+ membership) and most typical
    (closest to the centre) rows, one per player."""
    gm = mixture(k).fit(X)
    prob = gm.predict_proba(X)
    order = np.argsort(-(prob.T @ pc[:, 0]) / prob.sum(axis=0))
    lab = prob[:, order].argmax(axis=1) + 1
    d = rows.assign(cluster=lab, membership=prob.max(axis=1))
    typical, known = {}, {}
    for c in range(1, k + 1):
        j = order[c - 1]
        dens = -0.5 * (((X - gm.means_[j]) ** 2 / gm.covariances_[j]) + np.log(2 * np.pi * gm.covariances_[j])).sum(axis=1)
        m = d.assign(typicality=dens)[(d["cluster"] == c) & (d[minutes_col] >= min_minutes)]
        typical[c] = m.sort_values("typicality", ascending=False).drop_duplicates("player_name").head(n)
        known[c] = m[m["membership"] >= 0.9].sort_values(minutes_col, ascending=False).drop_duplicates("player_name").head(n)
    return lab, prob.max(axis=1), typical, known


def profile_heatmap(prof, known, fname, title, value_label="vs the average (SD)", names=None):
    """One row per cluster, one column per style measure. `names` ({cluster: name}) labels rows by name instead of number."""
    k = len(prof)
    fig, ax = plt.subplots(figsize=(15, 0.62 * k + 1.6))
    im = ax.imshow(prof[FEATURES].to_numpy(), cmap=DIVERGING, vmin=-1.6, vmax=1.6, aspect="auto")
    for i in range(k):
        for j, col in enumerate(FEATURES):
            v = prof.iloc[i][col]
            ax.text(j, i, f"{v:+.1f}", ha="center", va="center", fontsize=9, color=SURFACE if abs(v) > 1.0 else INK)
    rows = [f"{c}. {names[c]}  ({', '.join(known[c]['player_name'].head(2))})" if names else f"Cluster {c}: " + ", ".join(known[c]["player_name"].head(3))
            for c in prof.index]
    ax.set_yticks(range(k), rows, fontsize=9.5)
    ax.set_xticks(range(len(FEATURES)), [SHORT[c] for c in FEATURES], rotation=35, ha="right", fontsize=9)
    x0 = 0
    for g, cs in GROUPS.items():
        ax.text(x0 + (len(cs) - 1) / 2, -0.65, g, ha="center", va="bottom", fontsize=9.5, color=INK2, fontweight="bold")
        if x0: ax.axvline(x0 - 0.5, color=SURFACE, linewidth=3)
        x0 += len(cs)
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01); cb.set_label(value_label)
    ax.set_title(title, loc="left", fontsize=12, pad=44)
    fig.savefig(FIG_DIR / fname, dpi=150, bbox_inches="tight")
    return fig


def traits(prof_row, n_hi=3, n_lo=2):
    hi = [SHORT[c] for c in prof_row.sort_values(ascending=False).index[:n_hi] if prof_row[c] > 0.3]
    lo = [SHORT[c] for c in prof_row.sort_values().index[:n_lo] if prof_row[c] < -0.3]
    return textwrap.fill("more: " + ", ".join(hi), 46) + ("\n" + textwrap.fill("less: " + ", ".join(lo), 46) if lo else "")


def who_is_in_which(pc, lab, rows, known, typical, prof, sizes, when, fname, title, map_note=True, names=None, unit="rows"):
    """Small multiples: the style map with one cluster highlighted, its best-known (black dots) and most typical players,
    what it does most and least, and its typical size. `when(row)` formats the season or window shown after a name.
    `names` ({cluster: name}) titles each panel by name; `unit` names what a row is (for "x% of player-seasons")."""
    k = len(prof)
    nrows = (k + 1) // 2
    fig = plt.figure(figsize=(17, 4.75 * nrows))
    gs = fig.add_gridspec(nrows, 4, width_ratios=[1.15, 1, 1.15, 1], hspace=0.32, wspace=0.05)
    lo, hi = np.percentile(pc, [0.2, 99.8], axis=0)
    for c in range(1, k + 1):
        r, col = (c - 1) // 2, ((c - 1) % 2) * 2
        ax, tx = fig.add_subplot(gs[r, col]), fig.add_subplot(gs[r, col + 1])
        m = lab == c
        ax.scatter(pc[~m, 0], pc[~m, 1], s=3, color=MUTED, alpha=0.35, edgecolor="none")
        ax.scatter(pc[m, 0], pc[m, 1], s=6, color=SERIES8[c - 1], alpha=0.7, edgecolor="none")
        idx = [rows.index.get_loc(i) for i in known[c].head(6).index]
        ax.scatter(pc[idx, 0], pc[idx, 1], s=34, color=INK, edgecolor=SURFACE, linewidth=0.8, zorder=3)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1] + 0.25 * (hi[1] - lo[1]))
        head = textwrap.fill(f"{c}. {names[c]}", 26) if names else f"Cluster {c}"
        ax.text(0.03, 0.97, head, transform=ax.transAxes, fontsize=12.5 if names else 14, fontweight="bold", color=INK, va="top", linespacing=1.15)
        ax.text(0.03, 0.97 - 0.09 * (head.count("\n") + 1), f"{m.mean():.0%} of {unit}", transform=ax.transAxes, fontsize=9, color=INK2, va="top")
        if c == 1 and map_note:
            ax.text(0.98, 0.02, "map: ← perimeter · inside →, ↓ off-ball · on-ball ↑", transform=ax.transAxes, fontsize=7.5, color=INK2, ha="right")
        tx.axis("off")
        lines = [("Best-known (black dots)", True)] + [(f"{r_['player_name']}  ({when(r_)})", False) for _, r_ in known[c].head(6).iterrows()]
        lines += [("", False), ("Most typical", True)] + [(f"{r_['player_name']}  ({when(r_)})", False) for _, r_ in typical[c].head(3).iterrows()]
        y = 0.98
        for text, bold in lines:
            tx.text(0.04, y, text, fontsize=10 if bold else 9.5, fontweight="bold" if bold else "normal", color=INK if bold else INK2,
                    va="top", transform=tx.transAxes)
            y -= 0.078
        tx.text(0.04, y - 0.02, traits(prof.loc[c]), fontsize=9, color=INK, va="top", transform=tx.transAxes, linespacing=1.4)
        s = sizes.loc[c]
        tx.text(0.04, y - 0.24, f"typical size: {s['height'] // 12:.0f}'{s['height'] % 12:.0f}\", {s['weight']:.0f} lb",
                fontsize=9, color=INK2, va="top", transform=tx.transAxes)
    fig.suptitle(title, x=0.06, y=0.915 if nrows == 4 else 0.93, ha="left", fontsize=15, fontweight="bold")
    fig.savefig(FIG_DIR / fname, dpi=150, bbox_inches="tight")
    return fig
