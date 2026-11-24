#!/usr/bin/env python3
"""Make the US car dealership directory answerable in the analyst.

The source is a directory: 19,169 franchised dealers with a name, address,
phone, site and coordinates, and nothing numeric to average. Opened as-is the
analyst had no measure, so its starter report fell back to "count of name by
name" - a column of 1s (2026-11-23). A directory's questions are counts: how
many dealers, of which brand, where. This adds what those need:

  brand         - the first make named in the dealer's name ("Alpine Buick Gmc"
                  -> Buick); "Independent / other" when no make appears.
                  Brands under 1% of dealers are pooled into "Other brands".
  automaker     - the brand's parent company (Stellantis, General Motors, ...),
                  the honest grouping for multi-franchise signs.
  region        - Census region of the state (Northeast, Midwest, South, West;
                  DC with the South, PR/Guam/USVI as "Territories").
  state_group   - the state, with states under 1% of dealers pooled into
                  "Other states" so the chart stays readable.
  dealer_count  - 1 per row; its sum is the number of dealers.

and writes us_car_dealerships.questions.json, which the analyst uses as the
dataset's starter report. Run in place:

    python3 scripts/build_dealerships.py /var/www/fleminganalytic/db/analyst
"""

import csv
import json
import re
import sys
from pathlib import Path

import pandas as pd

BRANDS = [  # longest first, so "Land Rover" wins over "Rover", "Mercedes-Benz" over "Benz"
    ("alfa romeo", "Alfa Romeo"), ("land rover", "Land Rover"), ("mercedes-benz", "Mercedes-Benz"),
    ("mercedes", "Mercedes-Benz"), ("rolls-royce", "Rolls-Royce"), ("aston martin", "Aston Martin"),
    ("volkswagen", "Volkswagen"), ("vw", "Volkswagen"), ("chevrolet", "Chevrolet"), ("chevy", "Chevrolet"),
    ("acura", "Acura"), ("audi", "Audi"), ("bmw", "BMW"), ("buick", "Buick"), ("cadillac", "Cadillac"),
    ("chrysler", "Chrysler"), ("dodge", "Dodge"), ("fiat", "Fiat"), ("ford", "Ford"), ("genesis", "Genesis"),
    ("gmc", "GMC"), ("honda", "Honda"), ("hyundai", "Hyundai"), ("infiniti", "Infiniti"), ("jaguar", "Jaguar"),
    ("jeep", "Jeep"), ("kia", "Kia"), ("lexus", "Lexus"), ("lincoln", "Lincoln"), ("maserati", "Maserati"),
    ("mazda", "Mazda"), ("mini", "MINI"), ("mitsubishi", "Mitsubishi"), ("nissan", "Nissan"),
    ("porsche", "Porsche"), ("ram", "Ram"), ("subaru", "Subaru"), ("tesla", "Tesla"), ("toyota", "Toyota"),
    ("volvo", "Volvo"), ("ferrari", "Ferrari"), ("lamborghini", "Lamborghini"), ("bentley", "Bentley"),
    ("scion", "Scion"),
]

# Parent company. Dealer names list every franchise on the sign ("Chrysler
# Dodge Jeep Ram", "Buick GMC", "Ford Lincoln"), so the first make named says
# little on its own - but the makes on one sign almost always share a parent,
# which makes the automaker the honest grouping.
MAKER = {
    "Chrysler": "Stellantis", "Dodge": "Stellantis", "Jeep": "Stellantis", "Ram": "Stellantis",
    "Fiat": "Stellantis", "Alfa Romeo": "Stellantis", "Maserati": "Stellantis",
    "Chevrolet": "General Motors", "Buick": "General Motors", "GMC": "General Motors", "Cadillac": "General Motors",
    "Ford": "Ford", "Lincoln": "Ford",
    "Toyota": "Toyota", "Lexus": "Toyota", "Scion": "Toyota",
    "Honda": "Honda", "Acura": "Honda", "Nissan": "Nissan", "Infiniti": "Nissan",
    "Hyundai": "Hyundai / Kia", "Genesis": "Hyundai / Kia", "Kia": "Hyundai / Kia",
    "Volkswagen": "Volkswagen Group", "Audi": "Volkswagen Group", "Porsche": "Volkswagen Group",
    "Bentley": "Volkswagen Group", "Lamborghini": "Volkswagen Group",
    "BMW": "BMW", "MINI": "BMW", "Rolls-Royce": "BMW", "Mercedes-Benz": "Mercedes-Benz",
    "Jaguar": "Jaguar Land Rover", "Land Rover": "Jaguar Land Rover",
}
PATTERN = re.compile(r"\b(" + "|".join(re.escape(k) for k, _ in BRANDS) + r")\b", re.I)
LOOKUP = dict(BRANDS)

REGION = {  # U.S. Census Bureau regions
    **dict.fromkeys("CT ME MA NH RI VT NJ NY PA".split(), "Northeast"),
    **dict.fromkeys("IL IN MI OH WI IA KS MN MO NE ND SD".split(), "Midwest"),
    **dict.fromkeys("DE FL GA MD NC SC VA DC WV AL KY MS TN AR LA OK TX".split(), "South"),
    **dict.fromkeys("AZ CO ID MT NV NM UT WY AK CA HI OR WA".split(), "West"),
    **dict.fromkeys(["PR", "GU", "Guam", "VI"], "Territories"),
}


def brand_of(name):
    m = PATTERN.search(str(name or ""))
    return LOOKUP[m.group(1).lower()] if m else "Independent / other"


def pool(s, min_share, other):
    share = s.value_counts(normalize=True)
    return s.where(s.isin(share[share >= min_share].index), other)


def q(question, row):
    return {"type": "breakdown", "question": question,
            "action": {"type": "pivot", "rows": [row], "values": ["dealer_count"], "agg": "sum"}}


def main(folder):
    folder = Path(folder)
    src = folder / "us_car_dealerships.csv"
    df = pd.read_csv(src, dtype=str, keep_default_na=False, na_values=[""])
    for c in ("brand", "automaker", "region", "state_group", "dealer_count"):
        df = df.drop(columns=c, errors="ignore")   # re-runnable
    df["geo.latitude"] = pd.to_numeric(df["geo.latitude"], errors="coerce")
    df["geo.longitude"] = pd.to_numeric(df["geo.longitude"], errors="coerce")
    first = df["name"].map(brand_of)
    df["brand"] = pool(first, 0.01, "Other brands")
    df["automaker"] = pool(first.map(MAKER).fillna(first.where(first == "Independent / other", first)),
                           0.01, "Other automakers")
    st = df["address.addressRegion"].str.strip()
    df["region"] = st.map(REGION).fillna("Unknown")
    df["state_group"] = pool(st, 0.01, "Other states")
    df["dealer_count"] = 1
    df.to_csv(src, index=False, quoting=csv.QUOTE_NONNUMERIC)

    questions = [
        q("Which automakers have the most dealerships? (number of dealers, by parent company)", "automaker"),
        q("Where are the dealerships? (number of dealers by Census region)", "region"),
        q("Which states have the most dealerships? (number of dealers)", "state_group"),
    ]
    (folder / "us_car_dealerships.questions.json").write_text(json.dumps(questions, indent=2))
    print(f"wrote {src} ({len(df):,} dealers); brands: {df['brand'].nunique()}, "
          f"automakers: {df['automaker'].nunique()}, states shown: {df['state_group'].nunique()}, unmatched brand: "
          f"{(df['name'].map(brand_of) == 'Independent / other').mean():.1%}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/var/www/fleminganalytic/db/analyst")
