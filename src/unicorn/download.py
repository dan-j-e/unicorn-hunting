"""Populate data/raw/ with every API response the project uses.

Safe to re-run: anything already cached is skipped, so an interrupted run
resumes where it stopped.  Run with:  python -m unicorn.download
"""

import pandas as pd
from nba_api.stats.endpoints import (
    commonteamroster,
    draftcombinestats,
    drafthistory,
    leaguedashplayerbiostats,
    leaguedashplayershotlocations,
    leaguedashplayerstats,
)
from nba_api.stats.static import teams

from unicorn.raw import cache_path, fetch

SEASONS = [f"{y}-{str(y + 1)[-2:]}" for y in range(2011, 2026)]  # 2011-12 … 2025-26
SEASON_TYPES = ["Regular Season", "Playoffs"]
MEASURES = ["Base", "Advanced", "Usage", "Scoring", "Defense", "Misc"]
# Combine seasons are labelled by draft year ("2018-19" = 2018 draft). 2000 is the
# first year available; 2026-27 is this year's class, needed for the live season.
COMBINE_SEASONS = [f"{y}-{str(y + 1)[-2:]}" for y in range(2000, 2027)]


def build_requests():
    """Every (endpoint, params) pair to download, as a flat list."""
    reqs = []
    for season in SEASONS:
        for season_type in SEASON_TYPES:
            for measure in MEASURES:
                reqs.append((leaguedashplayerstats.LeagueDashPlayerStats, dict(
                    season=season, season_type_all_star=season_type,
                    measure_type_detailed_defense=measure, per_mode_detailed="Totals")))
            # Restricting to games started: GP here = games started (verified against PlayerCareerStats GS)
            reqs.append((leaguedashplayerstats.LeagueDashPlayerStats, dict(
                season=season, season_type_all_star=season_type, measure_type_detailed_defense="Base",
                per_mode_detailed="Totals", starter_bench_nullable="Starters")))
            reqs.append((leaguedashplayershotlocations.LeagueDashPlayerShotLocations, dict(
                season=season, season_type_all_star=season_type,
                distance_range="By Zone", per_mode_detailed="Totals")))
        reqs.append((leaguedashplayerbiostats.LeagueDashPlayerBioStats, dict(
            season=season, per_mode_simple="Totals")))
        for team in teams.get_teams():  # team IDs are stable across relocations/renames
            reqs.append((commonteamroster.CommonTeamRoster, dict(team_id=team["id"], season=season)))
    for season in COMBINE_SEASONS:
        reqs.append((draftcombinestats.DraftCombineStats, dict(season_all_time=season)))
    reqs.append((drafthistory.DraftHistory, {}))
    return reqs


def download_all():
    reqs = build_requests()
    log = []
    for i, (endpoint, params) in enumerate(reqs, 1):
        cached = cache_path(endpoint, params).exists()
        try:
            frames = fetch(endpoint, **params)
            rows = sum(len(df) for df in frames.values())
            status = "cached" if cached else "downloaded"
        except Exception as err:
            rows, status = None, f"FAILED: {type(err).__name__}: {err}"
        log.append({"endpoint": endpoint.__name__, **params, "rows": rows, "status": status})
        if status != "cached":
            print(f"[{i}/{len(reqs)}] {endpoint.__name__} {params} -> {status} ({rows} rows)", flush=True)
    return pd.DataFrame(log)


if __name__ == "__main__":
    log = download_all()
    print(log["status"].str.split(":").str[0].value_counts().to_string())
