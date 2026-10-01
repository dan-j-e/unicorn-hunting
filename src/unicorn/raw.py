"""Cached access to stats.nba.com via nba_api.

Every response is stored untouched as gzipped JSON under data/raw/<Endpoint>/,
so each (endpoint, parameters) pair is downloaded at most once. DataFrames are
always rebuilt from the cached JSON, never from a live object.
"""

import gzip
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import nba_api
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

SLEEP_SECONDS = 1.0  # pause after every live request; stats.nba.com rate-limits
MAX_RETRIES = 3


def cache_path(endpoint, params):
    """data/raw/<Endpoint>/<k1=v1__k2=v2>.json.gz, keys sorted so order doesn't matter."""
    key = "__".join(f"{k}={v}" for k, v in sorted(params.items())) or "all"
    key = key.replace(" ", "_").replace("/", "-")
    return RAW_DIR / endpoint.__name__ / f"{key}.json.gz"


def _download(endpoint, params, timeout):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = endpoint(**params, timeout=timeout).get_dict()
            time.sleep(SLEEP_SECONDS)
            return response
        except Exception as err:  # nba_api surfaces timeouts/HTTP errors as assorted types
            if attempt == MAX_RETRIES:
                raise
            wait = SLEEP_SECONDS * 5 * attempt
            print(f"{endpoint.__name__} {params} failed ({type(err).__name__}); retry in {wait:.0f}s")
            time.sleep(wait)


def fetch_raw(endpoint, timeout=60, refresh=False, **params):
    """Return the raw JSON response, downloading only on a cache miss (or refresh=True)."""
    path = cache_path(endpoint, params)
    if path.exists() and not refresh:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)["response"]

    response = _download(endpoint, params, timeout)
    record = {
        "endpoint": endpoint.__name__,
        "params": params,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "nba_api_version": nba_api.__version__,
        "response": response,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(record, f)
    tmp.replace(path)  # atomic: an interrupted download never leaves a half-written cache file
    return response


def fetch(endpoint, timeout=60, refresh=False, **params):
    """Return {result_set_name: DataFrame} for an nba_api endpoint, using the raw cache."""
    response = fetch_raw(endpoint, timeout=timeout, refresh=refresh, **params)
    return {
        rs["name"]: pd.DataFrame(rs["rowSet"], columns=rs["headers"])
        for rs in response["resultSets"]
    }
