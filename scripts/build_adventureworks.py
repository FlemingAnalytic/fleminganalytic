#!/usr/bin/env python3
"""Build a flat AdventureWorks internet-sales table for the analyst.

AdventureWorks is a star schema across a dozen tables, and the analyst
loads one dataframe. That is not a mismatch to work around - flattening the
fact table against its dimensions is exactly what a Power BI model does
before anyone asks a question of it, so the result is the shape people
already have in mind when they say "AdventureWorks demo".

Column names come from the CREATE TABLE statements in Microsoft's own
install script rather than from memory: the CSVs are pipe-delimited BULK
INSERT files with no header row, so getting the order wrong would silently
mislabel every column.
"""

import re
import sys
from pathlib import Path

import pandas as pd

RAW = "https://raw.githubusercontent.com/microsoft/sql-server-samples/master/samples/databases/adventure-works/data-warehouse-install-script"
WORK = Path("/tmp/claude-0/aw")
SQL = Path("/tmp/claude-0/instawdbdw.sql")


def schema(table: str) -> list[str]:
    """Column names for a table, read out of the install script."""
    text = SQL.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf"CREATE TABLE\s+\[?dbo\]?\.\[?{table}\]?\s*\((.*?)\n\)\s*ON",
                  text, re.S | re.I)
    if not m:
        m = re.search(rf"CREATE TABLE\s+\[?dbo\]?\.\[?{table}\]?\s*\((.*?)\n\)",
                      text, re.S | re.I)
    if not m:
        raise SystemExit(f"no CREATE TABLE found for {table}")

    cols = []
    for line in m.group(1).splitlines():
        line = line.strip()
        # Column lines start with a bracketed name; constraints and keys do not.
        cm = re.match(r"\[([^\]]+)\]\s+\[?[A-Za-z]", line)
        if cm and not line.upper().startswith(("CONSTRAINT", "PRIMARY", "FOREIGN")):
            cols.append(cm.group(1))
    return cols


def load(table: str, usecols=None) -> pd.DataFrame:
    cols = schema(table)
    path = WORK / f"{table}.csv"
    df = pd.read_csv(path, sep="|", header=None, names=cols, encoding="utf-16le"
                     if path.read_bytes()[:2] == b"\xff\xfe" else "latin-1",
                     low_memory=False, on_bad_lines="warn")
    print(f"  {table:<24} {len(df):>7,} rows x {len(df.columns):>3} cols")
    return df[usecols] if usecols else df


def main() -> int:
    facts = load("FactInternetSales")
    product = load("DimProduct")
    subcat = load("DimProductSubcategory")
    cat = load("DimProductCategory")
    customer = load("DimCustomer")
    geo = load("DimGeography")
    date = load("DimDate")
    territory = load("DimSalesTerritory")

    # Product -> subcategory -> category
    product = product.merge(
        subcat[["ProductSubcategoryKey", "EnglishProductSubcategoryName", "ProductCategoryKey"]],
        on="ProductSubcategoryKey", how="left")
    product = product.merge(
        cat[["ProductCategoryKey", "EnglishProductCategoryName"]],
        on="ProductCategoryKey", how="left")

    # Customer -> geography
    customer = customer.merge(
        geo[["GeographyKey", "City", "StateProvinceName", "EnglishCountryRegionName"]],
        on="GeographyKey", how="left")

    # Deliberately not taking StandardCost or ListPrice from DimProduct: the
    # fact table carries ProductStandardCost and UnitPrice as they were at the
    # time of the sale, while the dimension holds today's values. Merging both
    # also collides on the name, and pandas would quietly suffix one away.
    df = facts.merge(
        product[["ProductKey", "EnglishProductName", "EnglishProductSubcategoryName",
                 "EnglishProductCategoryName", "Color", "Size"]]
        .rename(columns={"EnglishProductName": "Product",
                         "EnglishProductSubcategoryName": "Subcategory",
                         "EnglishProductCategoryName": "Category"}),
        on="ProductKey", how="left")

    df = df.merge(
        customer[["CustomerKey", "Gender", "YearlyIncome", "TotalChildren",
                  "EnglishEducation", "EnglishOccupation", "HouseOwnerFlag",
                  "NumberCarsOwned", "CommuteDistance", "City", "StateProvinceName",
                  "EnglishCountryRegionName", "BirthDate", "MaritalStatus"]]
        .rename(columns={"EnglishEducation": "Education",
                         "EnglishOccupation": "Occupation",
                         "EnglishCountryRegionName": "Country",
                         "StateProvinceName": "StateProvince"}),
        on="CustomerKey", how="left")

    df = df.merge(
        territory[["SalesTerritoryKey", "SalesTerritoryRegion", "SalesTerritoryGroup"]],
        on="SalesTerritoryKey", how="left")

    # Only the calendar attributes; the fact's own OrderDate is the date.
    df = df.merge(
        date[["DateKey", "EnglishMonthName", "MonthNumberOfYear",
              "CalendarYear", "CalendarQuarter", "EnglishDayNameOfWeek"]]
        .rename(columns={"DateKey": "OrderDateKey",
                         "EnglishMonthName": "OrderMonth",
                         "MonthNumberOfYear": "OrderMonthNumber",
                         "CalendarYear": "OrderYear",
                         "CalendarQuarter": "OrderQuarter",
                         "EnglishDayNameOfWeek": "OrderDayOfWeek"}),
        on="OrderDateKey", how="left")

    # Date only: the time component is midnight on every row, and carrying it
    # would make the column read as a timestamp in the profiler.
    df["OrderDate"] = pd.to_datetime(df["OrderDate"], errors="coerce").dt.date

    # Two measures every demo of this data reaches for and the schema does
    # not carry: what was made on the sale, and at what rate.
    df["Profit"] = df["SalesAmount"] - df["TotalProductCost"]
    df["ProfitMargin"] = (df["Profit"] / df["SalesAmount"].replace(0, pd.NA)) * 100

    # Column order is not cosmetic here. The profiler takes the first two
    # measures it meets when it proposes questions, so the headline figures
    # lead: a dataset that opens on "SalesAmount by Country" is the demo
    # people came for, and one that opens on "UnitPrice by HouseOwnerFlag"
    # is not, even though both are true.
    keep = [
        "SalesAmount", "Profit", "ProfitMargin", "OrderQuantity",
        "Category", "Subcategory", "Product", "Color", "Size",
        "Country", "StateProvince", "City", "SalesTerritoryRegion", "SalesTerritoryGroup",
        "OrderDate", "OrderYear", "OrderQuarter", "OrderMonth", "OrderMonthNumber",
        "OrderDayOfWeek",
        "Education", "Occupation", "Gender", "MaritalStatus", "YearlyIncome",
        "TotalChildren", "HouseOwnerFlag", "NumberCarsOwned", "CommuteDistance",
        "UnitPrice", "ProductStandardCost", "TotalProductCost",
        "TaxAmt", "Freight", "DiscountAmount",
        "SalesOrderNumber", "SalesOrderLineNumber",
    ]
    missing = [c for c in keep if c not in df.columns]
    if missing:
        # Loudly, rather than quietly shipping a table missing a column the
        # demo was built around - a merge that suffixes a name away leaves no
        # other trace.
        raise SystemExit(f"expected columns absent after the joins: {missing}")
    out = df[keep].copy()

    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/claude-0/adventureworks_sales.csv")
    out.to_csv(dest, index=False)
    print(f"\nwrote {dest}: {len(out):,} rows x {len(out.columns)} cols, "
          f"{dest.stat().st_size / 1048576:.1f} MB")
    print(f"years {out.OrderYear.min()}-{out.OrderYear.max()}, "
          f"{out.Country.nunique()} countries, {out.Product.nunique()} products, "
          f"sales {out.SalesAmount.sum():,.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
