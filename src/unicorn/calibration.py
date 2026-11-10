"""Honest early-season chances (TODO item 3; notebook 20): temperature scaling of the choice model.

The model's chance for player i in a season is softmax(s_i), with s_i its score. Early in a season it is
too sure of its leaders. Temperature scaling replaces s_i with s_i / T: T > 1 spreads the chances out,
T < 1 sharpens them. The order of the players never changes, only how sure the model is.

T is learned per point of the season from out-of-sample scores: for each past season, scores from a model
that never saw that season, then the T that makes the actual winners most likely.
"""

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp


def scores(model, df):
    """The choice model's score s_i for every row (before the softmax)."""
    return model._design(df) @ model.coef_


def winner_loglik(groups, T):
    """Sum over seasons of log P(actual winner) with temperature T. groups: list of (scores, winner index)."""
    return sum(s[w] / T - logsumexp(s / T) for s, w in groups)


def fit_temperature(groups, bounds=(0.3, 6.0)):
    res = minimize_scalar(lambda logT: -winner_loglik(groups, np.exp(logT)), bounds=np.log(bounds), method="bounded")
    return float(np.exp(res.x))


def softmax_T(s, T):
    z = s / T
    return np.exp(z - logsumexp(z))
