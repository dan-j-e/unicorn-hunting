#!/usr/bin/env bash
# Re-run the live 2026-27 Most Improved race (notebook 12) and print today's leaderboard.
# Usage, from the project folder:   ./scripts/update_mip_race.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Downloading the newest games and re-running notebook 12 (takes about 3-5 minutes)..."
.venv/bin/jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=3600 notebooks/12_mip_live_race.ipynb 2>&1 | grep -v -i "warning" || true

.venv/bin/python - <<'PY'
import pandas as pd
d = pd.read_parquet("data/processed/mip_race_daily_2026_27.parquet")
last = d["day"].max()
today = d[d["day"] == last].nsmallest(7, "rank")
prev = d[d["day"] == last - 1].set_index("player_id")["rank"]
k = today["turning_point"].iloc[0]
print(f"\nMost Improved race after day {last} ({today['date'].iloc[0]:%d %b %Y}); scoring turning point: {'none' if pd.isna(k) else int(k)}\n")
for _, r in today.iterrows():
    was = prev.get(r["player_id"])
    move = "new" if pd.isna(was) else f"{int(was) - int(r['rank']):+d}"
    print(f"  {int(r['rank'])}. {r['player_name']:<24} {r['chance']:6.1%}   {r['ppg']:4.1f} pts ({r['base_ppg']:4.1f} last season)   vs yesterday: {move}")
print("\nCharts updated in outputs/figures/ (12_daily_worm.png, 12_race_today.png, ...).")
print("The README's 'Live' and 'Last updated' lines are not changed automatically.")
PY
