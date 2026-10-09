"""Most Improved Player voting results from Basketball-Reference (for evaluation/display only).

Pages are fetched politely (one at a time, with a pause) and cached raw under
data/raw/bref/, so each season is downloaded once.
"""

import time
import unicodedata

import pandas as pd
import requests
from bs4 import BeautifulSoup

from unicorn.raw import RAW_DIR

BREF_DIR = RAW_DIR / "bref"
URL = "https://www.basketball-reference.com/awards/awards_{year}.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (personal research project; low request rate)"}
PAUSE_SECONDS = 4.0


def _page(year):
    path = BREF_DIR / f"awards_{year}.html"
    if not path.exists():
        r = requests.get(URL.format(year=year), headers=HEADERS, timeout=30)
        r.raise_for_status()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)   # raw bytes; the page is UTF-8 (requests' guessed encoding garbles accents)
        time.sleep(PAUSE_SECONDS)
    return path.read_text(encoding="utf-8")


def normalize_name(name):
    """Lower-case ASCII name without punctuation or suffixes, for matching NBA.com and B-Ref spellings."""
    s = unicodedata.normalize("NFKD", name.replace("ı", "i")).encode("ascii", "ignore").decode().lower()  # Turkish dotless i
    s = "".join(ch for ch in s if ch.isalnum() or ch == " ")
    return " ".join(w for w in s.split() if w not in {"jr", "sr", "ii", "iii", "iv"})


def mip_voting(year):
    """Voting table for the season ending in `year` (e.g. 2026 = 2025-26)."""
    html = _page(year).replace("<!--", "").replace("-->", "")   # some tables sit inside HTML comments
    table = BeautifulSoup(html, "html.parser").find("table", id="mip")
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cell = {td.get("data-stat"): td.get_text(strip=True) for td in tr.find_all(["th", "td"])}
        if not cell.get("player"):
            continue
        rows.append({"season": f"{year - 1}-{str(year)[-2:]}", "vote_rank": cell.get("rank"), "player": cell["player"],
                     "team": cell.get("team_id"), "first_place_votes": cell.get("votes_first"),
                     "points": cell.get("points_won"), "share": cell.get("award_share")})
    df = pd.DataFrame(rows)
    df["points"] = pd.to_numeric(df["points"], errors="coerce")
    df["share"] = pd.to_numeric(df["share"], errors="coerce")
    df = df.sort_values("points", ascending=False).reset_index(drop=True)
    df["vote_rank"] = df["points"].rank(ascending=False, method="min").astype(int)
    df["name_key"] = df["player"].map(normalize_name)
    return df


def all_mip_voting(first_year=2012, last_year=2026):
    return pd.concat([mip_voting(y) for y in range(first_year, last_year + 1)], ignore_index=True)


def attach_player_ids(votes, games):
    """Add NBA.com player_id to B-Ref voting rows by matching normalized names within the season."""
    names = games.groupby(["season", "player_id"])["player_name"].last().reset_index()
    names["name_key"] = names["player_name"].map(normalize_name)
    return votes.merge(names[["season", "name_key", "player_id"]], on=["season", "name_key"], how="left")
