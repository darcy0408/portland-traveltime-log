"""Log live arterial travel times for the fixed OD pairs in pairs.json.

Runs hourly via GitHub Actions (see .github/workflows/log.yml). Each run
appends one CSV row per pair to data/traveltimes_YYYY-MM.csv. Stdlib only,
so the Actions runner needs no installs.

Why this exists: PORTAL archives freeway loop detectors, but nobody archives
SURFACE-street travel times; Google and TomTom show them live and throw them
away. The Sept 11 2026 I-5 SB closure will push traffic onto surface streets,
and the model's registered predictions about that redistribution can only be
graded if a before-baseline exists. This logger IS that baseline, and its
commit history is the provable timestamp.

Data discipline: this data grades registered predictions. It is never used to
tune the model. The pairs were frozen before logging began.
"""
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://api.tomtom.com/routing/1/calculateRoute"
HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ["utc", "pair", "travel_s", "no_traffic_s", "historic_s",
          "delay_s", "length_m", "status"]


def query(key, frm, to):
    """One routing call. Returns the summary dict, raising on HTTP errors."""
    locs = f"{frm[0]},{frm[1]}:{to[0]},{to[1]}"
    params = urllib.parse.urlencode({
        "key": key, "traffic": "true", "travelMode": "car",
        "routeType": "fastest", "computeTravelTimeFor": "all"})
    url = f"{API}/{locs}/json?{params}"
    with urllib.request.urlopen(url, timeout=60) as r:
        body = json.load(r)
    return body["routes"][0]["summary"]


def main():
    key = os.environ.get("TOMTOM_API_KEY")
    if not key:
        sys.exit("TOMTOM_API_KEY is not set; add it as a repository secret.")

    with open(os.path.join(HERE, "pairs.json")) as f:
        pairs = json.load(f)["pairs"]

    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    out = os.path.join(HERE, "data", f"traveltimes_{now.strftime('%Y-%m')}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    new_file = not os.path.exists(out)

    rows, failures = [], 0
    for p in pairs:
        row = {"utc": stamp, "pair": p["id"]}
        try:
            s = query(key, p["from"], p["to"])
            row.update({
                "travel_s": s.get("travelTimeInSeconds"),
                "no_traffic_s": s.get("noTrafficTravelTimeInSeconds"),
                "historic_s": s.get("historicTrafficTravelTimeInSeconds"),
                "delay_s": s.get("trafficDelayInSeconds"),
                "length_m": s.get("lengthInMeters"),
                "status": "ok"})
        except Exception as e:                       # log the failure as a row
            failures += 1
            row.update({"travel_s": "", "no_traffic_s": "", "historic_s": "",
                        "delay_s": "", "length_m": "",
                        "status": f"error:{type(e).__name__}"})
        rows.append(row)
        time.sleep(1)                                # stay far under rate limits

    with open(out, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerows(rows)

    print(f"{stamp}: {len(rows) - failures} ok, {failures} failed -> {out}")
    # Fail the workflow only if EVERY call failed (bad key, API outage), so a
    # single flaky pair never blocks the commit of the others.
    if failures == len(rows):
        sys.exit("every call failed")


if __name__ == "__main__":
    main()
