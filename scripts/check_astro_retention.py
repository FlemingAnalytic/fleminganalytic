#!/usr/bin/env python3
"""Assert the astrology app keeps nothing, against the running service.

    scripts/check_astro_retention.py [--base https://api.fleminganalytic.com]

The privacy policy claims charts are deleted as they are delivered. That claim
was previously false for eight months and nobody noticed, because nothing
observable changed when it broke: charts were served correctly, the app worked,
and the only symptom was a directory quietly growing to 244 MB of other
people's birth data behind a policy that said it did not exist.

An unobservable property has to be checked deliberately or not at all. This
generates a real chart and then proves, from outside, that:

  1. the artefact is delivered once and is gone on the second request
  2. nothing lands in any web-served directory
  3. an artefact nobody collects does not survive

It talks to the live service rather than importing the code, because the
failure was never in the logic - it was in where the files went and who served
them, which only the deployed system can answer.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSIENT = os.path.join(ROOT, "db", "astro_transient")
# Directories nginx serves straight off disk. A chart must never be in one.
WEB_SERVED = [os.path.join(ROOT, "static", "images"), os.path.join(ROOT, "static", "pdf")]

CHART = {"name": "Retention Check", "year": 1974, "month": 1, "day": 15,
         "hour": 7, "minute": 30, "city": "Chicago", "country": "US"}


def post(url: str, payload: dict, timeout: int = 180) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def status_of(url: str, timeout: int = 60):
    """Return (status, body, headers) with case-insensitive header lookup.

    Headers are lower-cased on the wire under HTTP/2. dict(r.headers) throws
    away urllib's case-insensitive Message and leaves a plain dict, so
    .get("Cache-Control") missed a header that was present - this check
    reported a failure the server did not have.
    """
    def flatten(h):
        return {k.lower(): v for k, v in (h or {}).items()}
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read(), flatten(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, b"", flatten(e.headers)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://api.fleminganalytic.com")
    args = ap.parse_args()
    fails = 0

    print("\n  generating a chart...")
    data = post(f"{args.base}/astro/generate-chart", CHART)
    urls = [("chart", data["chart_url"])]
    if (data.get("wordcloud") or {}).get("file_url"):
        urls.append(("wordcloud", data["wordcloud"]["file_url"]))

    for label, url in urls:
        # 1. delivered once
        code, body, headers = status_of(url)
        ok_first = code == 200 and len(body) > 1000
        code2, _, _ = status_of(url)
        ok_second = code2 == 404
        cache = headers.get("cache-control", "").lower()
        ok_cache = "no-store" in cache

        for name, ok, detail in [
            (f"{label}: delivered", ok_first, f"HTTP {code}, {len(body)} bytes"),
            (f"{label}: gone after delivery", ok_second, f"second request HTTP {code2}"),
            (f"{label}: not cacheable", ok_cache, f"Cache-Control: {cache or 'absent'}"),
        ]:
            print(f"  {'OK  ' if ok else 'FAIL'} {name:<34} {detail}")
            if not ok:
                fails += 1

    # 2. nothing in a web-served directory
    for d in WEB_SERVED:
        stray = [f for f in os.listdir(d)] if os.path.isdir(d) else []
        ok = not stray
        print(f"  {'OK  ' if ok else 'FAIL'} {'nothing in ' + os.path.relpath(d, ROOT):<34} "
              f"{len(stray)} file(s)")
        if not ok:
            fails += 1
            for f in stray[:5]:
                print(f"       stray: {f}")

    # 3. an uncollected artefact does not survive
    data2 = post(f"{args.base}/astro/generate-chart", CHART)   # deliberately not fetched
    before = len(os.listdir(TRANSIENT)) if os.path.isdir(TRANSIENT) else 0
    for f in os.listdir(TRANSIENT):
        p = os.path.join(TRANSIENT, f)
        os.utime(p, (time.time() - 7200, time.time() - 7200))  # age past the threshold
    post(f"{args.base}/astro/generate-chart", CHART)           # any generation sweeps
    after = [f for f in os.listdir(TRANSIENT)] if os.path.isdir(TRANSIENT) else []
    # the two just created by the sweeping call are expected to remain
    ok = len(after) <= 2
    print(f"  {'OK  ' if ok else 'FAIL'} {'uncollected charts are swept':<34} "
          f"{before} aged -> {len(after)} left")
    if not ok:
        fails += 1

    print(f"\n  {'ASTRO RETAINS NOTHING' if not fails else f'{fails} RETENTION CHECK(S) FAILED'}\n")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
