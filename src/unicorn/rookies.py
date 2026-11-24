"""Segment 5 (rookies): one table per pool, with the 15 style measures (D57).

A pool is everyone who played in one setting: a year's summer leagues (all combined, D56), a preseason,
or a regular season (optionally split by team stint, D51). Style is the box score plus shot diet (D49 revised).

Combining leagues or games: counts are added up; rates that NBA.com gives as percentages are rebuilt from
weighted parts and divided by the summed weight (D57):
  * team-context rates (usage, assist %, offensive and defensive rebound %) are weighted by possessions;
  * shares with an exact denominator are pooled exactly: self-created makes by field goals made,
    fast-break points by points.
The same 15 rates as segment 2's play-style groups (`unicorn.style_history.STYLE`).
"""

from pathlib import Path

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayershotlocations, leaguedashplayerstats, leaguegamelog

from unicorn.raw import fetch
from unicorn.style_history import STYLE

# NBA.com league codes for the summer leagues (league 13 has no 2015 data; Orlando, 14, last ran before 2026)
SUMMER_LEAGUES = {"13": "California", "14": "Orlando", "15": "Las Vegas", "16": "Utah"}
SHOT_ZONE_MEASURES = ["rim_rate", "paint_non_ra_rate", "mid_rate", "corner3_share"]   # dropped in the box-score-only check (D49)
BOX_ONLY = [c for c in STYLE if c not in SHOT_ZONE_MEASURES]
ZONES = {"Restricted Area__FGA": "ra_fga", "In The Paint (Non-RA)__FGA": "paint_fga", "Mid-Range__FGA": "mid_fga",
         "Corner 3__FGA": "corner3_fga", "Above the Break 3__FGA": "atb3_fga"}
COUNTS = ["min", "fgm", "fga", "fg3a", "fta", "stl", "blk", "pf", "pts", "poss", *[z for z in ZONES.values()],
          "usg_w", "ast_w", "oreb_w", "dreb_w", "uast_w", "fb_w", "tov_w"]


def _one(season, **kw):
    """Totals for one league or season type (optionally one team), one row per player."""
    g = fetch(leaguegamelog.LeagueGameLog, season=season, player_or_team_abbreviation="P",
              **{k: v for k, v in kw.items() if k in ("league_id", "season_type_all_star", "date_to_nullable")})["LeagueGameLog"]
    dash = {k.replace("league_id", "league_id_nullable"): v for k, v in kw.items()}
    if "team_id_nullable" in dash:
        g = g[g["TEAM_ID"].astype(str) == dash["team_id_nullable"]]
    box = g.groupby("PLAYER_ID").agg(player_name=("PLAYER_NAME", "last"), games=("GAME_ID", "nunique"),
                                     **{c.lower(): (c, "sum") for c in ["MIN", "FGM", "FGA", "FG3A", "FTA", "STL", "BLK", "PF", "PTS"]})
    lds = lambda m: fetch(leaguedashplayerstats.LeagueDashPlayerStats, season=season, measure_type_detailed_defense=m,
                          per_mode_detailed="Totals", **dash)["LeagueDashPlayerStats"].set_index("PLAYER_ID")
    adv = lds("Advanced")[["POSS", "USG_PCT", "AST_PCT", "OREB_PCT", "DREB_PCT", "TM_TOV_PCT"]]
    sco = lds("Scoring")[["PCT_UAST_FGM", "PCT_PTS_FB"]]
    shots = fetch(leaguedashplayershotlocations.LeagueDashPlayerShotLocations, season=season, distance_range="By Zone",
                  per_mode_detailed="Totals", **dash)["ShotLocations"].set_index("PLAYER_ID").rename(columns=ZONES)[list(ZONES.values())]
    d = box.join(adv).join(sco).join(shots)
    d[list(ZONES.values())] = d[list(ZONES.values())].fillna(0)
    d["poss"] = d.pop("POSS")
    d["usg_w"], d["ast_w"] = d["USG_PCT"] * d["poss"], d["AST_PCT"] * d["poss"]
    d["oreb_w"], d["dreb_w"] = d["OREB_PCT"] * d["poss"], d["DREB_PCT"] * d["poss"]
    d["uast_w"], d["fb_w"] = d["PCT_UAST_FGM"] * d["fgm"], d["PCT_PTS_FB"] * d["pts"]
    d["tov_w"] = d["TM_TOV_PCT"] * d["poss"]   # for the position model (D5) only; not one of the 15 style measures
    d.index.name = "player_id"
    return d[["player_name", "games", *COUNTS]]


def rates(t):
    """The 15 style rates from pooled totals. A zero denominator means the action did not happen, so the rate is 0
    (D62); a rate stays missing only when its data does not exist (D61)."""
    safe = lambda a, b: (a / b.where(b > 0)).mask(b.eq(0) & a.notna(), 0.0)
    return pd.DataFrame({
        "rim_rate": safe(t["ra_fga"], t["fga"]), "paint_non_ra_rate": safe(t["paint_fga"], t["fga"]),
        "mid_rate": safe(t["mid_fga"], t["fga"]), "fg3a_rate": safe(t["fg3a"], t["fga"]),
        "corner3_share": safe(t["corner3_fga"], t["fg3a"]), "fta_rate": safe(t["fta"], t["fga"]),
        "usg_pct": safe(t["usg_w"], t["poss"]), "pct_uast_fgm": safe(t["uast_w"], t["fgm"]),
        "ast_pct": safe(t["ast_w"], t["poss"]), "pct_pts_fb": safe(t["fb_w"], t["pts"]),
        "oreb_pct": safe(t["oreb_w"], t["poss"]), "dreb_pct": safe(t["dreb_w"], t["poss"]),
        "blk_per100": safe(100 * t["blk"], t["poss"]), "stl_per100": safe(100 * t["stl"], t["poss"]),
        "pf_per36": safe(36 * t["pf"], t["min"]), "tm_tov_pct": safe(t["tov_w"], t["poss"])}, index=t.index)[[*STYLE, "tm_tov_pct"]]


def _finish(parts):
    t = pd.concat(parts)
    t.index = t.index.astype(int)
    names = t.groupby(level=0)["player_name"].last()
    t = t.groupby(level=0)[["games", *COUNTS]].sum()
    t.insert(0, "player_name", names)
    return pd.concat([t, rates(t)], axis=1)


def summer_pool(season):
    """Every summer league held in `season` (e.g. "2026-27" = July 2026), combined (D56)."""
    parts = []
    for lid, name in SUMMER_LEAGUES.items():
        part = _one(season, league_id=lid)
        if len(part):
            parts.append(part.assign(leagues=name))
    leagues = pd.concat(parts)["leagues"]
    leagues = leagues.groupby(leagues.index.astype(int)).agg(", ".join)
    return _finish([p.drop(columns="leagues") for p in parts]).join(leagues)


def preseason_pool(season):
    return _finish([_one(season, season_type_all_star="Pre Season")])


def regular_pool(season, through=None):
    """A regular season, one row per player (all teams combined). `through` (a date) cuts it at that night,
    for the season in progress; the cut is part of the cache key, so a dated snapshot never changes."""
    kw = {"season_type_all_star": "Regular Season"}
    if through is not None:
        kw["date_to_nullable"] = pd.Timestamp(through).strftime("%m/%d/%Y")
    return _finish([_one(season, **kw)])


def regular_stints(season):
    """A completed regular season split by team stint (D51): one row per (player, team)."""
    g = fetch(leaguegamelog.LeagueGameLog, season=season, player_or_team_abbreviation="P",
              season_type_all_star="Regular Season")["LeagueGameLog"]
    parts = []
    for tid in sorted(g["TEAM_ID"].unique()):
        t = _finish([_one(season, season_type_all_star="Regular Season", team_id_nullable=str(tid))])
        parts.append(t.assign(team_id=tid).reset_index())
    return pd.concat(parts, ignore_index=True).set_index(["player_id", "team_id"])


# ---------------------------------------------------------------- size (D58)

def _bio(**kw):
    from nba_api.stats.endpoints import leaguedashplayerbiostats
    b = fetch(leaguedashplayerbiostats.LeagueDashPlayerBioStats, per_mode_simple="Totals", **kw)["LeagueDashPlayerBioStats"]
    b = b.assign(height_in=pd.to_numeric(b["PLAYER_HEIGHT_INCHES"], errors="coerce"),
                 weight_lb=pd.to_numeric(b["PLAYER_WEIGHT"], errors="coerce"))
    b = b[(b["height_in"] > 0) & (b["weight_lb"] > 0)]
    return b.drop_duplicates("PLAYER_ID").set_index("PLAYER_ID")[["height_in", "weight_lb"]]


def nba_sizes(near_season_start):
    """Each player's listed size from the NBA regular season nearest to the given season (NBA.com, D58 step 2)."""
    import glob, gzip, json
    from unicorn.raw import RAW_DIR
    rows = []
    for f in glob.glob(str(RAW_DIR / "LeagueDashPlayerBioStats" / "per_mode_simple=Totals__season=*.json.gz")):
        rs = json.load(gzip.open(f, "rt"))["response"]["resultSets"][0]
        d = pd.DataFrame(rs["rowSet"], columns=rs["headers"]).assign(season_start=int(f.split("season=")[1][:4]))
        rows.append(d)
    b = pd.concat(rows)
    b["height_in"] = pd.to_numeric(b["PLAYER_HEIGHT_INCHES"], errors="coerce")
    b["weight_lb"] = pd.to_numeric(b["PLAYER_WEIGHT"], errors="coerce")
    b = b[(b["height_in"] > 0) & (b["weight_lb"] > 0)].assign(gap=lambda d: (d["season_start"] - near_season_start).abs())
    return b.sort_values("gap").drop_duplicates("PLAYER_ID").set_index("PLAYER_ID")[["height_in", "weight_lb"]]


def attach_sizes(pool, listing, season_start, extra=None):
    """Size in D58's order: the pool's own listing, then the nearest NBA season, then `extra` (combine,
    Basketball-Reference; a frame indexed by player_id with height_in, weight_lb, source). Missing = left out."""
    out = pool.copy()
    out[["height_in", "weight_lb"]] = listing.reindex(out.index).to_numpy()
    out["size_source"] = out["height_in"].notna().map({True: "pool listing", False: None})
    steps = [(nba_sizes(season_start), "NBA regular season")]
    if extra is not None:
        steps.append((extra, None))
    for table, label in steps:
        gap = out["height_in"].isna() & out.index.isin(table.index)
        out.loc[gap, ["height_in", "weight_lb"]] = table.loc[out.index[gap], ["height_in", "weight_lb"]].to_numpy()
        out.loc[gap, "size_source"] = label if label else table.loc[out.index[gap], "source"].to_numpy()
    return out


# ---------------------------------------------------------------- the map (D5) and uniqueness (D50, D57, D60)

def _z(pool, cols):
    return (pool[cols] - pool[cols].mean()) / pool[cols].std()


def add_map(pool, last_train_season):
    """Body and style positions (1-5) from the D5 models, fitted on regular seasons up to `last_train_season`;
    the pool's measures are standardised within the pool."""
    from sklearn.linear_model import RidgeCV
    from unicorn.position import ALPHAS, BODY_FEATURES, FIT_MIN, STYLE_FEATURES
    ps = pd.read_parquet(Path(__file__).resolve().parents[2] / "data" / "processed" / "player_season_unicorn.parquet")
    train = ps[(ps["position_source"] == "roster") & (ps["min"] >= FIT_MIN) & ps["position_num"].notna()
               & (ps["season_start"] <= last_train_season)]
    out = pool.copy()
    for name, feats in [("position_body", BODY_FEATURES), ("position_style", STYLE_FEATURES)]:
        base = [f[:-2] for f in feats]
        fit = train.dropna(subset=feats)                          # D61: rows with missing data are dropped, not filled
        model = RidgeCV(alphas=ALPHAS).fit(fit[feats].to_numpy(), fit["position_num"])
        Z = _z(out, base)
        ok = Z.notna().all(axis=1)
        out[name] = np.nan
        out.loc[ok, name] = np.clip(model.predict(Z[ok].to_numpy()), 1, 5)
    out["style_vs_body"] = out["position_style"] - out["position_body"]   # <0: plays smaller than his body
    return out


def _mahalanobis_tail(Z, cov):
    """Chi-square tail probability of each row's Mahalanobis distance, on the measures the row has (D60)."""
    from scipy.stats import chi2
    p = np.full(len(Z), np.nan)
    d2s = np.full(len(Z), np.nan)
    for i, z in enumerate(Z):
        ok = ~np.isnan(z)
        if ok.sum() == 0:
            continue
        sub = cov[np.ix_(ok, ok)]
        d2 = float(z[ok] @ np.linalg.pinv(sub) @ z[ok])
        d2s[i], p[i] = d2, chi2.sf(d2, ok.sum())
    return d2s, p


def add_uniqueness(pool, measures=STYLE):
    """Uniqueness on style and size together, plus each part alone (D50, D57, D60).
    Players without a size are left out (D58). Higher percentile = stands out more from the pool."""
    out = pool.copy()
    has = out["height_in"].notna() & out["weight_lb"].notna()
    parts = {"uniqueness": [*measures, "height_in", "weight_lb"], "uniqueness_style": list(measures),
             "uniqueness_size": ["height_in", "weight_lb"]}
    for name, cols in parts.items():
        sub = out.loc[has, cols]
        Z = ((sub - sub.mean()) / sub.std()).to_numpy(dtype=float)
        cov = pd.DataFrame(Z).cov(min_periods=10).to_numpy()   # pairwise: each pair of measures on the players who have both
        d2, p = _mahalanobis_tail(Z, cov)
        out[name + "_d2"] = pd.Series(d2, index=sub.index)
        tail = pd.Series(p, index=sub.index)
        out[name + "_pctl"] = (1 - tail).rank(pct=True) * 100
    return out


# ---------------------------------------------------------------- reasons and charts

def reasons(pool, ids, n=2):
    """Plain words for what makes each player stand out in his pool: his n most unusual style measures and his size,
    each in standard deviations from the pool's average (descriptive, not a model)."""
    from unicorn.archetypes import SHORT
    z = _z(pool, [*STYLE, "height_in", "weight_lb"])
    out = {}
    for pid in ids:
        if pid not in z.index:
            continue
        r = z.loc[pid]
        style = r[STYLE].dropna().abs().sort_values(ascending=False).index[:n]
        words = [f"{SHORT[c]} {'high' if r[c] > 0 else 'low'} ({r[c]:+.1f} SD)" for c in style]
        if pd.notna(r["height_in"]):
            words.append(f"height {r['height_in']:+.1f} SD, weight {r['weight_lb']:+.1f} SD")
        out[pid] = "; ".join(words)
    return pd.Series(out, name="what stands out")


def plot_maps(pools, picks, title, path):
    """Body position (x) against style position (y), one panel per pool; picks labelled, everyone else muted."""
    import matplotlib.pyplot as plt
    from adjustText import adjust_text
    from unicorn.plotting import BLUE, INK, INK2, MUTED, apply_style
    apply_style()
    fig, axes = plt.subplots(1, len(pools), figsize=(5.2 * len(pools), 5.4), sharex=True, sharey=True)
    for ax, (label, p) in zip(np.atleast_1d(axes), pools.items()):
        ok = p["position_body"].notna() & p["position_style"].notna()
        rest, mine = p[ok & ~p.index.isin(picks)], p[ok & p.index.isin(picks)]
        ax.plot([1, 5], [1, 5], ls="--", lw=1, color=INK2, zorder=1)
        ax.scatter(rest["position_body"], rest["position_style"], s=10, color=MUTED, alpha=0.6, lw=0, zorder=2)
        ax.scatter(mine["position_body"], mine["position_style"], s=46, color=BLUE, edgecolor="white", lw=1.2, zorder=3)
        texts = [ax.text(r["position_body"], r["position_style"], picks[i], fontsize=8, color=INK) for i, r in mine.iterrows()]
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.5))
        ax.set_title(f"{label}\n{ok.sum()} players with a size and style", fontsize=10)
        ax.set_xlim(0.8, 5.2); ax.set_ylim(0.8, 5.2)
        ax.set_xlabel("body position (1 guard → 5 centre), from height and weight")
    np.atleast_1d(axes)[0].set_ylabel("style position (1 guard → 5 centre), from how he plays")
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.text(0.01, -0.04, "Blue dots = lottery picks; grey = everyone else in that pool. On the dashed line: he plays the position his body "
             "suggests. Below it: he plays smaller than his body; above it: bigger.", fontsize=8.5, color=INK2)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


def plot_uniqueness(table, pools, title, path):
    """Uniqueness percentile of each pick in each pool: one row per pick, one marker per pool."""
    import matplotlib.pyplot as plt
    from unicorn.plotting import INK2, SERIES, apply_style
    apply_style()
    t = table.sort_values(pools[-1])
    fig, ax = plt.subplots(figsize=(8.5, 0.36 * len(t) + 1.6))
    y = np.arange(len(t))
    for i, (pool, marker) in enumerate(zip(pools, ["o", "s", "D", "^"])):
        ax.scatter(t[pool], y, s=52, marker=marker, color=SERIES[i], edgecolor="white", lw=1.2, zorder=3, label=pool)
    for yi, (_, r) in zip(y, t.iterrows()):
        vals = r[pools].dropna()
        if len(vals) > 1:
            ax.plot([vals.min(), vals.max()], [yi, yi], color=INK2, lw=0.8, alpha=0.5, zorder=2)
    ax.set_yticks(y, t.index); ax.set_xlim(0, 100); ax.grid(axis="y", visible=False)
    ax.set_xlabel("uniqueness percentile within the pool (100 = stands out most in style and size together)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=len(pools), frameon=False, fontsize=8.5)
    ax.set_title(title, loc="left", pad=28)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


def plot_parts(pool, picks, title, path):
    """What drives uniqueness: style part (x) against size part (y), percentiles within the pool."""
    import matplotlib.pyplot as plt
    from adjustText import adjust_text
    from unicorn.plotting import BLUE, INK, INK2, MUTED, apply_style
    apply_style()
    ok = pool["uniqueness_style_pctl"].notna() & pool["uniqueness_size_pctl"].notna()
    rest, mine = pool[ok & ~pool.index.isin(picks)], pool[ok & pool.index.isin(picks)]
    fig, ax = plt.subplots(figsize=(6.4, 6))
    ax.scatter(rest["uniqueness_style_pctl"], rest["uniqueness_size_pctl"], s=10, color=MUTED, alpha=0.6, lw=0)
    ax.scatter(mine["uniqueness_style_pctl"], mine["uniqueness_size_pctl"], s=46, color=BLUE, edgecolor="white", lw=1.2, zorder=3)
    texts = [ax.text(r["uniqueness_style_pctl"], r["uniqueness_size_pctl"], picks[i], fontsize=8, color=INK) for i, r in mine.iterrows()]
    adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.5))
    ax.axvline(50, color=INK2, lw=0.6, ls=":"); ax.axhline(50, color=INK2, lw=0.6, ls=":")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.set_xlabel("style uniqueness percentile"); ax.set_ylabel("size uniqueness percentile")
    ax.set_title(title, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


# ---------------------------------------------------------------- Stage 2: play-style groups on team stints (D51, D64)

STINT_MIN_MINUTES = 500


def load_stints(min_minutes=STINT_MIN_MINUTES):
    """Team stints 2000-01 to 2025-26 with 500+ minutes (D64), each style measure standardised within its season."""
    d = pd.read_parquet(Path(__file__).resolve().parents[2] / "data" / "processed" / "style_stints_2000_2026.parquet")
    d = d[d["min"] >= min_minutes].copy()
    z = d.groupby("season_start")[STYLE].transform(lambda c: (c - c.mean()) / c.std())
    d[[f"{c}_z" for c in STYLE]] = z.to_numpy()
    return d.reset_index(drop=True)
