"""Small statistical helpers used across the analysis notebooks."""

import numpy as np
import pandas as pd
from scipy.stats import rankdata


def _residualize(y, controls):
    X = np.column_stack([np.ones(len(y)), controls])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    return y - X @ beta


def _partial_spearman_arrays(x, y, controls):
    """Spearman partial correlation: rank everything, residualize x and y on the
    ranked controls, correlate the residuals."""
    x, y = rankdata(x), rankdata(y)
    c = np.column_stack([rankdata(col) for col in controls.T]) if controls.size else np.empty((len(x), 0))
    return np.corrcoef(_residualize(x, c), _residualize(y, c))[0, 1]


def partial_spearman(df, x, y, controls, cluster="player_id", n_boot=500, seed=0):
    """Partial Spearman correlation of x with y given controls, with a cluster
    bootstrap 95% CI (resampling whole players, since a player contributes
    several correlated seasons).

    Returns a dict: estimate, ci_low, ci_high, n.
    """
    d = df[[x, y, *controls, cluster]].dropna()
    xs, ys, cs = d[x].to_numpy(float), d[y].to_numpy(float), d[controls].to_numpy(float)
    est = _partial_spearman_arrays(xs, ys, cs)

    rng = np.random.default_rng(seed)
    groups = [np.flatnonzero(m) for m in pd.get_dummies(d[cluster]).to_numpy(bool).T]
    boots = []
    for _ in range(n_boot):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        boots.append(_partial_spearman_arrays(xs[idx], ys[idx], cs[idx]))
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    return {"estimate": est, "ci_low": lo, "ci_high": hi, "n": len(d)}
