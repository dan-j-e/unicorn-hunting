"""Most Improved Player choice model.

Each season exactly one eligible player wins. A conditional-logit ("choice") model gives every
player a score w · x (x = his improvements vs his previous season) and turns scores into win
probabilities with a softmax *within the season*, so probabilities in a season sum to 1. The
weights w say how much each kind of improvement matters to the voters.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import logsumexp

DELTAS = ["ppg_delta", "rpg_delta", "apg_delta", "mpg_delta", "game_score_delta", "ts_delta", "usg_delta", "start_rate_delta"]
L2_GRID = (0.1, 0.3, 1.0, 3.0, 10.0)


class ChoiceModel:
    def __init__(self, features, l2=1.0):
        self.features, self.l2 = list(features), l2

    def _design(self, df):
        X = df[self.features].fillna(0.0).to_numpy(float)
        return (X - self.mean_) / self.std_

    def fit(self, df, season_col="season", target="mip"):
        X = df[self.features].fillna(0.0).to_numpy(float)
        self.mean_, self.std_ = X.mean(axis=0), X.std(axis=0) + 1e-9
        X = (X - self.mean_) / self.std_
        groups = [np.flatnonzero(m) for m in pd.get_dummies(df[season_col]).to_numpy(bool).T]
        winners = [idx[df[target].to_numpy()[idx]] for idx in groups]
        groups = [(idx, w[0]) for idx, w in zip(groups, winners) if len(w) == 1]

        def loss(beta):
            s = X @ beta
            nll, grad = 0.0, np.zeros_like(beta)
            for idx, win in groups:
                lse = logsumexp(s[idx])
                p = np.exp(s[idx] - lse)
                nll -= s[win] - lse
                grad -= X[win] - p @ X[idx]
            return nll + 0.5 * self.l2 * beta @ beta, grad + self.l2 * beta

        self.coef_ = minimize(loss, np.zeros(X.shape[1]), jac=True, method="L-BFGS-B").x
        return self

    def predict_proba(self, df, season_col="season"):
        s = pd.Series(self._design(df) @ self.coef_, index=df.index)
        return s.groupby(df[season_col]).transform(lambda v: np.exp(v - logsumexp(v)))

    def coefficients(self):
        return pd.Series(self.coef_, index=self.features)


def _winner_logprob(df, proba, target="mip"):
    return np.log(proba[df[target]].clip(lower=1e-12)).mean()


def choose_l2(train, features, grid=L2_GRID):
    """Pick the L2 strength by leave-one-season-out log-likelihood *inside* the training seasons."""
    seasons = train["season"].unique()
    best, best_ll = grid[0], -np.inf
    for l2 in grid:
        ll = []
        for s in seasons:
            fit, held = train[train["season"] != s], train[train["season"] == s]
            m = ChoiceModel(features, l2).fit(fit)
            ll.append(_winner_logprob(held, m.predict_proba(held)))
        if np.mean(ll) > best_ll:
            best, best_ll = l2, np.mean(ll)
    return best


def out_of_sample_probabilities(df, features, scheme="loso", min_train=5):
    """Win probability for every eligible player, each season predicted by a model that never saw it.

    scheme="loso":         trained on all OTHER seasons (fine for 'in retrospect')
    scheme="walk_forward": trained only on EARLIER seasons (needs >= min_train of them)
    The L2 strength is chosen inside each training set (nested), so the held-out season is untouched.
    """
    out = []
    seasons = sorted(df["season"].unique())
    for i, s in enumerate(seasons):
        train = df[df["season"] != s] if scheme == "loso" else df[df["season"].isin(seasons[:i])]
        if scheme == "walk_forward" and len(seasons[:i]) < min_train:
            continue
        test = df[df["season"] == s]
        m = ChoiceModel(features, choose_l2(train, features)).fit(train)
        out.append(pd.Series(m.predict_proba(test), index=test.index))
    return pd.concat(out)


def summarize(df, proba, target="mip"):
    d = df.assign(p=proba).dropna(subset=["p"])
    d["rank"] = d.groupby("season")["p"].rank(ascending=False, method="min")
    w = d[d[target]]
    pool = d.groupby("season").size()
    return {"seasons": len(w), "winner #1": int((w["rank"] == 1).sum()), "winner top 3": int((w["rank"] <= 3).sum()),
            "median winner rank": float(w["rank"].median()), "mean winner probability": float(w["p"].mean()),
            "log-likelihood vs random pick": float(np.mean(np.log(w["p"]) - np.log(1 / pool[w["season"]].to_numpy())))}
