"""Interactive dashboard: tune star weights and breakout thresholds, see who qualifies.

Run from the project root:  streamlit run dashboard/app.py
Uses the same definitions as the notebooks (unicorn.labels); defaults reproduce them exactly.
"""

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from unicorn import labels as L
from unicorn.raw import PROJECT_ROOT

st.set_page_config(page_title="Unicorn & Breakout Lab", layout="wide")

BLUE, ORANGE, AQUA, YELLOW, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#8a8984"
TYPE_COLORS = {"scoring": BLUE, "role": ORANGE, "production": AQUA}
PILLARS = list(L.STAR_PILLARS)
DEFAULTS = {
    **{f"w_{p}": 1.0 for p in PILLARS},
    "size_adjustment": L.SIZE_ADJUSTMENT, "star_top_pct": round(100 * (1 - L.STAR_SCORE_PCTL)), "star_min": L.STAR_MIN,
    "tier_top_pct": round(100 * (1 - L.STAR_TIER_PCTL)), "steady_min_rise": L.STEADY_MIN_RISE,
    **L.BREAKOUT_RULES,
}


# ---------------------------------------------------------------- data (slow parts, cached once)
@st.cache_data(show_spinner="Loading player seasons…")
def load_base():
    uni = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "player_season_unicorn.parquet")
    base = L.label_inputs(uni)
    raw, adjusted = L.star_pillars(base)
    base["group"] = pd.cut(base["position_num"], [0, 2.0, 3.5, 5.0], labels=["guards", "forwards", "bigs"]).astype(str)
    return base, raw, adjusted


def compute(base, raw, adjusted, s):
    rules = {k: s[k] for k in L.BREAKOUT_RULES}
    df = L.apply_breakout_rules(base, **rules)
    df = L.apply_star_score(df, raw, adjusted, weights={p: s[f"w_{p}"] for p in PILLARS},
                            size_adjustment=s["size_adjustment"], star_pctl_cut=1 - s["star_top_pct"] / 100,
                            star_min=s["star_min"])
    return L.add_star_routes(df, tier=1 - s["tier_top_pct"] / 100, min_rise=s["steady_min_rise"])


@st.cache_data(show_spinner=False)
def compute_cached(settings_items):
    base, raw, adjusted = load_base()
    return compute(base, raw, adjusted, dict(settings_items))


# ---------------------------------------------------------------- sidebar controls
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v


with st.sidebar:
    st.header("Settings")
    st.button("Reset to project defaults", on_click=reset, width="stretch")

    with st.expander("Star score: pillar weights", expanded=True):
        st.caption("Star score = weighted mean of six pillars (season-relative z-scores).")
        for p in PILLARS:
            st.slider(p, 0.0, 3.0, step=0.25, key=f"w_{p}")
        st.slider("size-fairness dial", 0.0, 1.0, step=0.05, key="size_adjustment",
                  help="0 = raw pillars; 1 = each pillar judged only against players of the same body size")

    with st.expander("Star definitions"):
        st.slider("star season = top X% of eligible players", 1, 20, step=1, key="star_top_pct")
        st.slider("minutes needed to be eligible (scaled to 82 games)", 800, 2500, step=100, key="star_min")
        st.slider("star tier (routes) = top X%", 5, 25, step=1, key="tier_top_pct")
        st.slider("steady route: minimum climb (percentile points)", 0.0, 0.3, step=0.01, key="steady_min_rise")

    with st.expander("Breakout rules"):
        st.slider("breakout season needs ≥ minutes (scaled)", 600, 2000, step=100, key="real_season_min")
        st.markdown("**Scoring**")
        st.slider("+ppg vs own past", 2.0, 10.0, step=0.5, key="scoring_ppg")
        st.slider("ppg at least", 8.0, 25.0, step=1.0, key="scoring_level")
        st.markdown("**Role**")
        st.slider("+minutes per game vs own past", 2.0, 12.0, step=0.5, key="role_mpg")
        st.slider("usage rise (SD) vs own past", 0.0, 1.5, step=0.1, key="role_usg")
        st.markdown("**Production**")
        st.slider("impact jump beyond normal for age (SD)", 0.25, 2.0, step=0.05, key="production_excess")
        st.slider("impact level at least (z)", -0.5, 2.0, step=0.1, key="production_level")
        st.markdown("**Efficiency (scoring & role)**")
        st.slider("shrunk TS% may fall at most (SD)", -1.5, 0.0, step=0.1, key="efficiency_floor")

settings = {k: st.session_state[k] for k in DEFAULTS}
df = compute_cached(tuple(sorted(settings.items())))
ref = compute_cached(tuple(sorted(DEFAULTS.items())))
changed = [k for k in DEFAULTS if settings[k] != DEFAULTS[k]]

st.title("Unicorn & Breakout Lab")
st.caption("Tune the definitions and see who counts as a star or a breakout. "
           + (f"**Changed from defaults:** {', '.join(changed)}" if changed else "Showing project defaults."))

seasons = sorted(df["season"].unique())
tab_stars, tab_brk, tab_player, tab_routes, tab_pred = st.tabs(
    ["⭐ Stars", "🚀 Breakouts", "👤 Player", "🛣️ Routes to stardom", "🎯 Predictability"])


# ---------------------------------------------------------------- stars
with tab_stars:
    season = st.selectbox("Season", seasons, index=len(seasons) - 1, key="star_season_pick")
    stars = df[df["star_season"]]
    ref_stars = ref[ref["star_season"]]
    rot = df[df["min_scaled"] >= settings["star_min"]]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Star seasons (all years)", len(stars), len(stars) - len(ref_stars) or None)
    c2.metric("Different players", stars["player_id"].nunique(), stars["player_id"].nunique() - ref_stars["player_id"].nunique() or None)
    mix = stars["group"].value_counts(normalize=True)
    base_mix = rot["group"].value_counts(normalize=True)
    c3.metric("Guards among stars", f"{mix.get('guards', 0):.0%}", help=f"{base_mix.get('guards', 0):.0%} of eligible players")
    c4.metric("Bigs among stars", f"{mix.get('bigs', 0):.0%}", help=f"{base_mix.get('bigs', 0):.0%} of eligible players")

    left, right = st.columns([3, 2])
    with left:
        st.subheader(f"Top 25 by star score, {season}")
        s = df[(df["season"] == season) & (df["min_scaled"] >= settings["star_min"])].nlargest(25, "star_score").copy()
        r = ref[(ref["season"] == season) & (ref["min_scaled"] >= DEFAULTS["star_min"])]
        r = r.assign(default_rank=r["star_score"].rank(ascending=False))[["player_id", "default_rank"]]
        s = s.merge(r, on="player_id", how="left")
        s["rank"] = np.arange(1, len(s) + 1)
        s["vs default"] = (s["default_rank"] - s["rank"]).map(lambda x: "new" if pd.isna(x) else (f"▲{x:.0f}" if x > 0 else (f"▼{-x:.0f}" if x < 0 else "–")))
        show = ["rank", "player_name", "team_abbreviation", "age", "star_score", "star_season", "vs default"] + [f"pillar_{p}" for p in PILLARS]
        st.dataframe(s[show].rename(columns=lambda c: c.replace("pillar_", "")), hide_index=True, width="stretch",
                     column_config={"star_score": st.column_config.NumberColumn(format="%.2f"),
                                    **{p: st.column_config.NumberColumn(format="%.2f") for p in PILLARS},
                                    "age": st.column_config.NumberColumn(format="%.1f")})
    with right:
        st.subheader("Most star seasons, 2011-12 → 2025-26")
        counts = stars.groupby("player_name").size().rename("now")
        counts = pd.concat([counts, ref_stars.groupby("player_name").size().rename("default")], axis=1).fillna(0).astype(int)
        top = counts.sort_values(["now", "default"], ascending=False).head(20).reset_index(names="player")
        chart = alt.Chart(top).mark_bar(color=BLUE, cornerRadiusEnd=3).encode(
            x=alt.X("now:Q", title="star seasons (your settings)"),
            y=alt.Y("player:N", sort="-x", title=None),
            tooltip=["player", alt.Tooltip("now:Q", title="your settings"), alt.Tooltip("default:Q", title="defaults")])
        ticks = alt.Chart(top).mark_tick(color=GRAY, thickness=2, size=14).encode(x="default:Q", y=alt.Y("player:N", sort="-x"))
        st.altair_chart(chart + ticks, width="stretch")
        st.caption("Gray tick = number under project defaults.")

    st.subheader("Who gains or loses star seasons vs the defaults")
    diff = counts.assign(change=counts["now"] - counts["default"]).query("change != 0").sort_values("change")
    if diff.empty:
        st.info("No change: same star seasons as the defaults.")
    else:
        g1, g2 = st.columns(2)
        g1.markdown("**Gains**"); g1.dataframe(diff[diff["change"] > 0].sort_values("change", ascending=False), width="stretch")
        g2.markdown("**Losses**"); g2.dataframe(diff[diff["change"] < 0], width="stretch")


# ---------------------------------------------------------------- breakouts
TYPES = {"scoring": "breakout_scoring", "role": "breakout_role", "production": "breakout_production"}
with tab_brk:
    per = df.groupby("season")[list(TYPES.values())].sum().rename(columns={v: k for k, v in TYPES.items()})
    per_long = per.reset_index().melt("season", var_name="type", value_name="count")
    c1, c2, c3 = st.columns(3)
    c1.metric("Breakout seasons (any type)", int(df["breakout_any"].sum()), int(df["breakout_any"].sum() - ref["breakout_any"].sum()) or None)
    mip_hit = df.loc[df["mip"], "breakout_any"]
    c2.metric("Most Improved winners captured", f"{int(mip_hit.sum())}/{len(mip_hit)}")
    c3.metric("Players aged ≤ 25 breaking out, per season", f"{df.loc[df['age'] <= 25, 'breakout_any'].mean():.1%}")
    missed = df.loc[df["mip"] & ~df["breakout_any"], ["season", "player_name"]]
    if len(missed):
        st.caption("Most Improved winners not captured: " + ", ".join(f"{n} ({s})" for s, n in missed.values))

    st.altair_chart(alt.Chart(per_long).mark_bar().encode(
        x=alt.X("season:N", title=None), y=alt.Y("count:Q", title="breakout seasons (a player can count in several types)"),
        color=alt.Color("type:N", scale=alt.Scale(domain=list(TYPE_COLORS), range=list(TYPE_COLORS.values())), title="type"),
        xOffset="type:N", tooltip=["season", "type", "count"]).properties(height=260), width="stretch")

    season_b = st.selectbox("Season", seasons, index=len(seasons) - 1, key="brk_season_pick")
    cols = ["player_name", "team_abbreviation", "age", "ppg", "ppg_vs_past", "min_per_game", "min_per_game_vs_past",
            "usg_pct_z_vs_past", "ts_pct_shr_z_vs_past", "pie_excess_vs_age", "pie_z", "min_scaled"]
    now_s = df[(df["season"] == season_b)]
    ref_s = ref[(ref["season"] == season_b)].set_index("player_id")["breakout_any"]
    b = now_s[now_s["breakout_any"]].copy()
    b["types"] = [", ".join(t for t, c in TYPES.items() if r[c]) for _, r in b.iterrows()]
    b["vs default"] = b["player_id"].map(ref_s).map({True: "", False: "new"})
    st.subheader(f"Breakouts in {season_b} ({len(b)})")
    st.dataframe(b[["player_name", "types", "vs default"] + cols[1:]].sort_values("ppg_vs_past", ascending=False),
                 hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(format="%.2f") for c in cols[2:]})
    dropped = now_s[now_s["player_id"].map(ref_s).fillna(False).astype(bool) & ~now_s["breakout_any"]]
    if len(dropped):
        st.caption("Breakouts under the defaults that no longer count: " + ", ".join(dropped["player_name"]))

    st.subheader("Near misses: failed exactly one condition")
    r = settings
    real = now_s["min_scaled"] >= r["real_season_min"]
    eff = now_s["ts_pct_shr_z_vs_past"] >= r["efficiency_floor"]
    conds = {
        "scoring": {"minutes": real, "+ppg": now_s["ppg_vs_past"] >= r["scoring_ppg"], "ppg level": now_s["ppg"] >= r["scoring_level"], "efficiency": eff},
        "role": {"minutes": real, "+min/game": now_s["min_per_game_vs_past"] >= r["role_mpg"], "usage": now_s["usg_pct_z_vs_past"] >= r["role_usg"], "efficiency": eff},
        "production": {"minutes": real, "impact jump": now_s["pie_excess_vs_age"] >= r["production_excess"], "impact level": now_s["pie_z"] >= r["production_level"]},
    }
    near = []
    for t, cs in conds.items():
        m = pd.DataFrame(cs)
        one_off = (~m).sum(axis=1) == 1
        for idx in now_s.index[one_off & ~now_s[TYPES[t]]]:
            near.append({"player": now_s.at[idx, "player_name"], "type": t, "failed": m.columns[~m.loc[idx].to_numpy()][0],
                         "ppg": now_s.at[idx, "ppg"], "+ppg": now_s.at[idx, "ppg_vs_past"],
                         "+min/game": now_s.at[idx, "min_per_game_vs_past"], "usage Δ": now_s.at[idx, "usg_pct_z_vs_past"],
                         "efficiency Δ": now_s.at[idx, "ts_pct_shr_z_vs_past"], "impact jump": now_s.at[idx, "pie_excess_vs_age"]})
    near = pd.DataFrame(near)
    if near.empty:
        st.info("No near misses this season.")
    else:
        near = near[~near["player"].isin(b["player_name"])]
        st.dataframe(near, hide_index=True, width="stretch",
                     column_config={c: st.column_config.NumberColumn(format="%.2f") for c in near.columns[3:]})


# ---------------------------------------------------------------- player
with tab_player:
    names = sorted(df["player_name"].unique())
    name = st.selectbox("Player", names, index=names.index("Shai Gilgeous-Alexander"))
    p = df[df["player_name"] == name].sort_values("season_start").copy()
    p["types"] = [", ".join(t for t, c in TYPES.items() if r[c]) for _, r in p.iterrows()]
    tier = 1 - settings["tier_top_pct"] / 100
    line = alt.Chart(p).mark_line(point=True, color=BLUE).encode(
        x=alt.X("season:N", title=None), y=alt.Y("star_pctl:Q", title="star percentile", scale=alt.Scale(domain=[0, 1])),
        tooltip=["season", alt.Tooltip("star_pctl:Q", format=".2f"), alt.Tooltip("star_score:Q", format=".2f"), "types"])
    rings = alt.Chart(p[p["breakout_any"]]).mark_point(size=260, shape="circle", filled=False, strokeWidth=2.5, color=ORANGE).encode(
        x="season:N", y="star_pctl:Q", tooltip=["season", "types"])
    band = alt.Chart(pd.DataFrame({"y": [tier]})).mark_rule(strokeDash=[4, 4], color=GRAY).encode(y="y:Q")
    st.altair_chart((band + line + rings).properties(height=300), width="stretch")
    st.caption(f"Orange rings = breakout seasons under your rules. Dashed line = star tier (top {settings['tier_top_pct']}%). "
               "Seasons below the eligibility minutes have no percentile.")
    show = ["season", "team_abbreviation", "age", "min_per_game", "ppg", "star_score", "star_pctl", "star_season", "types",
            "route_steady", "route_breakout"] + [f"pillar_{x}" for x in PILLARS]
    st.dataframe(p[show].rename(columns=lambda c: c.replace("pillar_", "")), hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(format="%.2f") for c in ["age", "min_per_game", "ppg", "star_score", "star_pctl", *PILLARS]})


# ---------------------------------------------------------------- routes
with tab_routes:
    st.caption(f"Players aged ≤ 25 not yet in the star tier (top {settings['tier_top_pct']}%) who reach it within 3 seasons. "
               "Breakout route = at least one breakout season on the way; steady route = none, with a climb of at least "
               f"{settings['steady_min_rise']:.2f} percentile points.")
    pop = (df["age"] <= 25) & ~df["star_tier"] & (df["season_start"] + 3 <= df["season_start"].max())
    c1, c2 = st.columns(2)
    for col, route, label in [(c1, "route_steady", "Steady route"), (c2, "route_breakout", "Breakout route")]:
        first = df[pop & df[route]].groupby("player_name")["season"].min().sort_values()
        col.subheader(f"{label} ({len(first)} players)")
        col.dataframe(first.rename("first flagged from").reset_index(), hide_index=True, width="stretch")


# ---------------------------------------------------------------- predictability
with tab_pred:
    st.markdown("Re-run the **walk-forward backtest** for *any breakout next season* with your current rules "
                "(boosted trees vs current star score; predictions 2014-15 → 2024-25; about 20 seconds).")

    @st.cache_data(show_spinner="Running walk-forward backtest…")
    def run_backtest(settings_items):
        from unicorn.backtest import boosted_trees, evaluate, feature_columns, rule, walk_forward
        d = L.add_future(compute_cached(settings_items), ["breakout_any"], horizon=1)
        P = walk_forward(d, "breakout_any_next1", 1, d["age"] <= 25, 2014, 2024,
                         {"boosted trees": boosted_trees, "current star score": rule(lambda x: x["star_score"].fillna(-9))},
                         feature_columns(d))
        hits = (P.sort_values("score", ascending=False).groupby(["model", "test_season"]).head(10)
                .groupby(["model", "test_season"])["outcome"].sum().unstack("model"))
        return evaluate(P)[["positives", "base_rate", "ROC_AUC", "avg_precision", "AP_lift", "precision@10", "recall@25"]], hits

    if st.button("Run backtest with my settings", type="primary"):
        st.session_state["bt"] = (run_backtest(tuple(sorted(settings.items()))), dict(settings))
    if "bt" in st.session_state:
        (summary, hits), used = st.session_state["bt"]
        if used != settings:
            st.warning("Settings changed since this run; press the button again to update.")
        st.dataframe(summary.style.format({"base_rate": "{:.1%}", "ROC_AUC": "{:.3f}", "avg_precision": "{:.3f}",
                                           "AP_lift": "{:.2f}×", "precision@10": "{:.0%}", "recall@25": "{:.0%}"}),
                     width="stretch")
        h = hits.reset_index().melt("test_season", var_name="model", value_name="hits in top 10")
        st.altair_chart(alt.Chart(h).mark_line(point=True).encode(
            x=alt.X("test_season:O", title="season predictions were made"), y=alt.Y("hits in top 10:Q", scale=alt.Scale(domain=[0, 10])),
            color=alt.Color("model:N", scale=alt.Scale(range=[BLUE, AQUA])), tooltip=["test_season", "model", "hits in top 10"]
        ).properties(height=260), width="stretch")
        st.caption("Project defaults: boosted trees 4.2× lift, top-10 hit rate 39%.")
