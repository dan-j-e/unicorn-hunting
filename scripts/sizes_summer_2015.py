"""Sizes for 2015 summer-league players with no NBA listing (D58 steps 2-4).
Usage: python scripts/sizes_summer_2015.py <input csv from the NBA.com step> data/processed/sizes_summer_2015.csv
Basketball-Reference pages are cached in data/raw/bref/players, so a re-run makes no requests."""
import sys, re, time, glob, gzip, json, hashlib
from pathlib import Path
import pandas as pd, requests
H = {"User-Agent": "Mozilla/5.0 (personal research project; low request rate)"}
CACHE = Path("data/raw/bref/players"); CACHE.mkdir(parents=True, exist_ok=True)
def get(url):
    p = CACHE / (hashlib.md5(url.encode()).hexdigest() + ".html")
    if p.exists(): return p.read_text(encoding="utf-8"), None
    r = requests.get(url, headers=H, timeout=30); time.sleep(4)
    p.write_bytes(r.content); return r.content.decode("utf-8", "replace"), r.url
fr = []
for f in glob.glob("data/raw/DraftCombineStats/*"):
    r = json.load(gzip.open(f, "rt"))["response"]["resultSets"][0]; fr.append(pd.DataFrame(r["rowSet"], columns=r["headers"]))
comb = pd.concat(fr).dropna(subset=["HEIGHT_W_SHOES", "WEIGHT"]).drop_duplicates("PLAYER_ID", keep="last").set_index("PLAYER_ID")
m = pd.read_csv(sys.argv[1])
out = []
for _, row in m.iterrows():
    rec = dict(player_id=row.player_id, player_name=row.player_name, height_in=None, weight_lb=None, source=None, note="")
    if isinstance(row.source, str):
        h, i = row.height.split("-"); rec.update(height_in=int(h) * 12 + int(i), weight_lb=float(row.weight), source=row.source)
    elif row.player_id in comb.index:
        c = comb.loc[row.player_id]; rec.update(height_in=float(c.HEIGHT_W_SHOES), weight_lb=float(c.WEIGHT), source=f"NBA draft combine {c.SEASON} (height in shoes)")
    else:
        url = "https://www.basketball-reference.com/search/search.fcgi?search=" + requests.utils.quote(row.player_name)
        t, final = get(url)
        if final and "/international/players/" in final:
            cands = [(final.split(".com")[1], "")]
            yrs_ok = [cands[0]]
        else:
            cands = re.findall(r'<div class="search-item-name">.*?<a href="(/international/players/[^"]+)">([^<]+)</a>', t, re.S)
            def overlap(label):
                y = re.findall(r"\((\d{4})-(\d{4})\)|\((\d{4})\)", label)
                if not y: return False
                a, b, c1 = y[0]; lo, hi = (int(a), int(b)) if a else (int(c1), int(c1))
                return lo <= 2016 and hi >= 2014
            yrs_ok = [c for c in cands if overlap(c[1])]
        if len(yrs_ok) == 1:
            page, _ = get("https://www.basketball-reference.com" + yrs_ok[0][0])
            s = re.findall(r"<span>(\d)-(\d+)</span>,&nbsp;<span>(\d+)lb</span>", page)
            if s:
                f_, i_, w = s[0]; rec.update(height_in=int(f_) * 12 + int(i_), weight_lb=float(w), source="Basketball-Reference international page", note=yrs_ok[0][0])
            else: rec["note"] = "page has no size"
        else:
            rec["note"] = f"{len(yrs_ok)} matches with years overlapping 2014-16 ({len(cands)} international results)"
    out.append(rec); print(rec["player_name"], rec["source"], rec["note"], flush=True)
pd.DataFrame(out).to_csv(sys.argv[2], index=False)
print("DONE")
