"""Walk-forward (expanding window) backtest.

For each test season t (predictions made at the end of t):
  * features come from season t and earlier only (all feature columns are built that way);
  * a training row from season s is usable only if its outcome was KNOWN by the end of t,
    i.e. s + horizon <= t. For a next-season label that means s <= t-1; for a
    within-3-seasons label, s <= t-3;
  * any preprocessing (imputation, scaling) is fitted on those training rows only.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from unicorn.columns import relative_columns


def feature_columns(df):
    """Candidate predictors: current level, trajectory, career context, position, unicorn and star pillars."""
    rel = [f"{c}_z" for c in relative_columns()]
    trajectory = [f"{c}_{s}" for c in rel for s in ("delta", "slope3", "roll3", "vs_past")]
    context = ["age", "exp", "entry_age", "draft_pick_filled", "undrafted", "seasons_played", "seasons_missed",
               "career_min_to_date", "min", "gp", "start_rate", "min_vs_past", "min_delta"]
    position = ["position_num", "position_body", "position_style", "style_vs_listed", "style_vs_body"]
    unicorn = ["unicorn_score", "strangeness", "star_score"] + [c for c in df.columns if c.startswith("pillar_")]
    cols = rel + trajectory + context + position + unicorn
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"missing feature columns: {missing}")
    return cols


def logistic_model(C=0.1):
    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(),
                         LogisticRegression(C=C, max_iter=2000))


class TunedLogistic:
    """Logistic regression whose L2 strength is chosen inside the training window only:
    fit on all but the most recent training season, pick C by average precision on that
    season, then refit on the full training window."""

    grid = (0.003, 0.01, 0.03, 0.1, 0.3, 1.0)
    needs_frame = True

    def fit_frame(self, train, target, features):
        last = train["season_start"].max()
        inner, valid = train[train["season_start"] < last], train[train["season_start"] == last]
        best, self.C_ = -1.0, self.grid[0]
        if inner[target].sum() >= 5 and valid[target].any():
            for C in self.grid:
                m = logistic_model(C).fit(inner[features], inner[target].astype(int))
                ap = average_precision_score(valid[target].astype(int), m.predict_proba(valid[features])[:, 1])
                if ap > best:
                    best, self.C_ = ap, C
        self.model = logistic_model(self.C_).fit(train[features], train[target].astype(int))
        self.features = features
        return self

    def predict_proba(self, X):
        return self.model.predict_proba(X[self.features])


def boosted_trees():
    """Shallow, heavily regularized gradient boosting; handles missing values natively."""
    return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=40,
                                          l2_regularization=1.0, random_state=0)


COMP_FEATURES = [  # what "similar player" means for nearest-neighbour comps
    "age", "height_in_z", "weight_lb_z", "min_per_game_z", "usg_pct_z", "ts_pct_shr_z", "ast_pct_z", "tm_tov_pct_z",
    "oreb_pct_z", "dreb_pct_z", "stl_per100_z", "blk_per100_z", "fg3a_rate_z", "fg3_pct_shr_z", "fta_rate_z",
    "rim_rate_z", "pct_uast_fgm_z", "star_score",
]


class NearestComps:
    """Probability = distance-weighted share of the k most similar historical player-seasons that had the outcome."""

    def __init__(self, k=40):
        self.k = k

    def fit(self, X, y):
        self.model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                   KNeighborsClassifier(n_neighbors=self.k, weights="distance")).fit(X[COMP_FEATURES], y)
        return self

    def predict_proba(self, X):
        return self.model.predict_proba(X[COMP_FEATURES])


def walk_forward(df, target, horizon, population, first_test, last_test, models, features):
    """Run every model through every test season.

    models: {name: callable} where the callable is either
            - "rule": function(test_df) -> score (no fitting), or
            - a factory returning an sklearn estimator with predict_proba.
    Returns one row per (test season, player, model) with score and outcome.
    """
    out = []
    for t in range(first_test, last_test + 1):
        train = df[population & (df["season_start"] + horizon <= t) & df[target].notna()]
        test = df[population & (df["season_start"] == t)]
        if test.empty:
            continue
        for name, model in models.items():
            if getattr(model, "is_rule", False):
                score = model(test)
            elif getattr(model, "needs_frame", False):
                score = model().fit_frame(train, target, features).predict_proba(test)[:, 1]
            else:
                est = model().fit(train[features], train[target].astype(int))
                score = est.predict_proba(test[features])[:, 1]
            out.append(pd.DataFrame({"test_season": t, "model": name, "player_id": test["player_id"],
                                     "player_name": test["player_name"], "season": test["season"],
                                     "score": np.asarray(score, float), "outcome": test[target].astype(int),
                                     "n_train": len(train)}))
    return pd.concat(out, ignore_index=True)


def rule(fn):
    """Mark a plain scoring function as a no-fit baseline."""
    fn.is_rule = True
    return fn


def precision_at_k(g, k):
    return g.nlargest(k, "score")["outcome"].mean()


def recall_at_k(g, k):
    total = g["outcome"].sum()
    return g.nlargest(k, "score")["outcome"].sum() / total if total else np.nan


def evaluate(preds, ks=(10, 25)):
    """Per model: pooled ROC-AUC and average precision, plus mean per-season precision/recall@k."""
    rows = []
    for name, g in preds.groupby("model"):
        per_season = g.groupby("test_season")
        row = {"model": name, "n": len(g), "positives": int(g["outcome"].sum()), "base_rate": g["outcome"].mean(),
               "ROC_AUC": roc_auc_score(g["outcome"], g["score"]),
               "avg_precision": average_precision_score(g["outcome"], g["score"])}
        for k in ks:
            row[f"precision@{k}"] = per_season.apply(precision_at_k, k, include_groups=False).mean()
            row[f"recall@{k}"] = per_season.apply(recall_at_k, k, include_groups=False).mean()
        rows.append(row)
    out = pd.DataFrame(rows).set_index("model")
    out["AP_lift"] = out["avg_precision"] / out["base_rate"]
    return out.sort_values("avg_precision", ascending=False)


def per_season_ap(preds):
    return (preds.groupby(["model", "test_season"])
            .apply(lambda g: average_precision_score(g["outcome"], g["score"]) if g["outcome"].any() else np.nan,
                   include_groups=False)
            .unstack("model"))


def bootstrap_ap(preds, n_boot=500, seed=0, return_draws=False):
    """Average-precision lift per model with a 95% CI, resampling whole players (paired across models,
    so `draws[a] - draws[b]` gives a valid CI for the difference between two models)."""
    rng = np.random.default_rng(seed)
    players = preds["player_id"].unique()
    by_player = {pid: idx for pid, idx in preds.groupby("player_id").groups.items()}
    models = preds["model"].unique()
    draws = {m: [] for m in models}
    for _ in range(n_boot):
        sample = preds.loc[np.concatenate([by_player[p] for p in rng.choice(players, len(players))])]
        for m, g in sample.groupby("model"):
            if g["outcome"].any():
                draws[m].append(average_precision_score(g["outcome"], g["score"]) / g["outcome"].mean())
    point = evaluate(preds)["AP_lift"]
    table = pd.DataFrame({"AP_lift": point, "ci_low": {m: np.percentile(d, 2.5) for m, d in draws.items()},
                         "ci_high": {m: np.percentile(d, 97.5) for m, d in draws.items()}}).sort_values("AP_lift", ascending=False)
    return (table, pd.DataFrame(draws)) if return_draws else table
