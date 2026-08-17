#!/usr/bin/env python3
"""Assert that every clause of the policy source reaches the published page.

This exists because the generator lost one. `build_privacy.py` stripped the
masthead date by searching the whole document for "last updated", and the
"Changes to This Privacy Policy" clause quotes that phrase - so the clause
vanished from the published page while the page went on looking complete and
well-formed. Nothing about the output said a section was missing.

A privacy policy is the one document where quietly dropping a paragraph is
unacceptable, so the property is checked directly: take every sentence of the
markdown, normalise away the formatting, and require it to appear in the
rendered text.
"""
from __future__ import annotations

import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "apps", "astro", "static", "privacy.md")
OUTPUT = os.path.join(ROOT, "client-prod", "privacy.html")


def normalise(s: str) -> str:
    """Reduce to comparable prose: drop markdown, tags, entities and spacing.

    Punctuation is kept - dropping it once turned "industry-standard" into
    "industrystandard" and reported eight clauses missing that were present,
    which is the other way this check can fail: an alarm nobody believes.
    """
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = re.sub(r"\*\*|^#+\s*|^\s*-\s+", " ", s, flags=re.MULTILINE)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def main() -> int:
    md = open(SOURCE, encoding="utf-8").read()
    md = md.replace("Fleming Analytic Resources. Inc", "Fleming Analytic Resources, Inc.")
    if not os.path.exists(OUTPUT):
        print(f"FAIL {OUTPUT} does not exist")
        return 1
    page = open(OUTPUT, encoding="utf-8").read()
    body = page.split("<main", 1)[1] if "<main" in page else page
    rendered = normalise(body)

    checked, missing = 0, []
    for line in md.split("\n"):
        clause = normalise(line)
        # Skip headings-only fragments and short lines; they carry no clause.
        if len(clause) < 15:
            continue
        checked += 1
        if clause not in rendered:
            missing.append(line.strip())

    print(f"  clauses checked: {checked}")
    if missing:
        print(f"  FAIL {len(missing)} clause(s) of the policy are missing from /privacy:")
        for m in missing:
            print(f"    - {m[:96]}")
        return 1
    print("  ok   every clause of the source policy appears on the published page")
    return 0


if __name__ == "__main__":
    sys.exit(main())
