"""Breakout board: each season's top predicted breakout candidates and what actually happened."""

import json

import numpy as np
import pandas as pd

TYPES = {"breakout_scoring": "scoring", "breakout_role": "role", "breakout_production": "production"}


def build_board(lab, preds, top_n=25):
    """Top `top_n` candidates per test season, joined with this-season and next-season context."""
    top = (preds.sort_values(["test_season", "score"], ascending=[True, False])
           .groupby("test_season").head(top_n).copy())
    top["rank"] = top.groupby("test_season").cumcount() + 1
    now = lab[["player_id", "season_start", "team_abbreviation", "age", "exp", "min_per_game", "ppg", "star_score"]]
    nxt = lab[["player_id", "season_start", "team_abbreviation", "min_per_game", "ppg", *TYPES]].copy()
    nxt["season_start"] -= 1
    nxt = nxt.rename(columns={"team_abbreviation": "team_next", "min_per_game": "mpg_next", "ppg": "ppg_next"})
    top = (top.merge(now, left_on=["player_id", "test_season"], right_on=["player_id", "season_start"], how="left")
              .drop(columns="season_start")
              .merge(nxt, left_on=["player_id", "test_season"], right_on=["player_id", "season_start"], how="left")
              .drop(columns="season_start"))
    top["breakout_types"] = [", ".join(name for col, name in TYPES.items() if pd.notna(r[col]) and bool(r[col]))
                             for _, r in top.iterrows()]
    last = preds["test_season"].max()
    top["status"] = np.where(top["test_season"] == last, "pending", np.where(top["outcome"] == 1, "hit", "miss"))
    top["season_label"] = top["test_season"].map(lambda s: f"{s}-{(s + 1) % 100:02d}")
    top["outcome_label"] = top["test_season"].map(lambda s: f"{s + 1}-{(s + 2) % 100:02d}")
    return top


def season_summary(board, preds, k=10):
    rows = []
    for s, g in board.groupby("test_season"):
        all_s = preds[preds["test_season"] == s]
        rows.append({"test_season": s, "season_label": g["season_label"].iloc[0], "outcome_label": g["outcome_label"].iloc[0],
                     "pending": bool((g["status"] == "pending").all()), "pool": len(all_s),
                     "hits_top10": int(g.loc[g["rank"] <= k, "outcome"].sum()),
                     "base_rate": float(all_s["outcome"].mean()),
                     "expected_top10_by_chance": float(all_s["outcome"].mean() * k)})
    return pd.DataFrame(rows)


def board_json(board, summary):
    keep = ["test_season", "rank", "player_name", "team_abbreviation", "team_next", "age", "exp", "min_per_game", "ppg",
            "mpg_next", "ppg_next", "score", "status", "breakout_types"]
    b = board[keep].copy()
    b = b.astype(object).where(b.notna(), None)
    return json.dumps({"rows": b.to_dict("records"), "seasons": summary.to_dict("records")}, default=float)


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Breakout Board</title>
<style>
:root {
  --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink2: #52514e; --muted: #8a8984;
  --line: #e4e3df; --hit: #2a78d6; --hit-soft: #d6e6f9; --miss: #c3c2b7; --miss-soft: #efeee9;
  --pending: #52514e; --focus: #2a78d6;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink2: #c3c2b7; --muted: #8a8984;
    --line: #383835; --hit: #3987e5; --hit-soft: #1d3554; --miss: #5d5c57; --miss-soft: #2a2a28; --pending: #c3c2b7;
  }
}
:root[data-theme="dark"] {
  --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink2: #c3c2b7; --muted: #8a8984;
  --line: #383835; --hit: #3987e5; --hit-soft: #1d3554; --miss: #5d5c57; --miss-soft: #2a2a28; --pending: #c3c2b7;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink);
       font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
main { max-width: 920px; margin: 0 auto; padding: 32px 16px 56px; }
h1 { font-size: 26px; margin: 0 0 6px; letter-spacing: -0.01em; }
.sub { color: var(--ink2); margin: 0 0 24px; max-width: 70ch; }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 18px 18px 14px; margin-bottom: 18px; }
.card h2 { font-size: 14px; text-transform: uppercase; letter-spacing: .06em; color: var(--ink2); margin: 0 0 12px; font-weight: 600; }
.strip { display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 6px; align-items: end; }
.season { background: none; border: 0; padding: 4px 0 0; cursor: pointer; color: var(--ink2); font: inherit; font-size: 11px;
          border-radius: 6px; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.season:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.season .col { position: relative; width: 70%; height: 110px; display: flex; align-items: flex-end; }
.season .bar { width: 100%; background: var(--hit); border-radius: 4px 4px 0 0; min-height: 2px; }
.season .chance { position: absolute; left: -10%; width: 120%; border-top: 2px dashed var(--ink2); }
.season .num { font-weight: 600; color: var(--ink); font-size: 13px; }
.season.pending .bar { background: none; border: 2px dashed var(--muted); border-bottom: 0; height: 100% !important; }
.season[aria-pressed="true"] { background: var(--hit-soft); color: var(--ink); }
.legend { display: flex; flex-wrap: wrap; gap: 16px; color: var(--ink2); font-size: 13px; margin-top: 12px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.sw { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
.sw.dash { border-top: 2px dashed var(--ink2); height: 0; width: 16px; border-radius: 0; }
.head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
.head .title { font-size: 20px; font-weight: 650; }
.head .meta { color: var(--ink2); font-size: 14px; }
.toggle { display: inline-flex; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
.toggle button { background: none; border: 0; padding: 6px 12px; font: inherit; font-size: 13px; color: var(--ink2); cursor: pointer; }
.toggle button[aria-pressed="true"] { background: var(--hit-soft); color: var(--ink); font-weight: 600; }
.toggle button:focus-visible { outline: 2px solid var(--focus); outline-offset: -2px; }
.row { display: grid; grid-template-columns: 28px minmax(0, 1.25fr) minmax(0, 1fr) minmax(0, 1.1fr); gap: 12px; align-items: center;
       padding: 10px 4px; border-top: 1px solid var(--line); }
.row:first-of-type { border-top: 0; }
.rank { color: var(--muted); font-variant-numeric: tabular-nums; text-align: right; }
.name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ctx { color: var(--ink2); font-size: 12.5px; }
.prob { display: flex; align-items: center; gap: 8px; }
.track { flex: 1; height: 10px; background: var(--miss-soft); border-radius: 5px; overflow: hidden; }
.fill { height: 100%; border-radius: 5px; background: var(--ink2); }
.pct { font-variant-numeric: tabular-nums; font-size: 13px; width: 38px; text-align: right; color: var(--ink); }
.chip { display: inline-block; font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.chip.hit { background: var(--hit); color: #fff; }
.chip.miss { background: var(--miss-soft); color: var(--ink2); }
.chip.pending { border: 1.5px dashed var(--muted); color: var(--ink2); }
.after { color: var(--ink2); font-size: 12.5px; margin-top: 3px; }
.note { color: var(--ink2); font-size: 13px; }
.note p { margin: 6px 0; }
@media (max-width: 640px) {
  .row { grid-template-columns: 24px minmax(0, 1fr); }
  .row .prob, .row .result { grid-column: 2; }
  .season { font-size: 9px; }
}
</style>
</head>
<body>
<main>
  <h1>Breakout Board</h1>
  <p class="sub">At the end of each season, a model trained only on earlier seasons ranked every player aged 25 or under by
    their chance of <strong>breaking out the following season</strong> (a scoring, role or all-round production jump
    relative to their own past). Here are its top picks, and what actually happened.</p>

  <section class="card" aria-labelledby="strip-h">
    <h2 id="strip-h">Hits in the top 10, by season (click a season)</h2>
    <div class="strip" id="strip" role="group" aria-label="Choose a season"></div>
    <div class="legend">
      <span><i class="sw" style="background:var(--hit)"></i>top-10 picks who broke out</span>
      <span><i class="sw dash"></i>expected by chance</span>
      <span><i class="sw" style="border:2px dashed var(--muted)"></i>outcome not yet known</span>
    </div>
  </section>

  <section class="card" aria-live="polite">
    <div class="head">
      <div>
        <div class="title" id="title"></div>
        <div class="meta" id="meta"></div>
      </div>
      <div class="toggle" role="group" aria-label="How many candidates">
        <button type="button" data-n="10" aria-pressed="true">Top 10</button>
        <button type="button" data-n="25" aria-pressed="false">Top 25</button>
      </div>
    </div>
    <div id="rows"></div>
  </section>

  <section class="card note">
    <h2>How to read this</h2>
    <p><strong>Probability</strong>: boosted-trees model, walk-forward. Each season's model only saw seasons whose outcomes were already known.
       A typical young player breaks out about 4–13% of the time, depending on the season.</p>
    <p><strong>Breakout</strong> (next season, ≥ 1,200 minutes scaled to 82 games): <em>scoring</em> +5 ppg vs own past at ≥ 15 ppg with efficiency held;
       <em>role</em> +6 min/game and higher usage with efficiency held; <em>production</em> all-round impact far above normal for his age.</p>
    <p>A "miss" can still be a good season: Siakam went from 16.9 to 22.9 ppg in 2019-20 but his efficiency fell, so it doesn't count.</p>
  </section>
</main>
<script>
const DATA = __DATA__;
const seasons = DATA.seasons;
const rowsBySeason = {};
for (const r of DATA.rows) (rowsBySeason[r.test_season] ||= []).push(r);
let current = seasons[seasons.length - 1].test_season, topN = 10;

const fmt = (x, d = 1) => (x === null || x === undefined || Number.isNaN(x)) ? "–" : Number(x).toFixed(d);
const signed = x => (x > 0 ? "+" : "") + fmt(x);

function renderStrip() {
  const strip = document.getElementById("strip");
  strip.style.setProperty("--n", seasons.length);
  strip.innerHTML = "";
  for (const s of seasons) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "season" + (s.pending ? " pending" : "");
    b.setAttribute("aria-pressed", String(s.test_season === current));
    const h = s.pending ? 100 : (s.hits_top10 / 10) * 100;
    const chance = (s.expected_top10_by_chance / 10) * 100;
    b.title = s.pending ? `${s.season_label} → ${s.outcome_label}: outcome not yet known`
      : `${s.season_label} → ${s.outcome_label}: ${s.hits_top10} of top 10 broke out (≈${fmt(s.expected_top10_by_chance)} expected by chance)`;
    b.innerHTML = `<span class="num">${s.pending ? "?" : s.hits_top10}</span>
      <span class="col"><span class="bar" style="height:${h}%"></span>
      ${s.pending ? "" : `<span class="chance" style="bottom:${chance}%"></span>`}</span>
      <span>${s.season_label.slice(2)}</span>`;
    b.addEventListener("click", () => { current = s.test_season; render(); });
    strip.appendChild(b);
  }
}

function renderBoard() {
  const s = seasons.find(x => x.test_season === current);
  const rows = (rowsBySeason[current] || []).filter(r => r.rank <= topN);
  document.getElementById("title").textContent = `End of ${s.season_label}: who breaks out in ${s.outcome_label}?`;
  const hits = rows.filter(r => r.status === "hit").length;
  document.getElementById("meta").textContent = s.pending
    ? `${s.pool} young players ranked · outcomes arrive at the end of ${s.outcome_label}`
    : `${hits} of these ${rows.length} broke out · ${s.pool} young players ranked · base rate ${fmt(100 * s.base_rate, 0)}%`;
  const maxP = Math.max(...rows.map(r => r.score), 0.01);
  document.getElementById("rows").innerHTML = rows.map(r => {
    const chip = r.status === "hit" ? `<span class="chip hit">Broke out · ${r.breakout_types}</span>`
      : r.status === "miss" ? `<span class="chip miss">No breakout</span>` : `<span class="chip pending">Pending</span>`;
    const after = r.status === "pending" ? "" : (r.ppg_next === null
      ? `<div class="after">Did not play in ${s.outcome_label}</div>`
      : `<div class="after">${s.outcome_label}: ${fmt(r.ppg_next)} ppg (${signed(r.ppg_next - r.ppg)}), ${fmt(r.mpg_next)} min${r.team_next && r.team_next !== r.team_abbreviation ? " · " + r.team_next : ""}</div>`);
    return `<div class="row">
      <div class="rank">${r.rank}</div>
      <div><div class="name">${r.player_name}</div>
        <div class="ctx">${r.team_abbreviation || ""} · age ${fmt(r.age)} · ${fmt(r.min_per_game)} min · ${fmt(r.ppg)} ppg</div></div>
      <div class="prob"><div class="track"><div class="fill" style="width:${(100 * r.score / maxP).toFixed(1)}%"></div></div>
        <span class="pct">${fmt(100 * r.score, 0)}%</span></div>
      <div class="result">${chip}${after}</div>
    </div>`;
  }).join("");
}

function render() { renderStrip(); renderBoard(); }
document.querySelectorAll(".toggle button").forEach(btn => btn.addEventListener("click", () => {
  topN = Number(btn.dataset.n);
  document.querySelectorAll(".toggle button").forEach(b => b.setAttribute("aria-pressed", String(b === btn)));
  renderBoard();
}));
render();
</script>
</body>
</html>
"""


def render_html(board, summary, path):
    path.write_text(HTML_TEMPLATE.replace("__DATA__", board_json(board, summary)), encoding="utf-8")
    return path
