"""Prior All-Star selections, for the 'already established' Most Improved input (notebook 17, D38).

Two steps, so that father/son and same-name pairs (Tim Hardaway / Tim Hardaway Jr., Gary Payton / Gary Payton II)
are never confused:
  1. Basketball-Reference All-Star pages (1980 onward) give a broad list of names worth checking.
  2. NBA.com's PlayerAwards, looked up by NBA.com player_id, is the record that counts.

Only selections from BEFORE a season count for that season: many Most Improved winners are first picked
in the season they win, so that season's selection would leak the answer.
"""

import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from nba_api.stats.endpoints import playerawards

from unicorn.bref import BREF_DIR, HEADERS, PAUSE_SECONDS, normalize_name
from unicorn.raw import PROJECT_ROOT, fetch

URL = "https://www.basketball-reference.com/allstar/NBA_{year}.html"
FIRST_YEAR = 1980                     # covers the careers of everyone in the 2000-01 pool
NO_GAME = {1999}                      # lockout: no All-Star game in 1998-99


def _page(year):
    path = BREF_DIR / f"allstar_{year}.html"
    if not path.exists():
        r = requests.get(URL.format(year=year), headers=HEADERS, timeout=30)
        r.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)
        time.sleep(PAUSE_SECONDS)
    return path.read_text(encoding="utf-8")


def bref_allstar_names(first=FIRST_YEAR, last=2026):
    """Normalised names of every player linked on any All-Star page. Deliberately broad: step 2 does the checking."""
    names = set()
    for year in range(first, last + 1):
        if year in NO_GAME:
            continue
        html = _page(year).replace("<!--", "").replace("-->", "")
        for a in BeautifulSoup(html, "html.parser").select('a[href^="/players/"]'):
            names.add(normalize_name(a.get_text(strip=True)))
    return names


def allstar_selections(players):
    """NBA.com All-Star selections for the given players (DataFrame with player_id, player_name).
    Only players whose name appears on a Basketball-Reference All-Star page are looked up."""
    names = bref_allstar_names()
    check = players[players["player_name"].map(normalize_name).isin(names)].drop_duplicates("player_id")
    rows = []
    for pid in check["player_id"]:
        a = next(iter(fetch(playerawards.PlayerAwards, player_id=int(pid)).values()))
        a.columns = a.columns.str.upper()
        a = a[a["DESCRIPTION"].eq("NBA All-Star") & a["SEASON"].notna()]
        rows += [{"player_id": int(pid), "season": str(s)} for s in a["SEASON"].unique()]
    return pd.DataFrame(rows, columns=["player_id", "season"]), len(check)


def add_prior_allstar(frame, selections, season_col="season"):
    """Add prior_allstar (1 if picked in any season before this one) and prior_allstar_n (how many times)."""
    sel = selections.groupby("player_id")["season"].apply(sorted).to_dict()
    n = [sum(s < season for s in sel.get(int(p), [])) for p, season in zip(frame["player_id"], frame[season_col])]
    return frame.assign(prior_allstar_n=n, prior_allstar=[float(k > 0) for k in n])


SELECTIONS_PATH = PROJECT_ROOT / "data" / "processed" / "allstar_selections.parquet"


def load_selections():
    """All-Star selections for everyone who played since 1999-00 (built once, then read from data/processed)."""
    if SELECTIONS_PATH.exists():
        return pd.read_parquet(SELECTIONS_PATH)
    from unicorn.mip_history import load_games          # 1999-00 onward, so 2000s careers are covered
    players = load_games()[["player_id", "player_name"]].drop_duplicates("player_id")
    sel, _ = allstar_selections(players)
    sel.to_parquet(SELECTIONS_PATH, index=False)
    return sel
