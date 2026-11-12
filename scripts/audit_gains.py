"""Audit 2 (12 November 2026): are the recent Most Improved model changes real or noise?

For each model version, every season's strict-test score (log of the winner's chance × the number of candidates) is computed;
versions are compared season by season, and the seasons are resampled 5,000 times. See docs/AUDIT.md.
Run from the project folder:  .venv/bin/python scripts/audit_gains.py   (about 5 minutes)
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from unicorn import mip_history as MH
from unicorn.allstars import load_selections
from unicorn.mip import AGE, GAMELOG_DEFENSE, GAMELOG_DELTAS, RELATIVE, SECOND_YEAR, TEAM
from unicorn.mip_eval import LIVE_INPUTS, LIVE_INPUTS_D41, LIVE_TURN, POINTS_INPUTS, current_frame, winner_ranks

g = MH.load_games(); info = MH.player_info(); votes, winners = MH.voting(g); sel = load_selections()
DX = GAMELOG_DELTAS + GAMELOG_DEFENSE
V3 = DX + RELATIVE + TEAM + AGE + SECOND_YEAR
rng = np.random.default_rng(0)
out = []
for point, day in {"day 19": 19, "day 85": 85, "end of season": None}.items():
    f_pts = current_frame(g, info, winners, sel, day=day, level_col="base_ppg", turn=20)
    f_gs = current_frame(g, info, winners, sel, day=day)          # game score turning point at 14, established inputs
    models = {
        "stage 3 (voters: relative, team, age, 2nd year)": (f_pts, V3),
        "10 Nov (D39: points turning point, All-Star, lost season)": (f_pts, POINTS_INPUTS),
        "D41 (game-score turning point)": (f_gs, LIVE_INPUTS_D41),
        "D42 (+ already clearly a star)": (f_gs, LIVE_INPUTS),
    }
    logs = {}
    for name, (f, feats) in models.items():
        r = winner_ranks(f, feats, scheme="strict")
        logs[name] = np.log(r["p"].astype(float) * r["n"].astype(float))
    L = pd.DataFrame(logs)
    names = list(models)
    for a, b in [(names[1], names[2]), (names[2], names[3]), (names[1], names[3]), (names[0], names[3])]:
        d = (L[b] - L[a]).to_numpy()
        boots = np.array([rng.choice(d, len(d)).mean() for _ in range(5000)])
        out.append({"point": point, "from": a.split(" (")[0], "to": b.split(" (")[0],
                    "× blind (from → to)": f"{np.exp(L[a].mean()):.1f} → {np.exp(L[b].mean()):.1f}",
                    "seasons better / worse": f"{(d > 1e-9).sum()} / {(d < -1e-9).sum()}",
                    "share of resamples where 'to' is better": f"{(boots > 0).mean():.0%}",
                    "90% range of the change": f"×{np.exp(np.quantile(boots, 0.05)):.2f} to ×{np.exp(np.quantile(boots, 0.95)):.2f}"})
print(pd.DataFrame(out).to_string(index=False))
