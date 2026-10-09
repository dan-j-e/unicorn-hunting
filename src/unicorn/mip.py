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

from unicorn.labels import MIP_WINNERS as MIP_WINNER_IDS

DELTAS = ["ppg_delta", "rpg_delta", "apg_delta", "mpg_delta", "game_score_delta", "ts_delta", "usg_delta", "start_rate_delta"]
GAMELOG_DELTAS = ["ppg_delta", "rpg_delta", "apg_delta", "mpg_delta", "game_score_delta", "ts_delta"]  # usable mid-season
DEFENSE = ["spg_delta", "bpg_delta", "def_rating_delta"]
GAMELOG_DEFENSE = ["spg_delta", "bpg_delta"]  # defensive rating is season-long, so not used mid-season
RELATIVE = ["ppg_rel", "game_score_rel"]
ABSOLUTE_ALL = DELTAS + DEFENSE   # every ΔX
RELATIVE_ALL = ["ppg_rel", "rpg_rel", "apg_rel", "spg_rel", "bpg_rel", "mpg_rel", "game_score_rel", "ts_rel", "usg_rel",
                "def_rating_rel"]  # every Δ%
TEAM = ["team_win_delta"]
LEVEL = ["game_score", "ppg", "base_game_score"]          # where he ended up, and where he started
SEASON_LEVEL = ["star_score", "base_star_score", "became_starter"]
AGE = ["age"]
L2_GRID = (0.1, 0.3, 1.0, 3.0, 10.0)


class ChoiceModel:
    def __init__(self, features, l2=1.0):
        self.features, self.l2 = list(features), l2

    def _design(self, df):
        X = df[self.features].fillna(0.0).to_numpy(float)
        return (X - self.mean_) / self.std_

    def fit(self, df, season_col="season", target="mip"):
        # keep only seasons with exactly one winner, rows contiguous by season (vectorized softmax)
        winners_per_season = df.groupby(season_col)[target].transform("sum")
        d = df[winners_per_season == 1].sort_values(season_col, kind="stable")
        X = d[self.features].fillna(0.0).to_numpy(float)
        self.mean_, self.std_ = X.mean(axis=0), X.std(axis=0) + 1e-9
        X = (X - self.mean_) / self.std_
        group = pd.factorize(d[season_col])[0]
        starts = np.flatnonzero(np.r_[True, group[1:] != group[:-1]])
        x_win = X[d[target].to_numpy(bool)].sum(axis=0)

        def loss(beta):
            s = X @ beta
            m = np.maximum.reduceat(s, starts)
            e = np.exp(s - m[group])
            den = np.add.reduceat(e, starts)
            lse = m + np.log(den)
            p = e / den[group]
            nll = -(x_win @ beta - lse.sum())
            grad = -(x_win - p @ X)
            return nll + 0.5 * self.l2 * beta @ beta, grad + self.l2 * beta

        self.coef_ = minimize(loss, np.zeros(X.shape[1]), jac=True, method="L-BFGS-B").x
        return self

    def predict_proba(self, df, season_col="season"):
        s = pd.Series(self._design(df) @ self.coef_, index=df.index)
        lse = s.groupby(df[season_col]).transform(logsumexp)
        return np.exp(s - lse)

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


def probability_bars(P, title, subtitle, path, top_n=5):
    """Small multiples: each season's top-n players by win probability (full names); our top 3 in blue,
    the actual winner starred; if the winner is outside the top n he is appended with his rank."""
    import matplotlib.pyplot as plt
    from unicorn.plotting import BLUE, INK, INK2, MUTED, ORANGE

    P = P.copy()
    P["rank"] = P.groupby("season")["p"].rank(ascending=False, method="min").astype(int)
    seasons = sorted(P["season"].unique())
    ncols = 5
    nrows = int(np.ceil(len(seasons) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(21, 3.6 * nrows + 0.8))
    for ax in axes.flat[len(seasons):]:
        ax.axis("off")
    for ax, s in zip(axes.flat, seasons):
        d = P[P["season"] == s].sort_values("p", ascending=False)
        show, winner = d.head(top_n), d[d["mip"]]
        if not winner.empty and winner.index[0] not in show.index:
            show = pd.concat([show, winner])
        show = show.iloc[::-1]
        y = np.arange(len(show))
        ax.barh(y, show["p"], color=[BLUE if r <= 3 else MUTED for r in show["rank"]], height=0.66)
        for yi, (_, r) in zip(y, show.iterrows()):
            ax.annotate(f"{r['p']:.0%}" + (f"  (#{r['rank']})" if r["rank"] > top_n else ""), (r["p"], yi), xytext=(4, 0),
                        textcoords="offset points", va="center", fontsize=8, color=INK2)
            if r["mip"]:
                ax.scatter([-0.03], [yi], marker="*", s=130, color=ORANGE, clip_on=False, zorder=4,
                           transform=ax.get_yaxis_transform())
        ax.set_yticks(y, show["player_name"], fontsize=8.5)
        ax.set_xlim(0, max(0.85, show["p"].max() * 1.3)); ax.set_xticks([]); ax.grid(False)
        ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, pad=18)
        hit = "★ in our top 3" if (not winner.empty and winner["rank"].iloc[0] <= 3) else f"winner ranked #{winner['rank'].iloc[0]}"
        ax.set_title(f"{s}   {hit}", loc="left", fontsize=10, color=INK)
    fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.text(0.01, 1 - 0.55 / fig.get_figheight(), subtitle, ha="left", fontsize=10, color=INK2)
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.75 / fig.get_figheight())); fig.subplots_adjust(wspace=0.95)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


def top_k_overlap(df, proba, votes, k=7):
    """Per season: how many of our top-k (by predicted chance) were in the real top-k of the voting."""
    d = df.assign(p=proba).dropna(subset=["p"])
    ours = d.sort_values("p", ascending=False).groupby("season").head(k)
    real = votes[votes["vote_rank"] <= k]
    out = []
    for s, o in ours.groupby("season"):
        r = set(real.loc[real["season"] == s, "player_id"].dropna().astype(int))
        out.append({"season": s, "overlap": len(set(o["player_id"].astype(int)) & r), "real_top_k": len(r)})
    return pd.DataFrame(out).set_index("season")


def top7_vs_votes_chart(P, votes, all_candidates, title, subtitle, path, k=7):
    """Small multiples: our top-k by predicted chance. Blue = also in the real top-k of the voting
    (labelled with his voting rank), gray = not; ★ = actual winner. Below each panel: real top-k
    players we missed, with the reason (not eligible / ranked lower by us)."""
    import matplotlib.pyplot as plt
    from unicorn.plotting import BLUE, INK, INK2, MUTED, ORANGE

    P = P.copy()
    P["rank"] = P.groupby("season")["p"].rank(ascending=False, method="min").astype(int)
    real = votes[votes["vote_rank"] <= k].copy()
    seasons = sorted(P["season"].unique())
    ncols, nrows = 5, int(np.ceil(len(seasons) / 5))
    row_h = 6.2  # inches per row: 7 bars plus up to 7 "missed" lines underneath
    fig, axes = plt.subplots(nrows, ncols, figsize=(23, row_h * nrows + 1.0))
    for ax in axes.flat[len(seasons):]:
        ax.axis("off")
    overlaps = []
    for ax, s in zip(axes.flat, seasons):
        d = P[P["season"] == s].sort_values("p", ascending=False).head(k).iloc[::-1]
        r = real[real["season"] == s].set_index("player_id")
        in_real = d["player_id"].isin(r.index)
        y = np.arange(len(d))
        ax.barh(y, d["p"], color=np.where(in_real, BLUE, MUTED), height=0.66)
        for yi, (_, row) in zip(y, d.iterrows()):
            tag = f"  vote #{int(r.loc[row['player_id'], 'vote_rank'])}" if row["player_id"] in r.index else ""
            ax.annotate(f"{row['p']:.0%}{tag}", (row["p"], yi), xytext=(4, 0), textcoords="offset points", va="center",
                        fontsize=8, color=INK if tag else INK2, fontweight="bold" if tag else "normal")
            if row["mip"]:
                ax.scatter([-0.03], [yi], marker="*", s=130, color=ORANGE, clip_on=False, zorder=4, transform=ax.get_yaxis_transform())
        ax.set_yticks(y, d["player_name"], fontsize=8.5)
        ax.set_xlim(0, max(0.9, d["p"].max() * 1.45)); ax.set_xticks([]); ax.grid(False)
        ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, pad=18)
        n_match = int(in_real.sum()); overlaps.append(n_match)
        ax.set_title(f"{s}   {n_match} of our top {k} in the real top {k}", loc="left", fontsize=10, color=INK)
        missed = r[~r.index.isin(d["player_id"])].sort_values("vote_rank")
        notes = []
        for pid, m in missed.iterrows():
            cand = all_candidates[(all_candidates["season"] == s) & (all_candidates["player_id"] == pid)]
            if cand.empty or not bool(cand["eligible"].iloc[0]):
                why = "not eligible: year 1-2" if (not cand.empty and cand["prior_seasons"].iloc[0] < 2) else "not eligible"
            else:
                rk = P[(P["season"] == s) & (P["player_id"] == pid)]["rank"]
                why = f"our #{int(rk.iloc[0])}" if len(rk) else "not ranked"
            star = "★ " if MIP_WINNER_IDS.get(s) == pid else ""
            notes.append(f"{star}{m['player']} (vote #{int(m['vote_rank'])}, {why})")
        if notes:
            ax.text(-0.02, -0.06, "Real top 7 we missed:\n" + "\n".join(notes), transform=ax.transAxes, fontsize=7.6,
                    color=INK2, va="top", ha="left", linespacing=1.35)
    h = fig.get_figheight()
    fig.suptitle(title, x=0.01, y=1 - 0.2 / h, ha="left", va="top", fontsize=13, fontweight="bold")
    fig.text(0.01, 1 - 0.55 / h, subtitle.format(avg=np.mean(overlaps)), ha="left", va="top", fontsize=10, color=INK2)
    # fixed margins (tight_layout can't fit long names here and only emits a warning)
    fig.subplots_adjust(left=0.085, right=0.99, top=1 - 1.1 / fig.get_figheight(), bottom=0.07, wspace=1.05, hspace=0.8)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig
