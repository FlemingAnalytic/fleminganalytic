# =============================================================================
# SMART ANALYST v2.0 - SERVER DEPLOYMENT
# Refactored for production server deployment with FastAPI router
# =============================================================================

import os
import json
import uuid
import io
import base64
import warnings
import requests
from typing import List, Optional, Dict, Any

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest, RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.feature_selection import mutual_info_regression
import pickle
from scipy import stats

from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

warnings.filterwarnings('ignore')

# =============================================================================
# SETUP DIRECTORIES
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
LIBRARY_FILE = os.path.join(BASE_DIR, "data_library.json")
SAVED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "db", "analyst")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SAVED_DATA_DIR, exist_ok=True)

if not os.path.exists(LIBRARY_FILE):
    with open(LIBRARY_FILE, "w") as f:
        json.dump({}, f)

# =============================================================================
# LLM CONFIGURATION
# =============================================================================
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

# =============================================================================
# PUBLIC DATASETS
# =============================================================================
PUBLIC_DATASETS = {
    # Classic ML Datasets (Commonly used for testing)
    "titanic": {"source": "seaborn", "category": "Classic ML", "description": "Titanic passenger survival data (891 rows)"},
    "tips": {"source": "seaborn", "category": "Classic ML", "description": "Restaurant tipping data (244 rows)"},
    "iris": {"source": "seaborn", "category": "Classic ML", "description": "Fisher's Iris flower measurements (150 rows)"},
    "penguins": {"source": "seaborn", "category": "Classic ML", "description": "Palmer Archipelago penguin species (344 rows)"},
    "mpg": {"source": "seaborn", "category": "Classic ML", "description": "Auto MPG fuel efficiency (398 rows)"},
    "car_crashes": {"source": "seaborn", "category": "Classic ML", "description": "US car crash statistics by state"},
    "planets": {"source": "seaborn", "category": "Science", "description": "Exoplanet discoveries (1K rows)"},
    "geyser": {"source": "seaborn", "category": "Science", "description": "Old Faithful geyser eruption data"},
    "exercise": {"source": "seaborn", "category": "Health", "description": "Exercise and heart rate data"},
    
    # Scikit-Learn Datasets
    "sk_breast_cancer": {"source": "sklearn", "category": "Health", "description": "Breast cancer diagnostic dataset (569 rows)"},
    "sk_diabetes": {"source": "sklearn", "category": "Health", "description": "Diabetes progression dataset (442 rows)"},
    "sk_california_housing": {"source": "sklearn", "category": "Real Estate", "description": "California housing prices by block (20K rows)"},
    
    # Other Common Datasets
    "gapminder": {"source": "url", "category": "Demographics", "description": "Gapminder world health and wealth data", 
                  "url": "https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv"},
    "sp500_companies": {"source": "url", "category": "Finance", "description": "S&P 500 company list and sectors",
                         "url": "https://raw.githubusercontent.com/datasets/s-p-500-companies/master/data/constituents.csv"},

    # Large & Interesting Datasets (40K+ rows)

    # Seaborn - Large
    "diamonds": {"source": "seaborn", "category": "Retail", "description": "Diamond prices with cut, color, clarity & carat (54K rows)"},

    # NYC Open Data & Transportation
    "nyc_311_calls": {"source": "url", "category": "Urban Analytics",
                      "description": "NYC 311 service requests - complaints, noise, graffiti (100K rows)",
                      "url": "https://data.cityofnewyork.us/api/views/erm2-nwe9/rows.csv?accessType=DOWNLOAD&$limit=100000"},

    "nyc_motor_collisions": {"source": "url", "category": "Transportation",
                             "description": "NYC motor vehicle crashes with injuries & fatalities (100K rows)",
                             "url": "https://data.cityofnewyork.us/api/views/h9gi-nx95/rows.csv?accessType=DOWNLOAD&$limit=100000"},

    # Crime & Safety
    "chicago_crimes": {"source": "url", "category": "Crime",
                       "description": "Chicago crime incidents - type, location, arrest (100K rows)",
                       "url": "https://data.cityofchicago.org/api/views/ijzp-q8t2/rows.csv?accessType=DOWNLOAD&$limit=100000"},

    "la_crimes": {"source": "url", "category": "Crime",
                  "description": "Los Angeles crime data with victim demographics (100K rows)",
                  "url": "https://data.lacity.org/api/views/2nrs-mtv8/rows.csv?accessType=DOWNLOAD&$limit=100000"},

    # Finance & Economics
    "lending_club": {"source": "url", "category": "Finance",
                     "description": "Loan data - amounts, interest rates, default risk (100K rows)",
                     "url": "https://raw.githubusercontent.com/nateGeorge/preprocess_lending_club_data/master/data/accepted_2007_to_2018Q4.csv.gz"},

    "us_county_economics": {"source": "url", "category": "Economics",
                            "description": "US county-level economic indicators - income, employment, poverty (47K rows)",
                            "url": "https://raw.githubusercontent.com/plotly/datasets/master/us-county-data.csv"},

    # Health & Medicine
    "covid_us_counties": {"source": "url", "category": "Health",
                          "description": "COVID-19 cases & deaths by US county over time (2M+ rows)",
                          "url": "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"},

    "medicare_spending": {"source": "url", "category": "Healthcare",
                          "description": "Medicare hospital spending per beneficiary by state (50K rows)",
                          "url": "https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0/download?format=csv"},

    # E-commerce & Retail
    "online_retail": {"source": "url", "category": "E-commerce",
                      "description": "UK online retail transactions - products, quantities, countries (541K rows)",
                      "url": "https://raw.githubusercontent.com/databricks/LearningSparkV2/master/chapter4/data/online-retail-dataset.csv"},

    "instacart_orders": {"source": "url", "category": "E-commerce",
                         "description": "Instacart grocery orders - products, departments, reorders (100K rows)",
                         "url": "https://raw.githubusercontent.com/ankur715/Instacart_Market_Basket_Analysis/master/Data/orders.csv"},

    # Sports & Entertainment
    "nba_shots": {"source": "url", "category": "Sports",
                  "description": "NBA shot attempts - player, location, distance, success (128K rows)",
                  "url": "https://raw.githubusercontent.com/swar/nba_api/master/docs/examples/shot_chart_data_20_21.csv"},

    "spotify_tracks": {"source": "url", "category": "Entertainment",
                       "description": "Spotify tracks - audio features, popularity, genres (114K rows)",
                       "url": "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-01-21/spotify_songs.csv"},

    "video_game_sales": {"source": "url", "category": "Entertainment",
                         "description": "Video game sales by platform, genre, publisher (16K rows, comprehensive)",
                         "url": "https://raw.githubusercontent.com/datasets/video-game-sales/main/data/vgsales.csv"},

    # Environment & Energy
    "global_power_plants": {"source": "url", "category": "Energy",
                            "description": "Global power plants - capacity, fuel type, location (35K rows)",
                            "url": "https://raw.githubusercontent.com/wri/global-power-plant-database/master/output_database/global_power_plant_database.csv"},

    "us_wildfires": {"source": "url", "category": "Environment",
                     "description": "US wildfire occurrences - size, cause, location (88K rows)",
                     "url": "https://raw.githubusercontent.com/BuzzFeedNews/2018-07-wildfire-trends/master/data/wildfires.csv"},

    # Aviation & Travel
    "flight_delays": {"source": "url", "category": "Aviation",
                      "description": "US flight delays & cancellations by carrier and airport (100K rows)",
                      "url": "https://raw.githubusercontent.com/plotly/datasets/master/2015_flights.csv"},

    "airbnb_nyc": {"source": "url", "category": "Travel",
                   "description": "NYC Airbnb listings - price, location, reviews, room type (49K rows)",
                   "url": "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2019/2019-07-02/nyc_airbnb_data.csv"},

    # Demographics & Social
    "world_happiness": {"source": "url", "category": "Demographics",
                        "description": "World happiness rankings with GDP, health, freedom scores (782 rows, all countries)",
                        "url": "https://raw.githubusercontent.com/datasets/world-happiness-report/main/data/world-happiness-report.csv"},

    "us_baby_names": {"source": "url", "category": "Demographics",
                      "description": "US baby names by year, gender, and popularity (2M rows)",
                      "url": "https://raw.githubusercontent.com/hadley/data-baby-names/master/baby-names.csv"},

    # Technology
    "github_repos": {"source": "url", "category": "Technology",
                     "description": "GitHub repository statistics - stars, forks, languages (50K rows)",
                     "url": "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2019/2019-11-12/loc_cran_packages.csv"},

    "stackoverflow_survey": {"source": "url", "category": "Technology",
                             "description": "Stack Overflow developer survey - salaries, languages, experience (65K rows)",
                             "url": "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2024/2024-09-03/stackoverflow_survey_questions.csv"},

    # US Census Bureau - Population & Demographics
    "census_county_pop": {"source": "url", "category": "Census",
                          "description": "US County Population Estimates 2020-2023 - Births, Deaths, Migration (3.2K rows)",
                          "url": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/counties/totals/co-est2023-alldata.csv"},

    "census_state_pop": {"source": "url", "category": "Census",
                         "description": "US State Population Estimates 2020-2023 - All Components of Change (52 rows)",
                         "url": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/state/totals/st-est2023-alldata.csv"},

    "census_county_economics": {"source": "url", "category": "Census",
                                "description": "US County Economic Indicators - Income, Employment, Poverty (47K rows)",
                                "url": "https://raw.githubusercontent.com/plotly/datasets/master/us-county-data.csv"},

    # Dynamic Census API Access (Comprehensive Profiles)
    "census_national_demographics": {"source": "census", "category": "Census", "geography": "us",
                                    "description": "US National Comprehensive Demographics (ACS 5-Year Data Profile)"},
    "census_state_demographics": {"source": "census", "category": "Census", "geography": "state",
                                 "description": "US States Comprehensive Demographics - all states (ACS 5-Year Data Profile)"},
    "census_county_demographics": {"source": "census", "category": "Census", "geography": "county",
                                  "description": "US Counties Comprehensive Demographics - all 3,200+ counties (ACS 5-Year Data Profile)"},
    "census_zip_demographics": {"source": "census", "category": "Census", "geography": "zip",
                               "description": "US Zip Codes (ZCTA) Comprehensive Demographics - all 33,000+ codes (ACS 5-Year Data Profile)"},
    "us_car_dealerships": {"source": "url", "category": "Retail",
                           "description": "US franchised car dealerships with addresses and coordinates (19K rows)",
                           "url": "https://raw.githubusercontent.com/simon-wenmouth/dealerships/master/data/normalized.csv"},
    "abs_auto_loans": {"source": "local", "category": "Asset-Backed Securities",
                       "description": "SEC ABS-EE auto loan filings - loan-level data (100K sample)",
                       "path": "auto_loans_analyst_100k.csv"},
    "abs_auto_leases": {"source": "local", "category": "Asset-Backed Securities",
                        "description": "SEC ABS-EE auto lease filings - lease-level data (100K sample)",
                        "path": "auto_leases_analyst_100k.csv"},
    "abs_cmbs_loans": {"source": "local", "category": "Asset-Backed Securities",
                       "description": "SEC ABS-EE CMBS filings - commercial loan-level data with portfolio-loan flag (46K)",
                       "path": "cmbs_analyst.csv"},
    "abs_cmbs_properties": {"source": "local", "category": "Asset-Backed Securities",
                            "description": "SEC ABS-EE CMBS filings - property-level data with tenant & NOI detail (64K)",
                            "path": "cmbs_properties_analyst.csv"},
}




def safe_float(val, decimals=2):
    """Convert to float, replacing inf/nan with None for JSON safety"""
    if val is None or pd.isna(val) or np.isinf(val):
        return None
    return round(float(val), decimals)


def clean_for_json(obj):
    """Recursively clean an object for JSON serialization.

    NaN and infinity are not valid JSON and FastAPI substitutes nothing for
    them: a response containing one fails to encode, and the caller gets a
    bare 500 with no body for a request that was perfectly well formed. Every
    aggregated result has to come through here before it is returned.

    An aggregate is NaN whenever a group has no values at all for its
    measure - averaging chicagoland's `sqft` (missing in 7.9% of rows) by
    `zip` breaks, while averaging `beds` by the same 302 zips does not,
    because some zip holds no sqft anywhere in it. The finer the grouping,
    the likelier that is, so this matters most for exactly the detailed
    questions people ask second.

    null is the truthful answer - there is no average of nothing - and it
    lets a chart draw a gap rather than a zero, which would be a claim the
    data does not make.
    """
    if obj is pd.NaT:
        return None
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (np.floating, np.integer)):
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return None
        return val
    return obj


def load_public_dataset(name: str) -> pd.DataFrame:
    """Load a public dataset by name"""
    if name not in PUBLIC_DATASETS:
        raise ValueError(f"Unknown dataset: {name}")

    info = PUBLIC_DATASETS[name]
    source = info["source"]

    if source == "seaborn":
        return sns.load_dataset(name)

    elif source == "sklearn":
        from sklearn import datasets
        sklearn_map = {
            "sk_wine": datasets.load_wine,
            "sk_breast_cancer": datasets.load_breast_cancer,
            "sk_diabetes": datasets.load_diabetes,
            "sk_california_housing": datasets.fetch_california_housing,
        }
        loader = sklearn_map.get(name)
        if not loader:
            raise ValueError(f"Unknown sklearn dataset: {name}")
        data = loader()
        df = pd.DataFrame(data.data, columns=data.feature_names)
        if hasattr(data, 'target'):
            df['target'] = data.target
        return df

    elif source == "url":
        url = info["url"]
        kwargs = {}
        if "columns" in info:
            kwargs["names"] = info["columns"]
            kwargs["header"] = None
        if "sep" in info:
            sep = info["sep"]
            if sep == "\\s+":
                kwargs["sep"] = r"\s+"
            else:
                kwargs["sep"] = sep
        if "na_values" in info:
            kwargs["na_values"] = info["na_values"]

        # Census Bureau URLs often have ISO-8859-1 encoding
        if "census.gov" in url:
            try:
                return pd.read_csv(url, encoding='utf-8', **kwargs)
            except UnicodeDecodeError:
                return pd.read_csv(url, encoding='iso-8859-1', **kwargs)
        
        return pd.read_csv(url, **kwargs)

    elif source == "local":
        filepath = os.path.join(SAVED_DATA_DIR, info["path"])
        return pd.read_csv(filepath)

    elif source == "census":
        return fetch_census_comprehensive(info.get("geography", "county"))

    else:
        raise ValueError(f"Unknown source: {source}")


def fetch_census_comprehensive(geography="county"):
    """
    Fetch comprehensive demographics from Census Bureau API (ACS 5-Year Data Profiles).
    Optimized for high performance by fetching curated high-impact variables.
    """
    import requests
    # Keep base URL
    base_url = "https://api.census.gov/data/2022/acs/acs5/profile"
    
    geo_map = {
        "us": "us:1",
        "state": "state:*",
        "county": "county:*",
        "zip": "zip code tabulation area:*"
    }
    
    # Curated high-impact demographics from ALL profile groups (DP02-DP05)
    # This is MUCH faster than 'group(DPxx)' which returns hundreds of variables per request
    ACS_CURATED = {
        # DP02: Social
        "DP02_0001E": "Household_Total", "DP02_0068PE": "Pct_Bachelors_Degree_Plus", "DP02_0154PE": "Pct_Broadband_Internet",
        # DP03: Economic
        "DP03_0001E": "Labor_Force_Base", "DP03_0009PE": "Pct_Unemployed", "DP03_0062E": "Median_Household_Income", 
        "DP03_0088E": "Per_Capita_Income", "DP03_0128PE": "Pct_Families_Poverty", "DP03_0099PE": "Pct_Health_Insurance",
        # DP04: Housing
        "DP04_0001E": "Housing_Units_Total", "DP04_0046PE": "Pct_Owner_Occupied", "DP04_0089E": "Median_Home_Value", 
        "DP04_0134E": "Median_Gross_Rent", "DP04_0003PE": "Pct_Vacant_Housing",
        # DP05: Demographic
        "DP05_0001E": "Total_Population", "DP05_0018E": "Median_Age", "DP05_0019PE": "Pct_Male", 
        "DP05_0037PE": "Pct_White", "DP05_0038PE": "Pct_Black", "DP05_0044PE": "Pct_Asian", "DP05_0071PE": "Pct_Hispanic_Latino"
    }
    
    # Construct comma separated list of variables
    # We include 'NAME' for validation
    vars_to_fetch = ["NAME"] + list(ACS_CURATED.keys())
    
    params = {
        "get": ",".join(vars_to_fetch),
        "for": geo_map.get(geography, "county:*")
    }
    
    try:
        # Increase timeout for Census API to 90s
        resp = requests.get(base_url, params=params, timeout=90)
        
        if resp.status_code == 200:
            data = resp.json()
            headers = data[0]
            rows = data[1:]
            df = pd.DataFrame(rows, columns=headers)
            
            # Map codes to human readable names
            name_map = {k: v for k, v in ACS_CURATED.items()}
            # Also keep geo columns
            df.rename(columns=name_map, inplace=True)
            
            # Convert values to numeric (Census returns everything as strings)
            # Geography columns like 'state', 'county', 'zip code tabulation area' should remain strings
            geo_cols = ['state', 'county', 'zip code tabulation area', 'NAME', 'us']
            for col in df.columns:
                if col not in geo_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
        else:
            # If large fetch fails, or for specific errors
            print(f"Census API Error: {resp.status_code} {resp.text}")
            raise ValueError(f"Census Bureau API returned error {resp.status_code}. It may be currently overloaded.")
            
    except Exception as e:
        print(f"Census Fetch Exception: {e}")
        # Fallback to a VERY minimal set if the curated list is still too much (should not happen)
        raise e




def detect_quoted_columns(content: bytes) -> set:
    """
    Detect columns where values are quoted in the CSV.
    These should be treated as strings even if they contain numeric values.
    Examples: zip codes like "10001", years like "2024"
    """
    import csv

    try:
        # Decode content and read first N lines
        text = content.decode('utf-8')
        lines = text.split('\n')[:100]  # Check first 100 rows

        if not lines:
            return set()

        # Parse with csv module to detect quoting
        reader = csv.reader(lines)
        headers = next(reader, None)
        if not headers:
            return set()

        # Track which column indices have quoted values
        quoted_cols = set()

        # Re-read to check each cell's quoting
        # We need to check the raw text for quotes
        for line in lines[1:]:  # Skip header
            if not line.strip():
                continue

            # Find fields that are surrounded by quotes
            # Match pattern: ,"value", or ^"value", or ,"value"$
            in_quote = False
            field_start = 0
            field_idx = 0
            i = 0

            while i < len(line):
                char = line[i]

                if char == '"' and not in_quote:
                    in_quote = True
                    # Check if this field looks numeric but is quoted
                    # Find the end of the quoted field
                    end_quote = line.find('"', i + 1)
                    if end_quote > i + 1:
                        field_value = line[i+1:end_quote].strip()
                        # If the quoted value looks like a number, mark this column
                        if field_value and field_value.replace('.', '').replace('-', '').isdigit():
                            if field_idx < len(headers):
                                quoted_cols.add(headers[field_idx])
                elif char == '"' and in_quote:
                    in_quote = False
                elif char == ',' and not in_quote:
                    field_idx += 1

                i += 1

        return quoted_cols

    except Exception:
        return set()


def load_from_url(url: str) -> pd.DataFrame:
    """Load dataset from a direct URL"""
    import requests
    url_lower = url.lower()

    if url_lower.endswith('.xlsx') or url_lower.endswith('.xls'):
        return pd.read_excel(url)
    elif url_lower.endswith('.json'):
        return pd.read_json(url)
    elif url_lower.endswith('.parquet'):
        return pd.read_parquet(url)
    else:
        try:
            # Fetch content to detect quoted columns
            response = requests.get(url, timeout=30)
            content = response.content
            quoted_columns = detect_quoted_columns(content)
            dtype_overrides = {col: str for col in quoted_columns}

            df = pd.read_csv(io.BytesIO(content), dtype=dtype_overrides if dtype_overrides else None)
            if len(df.columns) == 1 and ';' in df.columns[0]:
                df = pd.read_csv(io.BytesIO(content), sep=';', dtype=dtype_overrides if dtype_overrides else None)
            elif len(df.columns) == 1 and '\t' in df.columns[0]:
                df = pd.read_csv(io.BytesIO(content), sep='\t', dtype=dtype_overrides if dtype_overrides else None)
            return df
        except Exception as e:
            raise ValueError(f"Could not parse URL: {e}")


# =============================================================================
# DATA PROFILER ENGINE
# =============================================================================
class DataProfiler:
    """Automatically analyzes and profiles any dataset"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.profile = {}
        self.columns_meta = {}
        self.correlations = None
        self.insights = []
        self.suggested_questions = []
        self.duplicates = {}

    def run_full_profile(self) -> dict:
        self._analyze_columns()
        self._compute_correlations()
        self._detect_anomalies()
        self._detect_duplicates()
        self._generate_insights()
        self._suggest_questions()

        return {
            "shape": {"rows": len(self.df), "cols": len(self.df.columns)},
            "columns": self.columns_meta,
            "correlations": self.correlations,
            "insights": self.insights,
            "suggested_questions": self.suggested_questions,
            "duplicates": self.duplicates
        }

    def _analyze_columns(self):
        for col in self.df.columns:
            meta = {"name": col}
            series = self.df[col]
            meta["total"] = len(series)
            meta["missing"] = int(series.isna().sum())
            meta["missing_pct"] = round(meta["missing"] / meta["total"] * 100, 1)
            meta["unique"] = int(series.nunique())
            meta["unique_pct"] = round(meta["unique"] / meta["total"] * 100, 1)

            # Detect geographic indicators
            col_lower = col.lower()
            if any(k in col_lower for k in ['zip', 'postal', 'zcta']):
                meta["geo_hint"] = "zip"
            elif any(k in col_lower for k in ['state', 'region', 'province']) and 'stat' in col_lower: # avoid 'status'
                 if 'status' not in col_lower:
                    meta["geo_hint"] = "state"
            elif any(k in col_lower for k in ['county', 'parish', 'municipality']):
                meta["geo_hint"] = "county"
            elif col_lower in ['st', 'cty']: # common abbreviations
                meta["geo_hint"] = "state" if col_lower == 'st' else "county"

            if pd.api.types.is_numeric_dtype(series):
                if meta["unique"] <= 20 or meta["unique_pct"] < 5:
                    meta["type"] = "categorical_numeric"
                    meta["role"] = "dimension"
                else:
                    meta["type"] = "continuous"
                    meta["role"] = "measure"

                clean = series.replace([np.inf, -np.inf], np.nan).dropna()
                if len(clean) > 0:
                    meta["stats"] = {
                        "mean": safe_float(clean.mean()),
                        "median": safe_float(clean.median()),
                        "std": safe_float(clean.std()) if len(clean) > 1 else 0,
                        "min": safe_float(clean.min()),
                        "max": safe_float(clean.max()),
                        "q25": safe_float(clean.quantile(0.25)),
                        "q75": safe_float(clean.quantile(0.75)),
                        "skew": safe_float(clean.skew()) if len(clean) > 2 else 0,
                        "kurtosis": safe_float(clean.kurtosis()) if len(clean) > 3 else 0
                    }
                    skew_val = meta["stats"]["skew"] or 0
                    if abs(skew_val) < 0.5:
                        meta["distribution"] = "normal"
                    elif skew_val > 0.5:
                        meta["distribution"] = "right_skewed"
                    else:
                        meta["distribution"] = "left_skewed"

            elif pd.api.types.is_datetime64_any_dtype(series):
                meta["type"] = "datetime"
                meta["role"] = "dimension"
                clean = series.dropna()
                if len(clean) > 0:
                    meta["stats"] = {
                        "min": str(clean.min()),
                        "max": str(clean.max()),
                        "range_days": (clean.max() - clean.min()).days
                    }
            else:
                meta["type"] = "categorical"
                meta["role"] = "dimension"
                top = series.value_counts().head(10)
                meta["top_values"] = [{"value": str(k), "count": int(v)} for k, v in top.items()]

            self.columns_meta[col] = meta

    def _compute_correlations(self):
        numeric_cols = [c for c, m in self.columns_meta.items() if m["type"] == "continuous"]

        if len(numeric_cols) < 2:
            self.correlations = {"matrix": {}, "strong_pairs": []}
            return

        corr_df = self.df[numeric_cols].corr()

        strong = []
        for i, c1 in enumerate(numeric_cols):
            for j, c2 in enumerate(numeric_cols):
                if i < j:
                    val = corr_df.loc[c1, c2]
                    if not np.isnan(val) and abs(val) > 0.5:
                        strong.append({
                            "col1": c1, "col2": c2,
                            "correlation": round(val, 3),
                            "strength": "strong" if abs(val) > 0.7 else "moderate"
                        })

        strong.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        # Ensure matrix is JSON compliant by replacing NaNs
        matrix = corr_df.round(3).replace({np.nan: None}).to_dict()
        self.correlations = {"matrix": matrix, "strong_pairs": strong[:20]}

    def _detect_anomalies(self):
        for col, meta in self.columns_meta.items():
            if meta["type"] != "continuous":
                continue
            series = self.df[col].replace([np.inf, -np.inf], np.nan).dropna()
            if len(series) < 10:
                continue
            q1, q3 = series.quantile([0.25, 0.75])
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers = series[(series < lower) | (series > upper)]
            meta["outliers"] = {
                "count": len(outliers), "pct": round(len(outliers) / len(series) * 100, 1),
                "lower_bound": safe_float(lower), "upper_bound": safe_float(upper)
            }

    def _detect_duplicates(self):
        """Detect duplicate rows in the dataset"""
        total_rows = len(self.df)
        duplicate_mask = self.df.duplicated(keep=False)
        duplicate_count = duplicate_mask.sum()
        exact_duplicate_count = self.df.duplicated(keep='first').sum()

        self.duplicates = {
            "total_duplicate_rows": int(duplicate_count),
            "exact_duplicates": int(exact_duplicate_count),
            "duplicate_pct": round(duplicate_count / total_rows * 100, 1) if total_rows > 0 else 0,
            "unique_rows": int(total_rows - exact_duplicate_count)
        }

    def _generate_insights(self):
        insights = []
        dims = [c for c, m in self.columns_meta.items() if m["role"] == "dimension"]
        measures = [c for c, m in self.columns_meta.items() if m["role"] == "measure"]

        insights.append({
            "type": "overview", "priority": 1, "title": "Dataset Structure",
            "detail": f"Found {len(dims)} dimensions and {len(measures)} measures across {len(self.df):,} rows"
        })

        high_missing = [(c, m["missing_pct"]) for c, m in self.columns_meta.items() if m["missing_pct"] > 10]
        if high_missing:
            high_missing.sort(key=lambda x: x[1], reverse=True)
            insights.append({
                "type": "data_quality", "priority": 2, "title": "Missing Data Alert",
                "detail": f"{len(high_missing)} columns have >10% missing. Highest: {high_missing[0][0]} ({high_missing[0][1]}%)"
            })

        if self.duplicates["duplicate_pct"] > 1:
            insights.append({
                "type": "data_quality", "priority": 2, "title": "Duplicate Rows Detected",
                "detail": f"{self.duplicates['exact_duplicates']:,} duplicate rows found ({self.duplicates['duplicate_pct']}% of data)"
            })

        if self.correlations and self.correlations["strong_pairs"]:
            top = self.correlations["strong_pairs"][0]
            insights.append({
                "type": "correlation", "priority": 2, "title": "Strong Correlation Found",
                "detail": f"{top['col1']} and {top['col2']} have {top['strength']} correlation ({top['correlation']})"
            })

        outlier_cols = [(c, m["outliers"]["pct"]) for c, m in self.columns_meta.items()
                       if "outliers" in m and m["outliers"]["pct"] > 5]
        if outlier_cols:
            outlier_cols.sort(key=lambda x: x[1], reverse=True)
            insights.append({
                "type": "anomaly", "priority": 3, "title": "Outliers Detected",
                "detail": f"{outlier_cols[0][0]} has {outlier_cols[0][1]}% outliers"
            })

        # 3. Geographic Enrichment Analysis
        # Only suggest if we haven't already enriched with Census data
        has_census_data = any(c in self.columns_meta for c in ['Total_Population', 'Median_Household_Income'])
        geo_cols = {m.get("geo_hint"): c for c, m in self.columns_meta.items() if m.get("geo_hint")}
        if geo_cols and not has_census_data:
            best_hint = "zip" if "zip" in geo_cols else ("county" if "county" in geo_cols else "state")
            insights.append({
                "type": "geo_enrichment", "priority": 1, "title": "Census Data Available",
                "detail": f"We detected a '{geo_cols[best_hint]}' column. You can enrich this dataset with US Census demographics.",
                "hint": best_hint,
                "column": geo_cols[best_hint]
            })

        self.insights = sorted(insights, key=lambda x: x["priority"])

    def _suggest_questions(self):
        questions = []
        dims = [c for c, m in self.columns_meta.items() if m["role"] == "dimension"]
        measures = [c for c, m in self.columns_meta.items() if m["role"] == "measure"]

        # Filter dimensions to find "useful" grouping columns
        # Exclude Unique IDs (high cardinality) and Constants (1 unique value)
        useful_dims = [
            d for d in dims 
            if 1 < self.columns_meta[d]["unique"] <= 100
        ]
        
        # Sort useful dims by uniqueness (prefer fewer categories for simpler charts)
        useful_dims.sort(key=lambda d: self.columns_meta[d]["unique"])

        for dim in useful_dims[:3]:
            for meas in measures[:2]:
                questions.append({
                    "type": "breakdown", "question": f"How does {meas} vary by {dim}?",
                    "action": {"type": "pivot", "rows": [dim], "values": [meas], "agg": "mean"}
                })

        if self.correlations and self.correlations["strong_pairs"]:
            for pair in self.correlations["strong_pairs"][:3]:
                questions.append({
                    "type": "relationship",
                    "question": f"What's the relationship between {pair['col1']} and {pair['col2']}?",
                    "action": {"type": "scatter", "x": pair["col1"], "y": pair["col2"]}
                })

        if len(useful_dims) >= 2 and measures:
            questions.append({
                "type": "multi_dim",
                "question": f"How does {measures[0]} break down by {useful_dims[0]} and {useful_dims[1]}?",
                "action": {"type": "pivot", "rows": [useful_dims[0]], "cols": [useful_dims[1]], "values": [measures[0]], "agg": "sum"}
            })

        for meas in measures[:2]:
            questions.append({
                "type": "classification",
                "question": f"Can we segment the data into groups based on {meas}?",
                "action": {"type": "classify", "column": meas, "method": "kmeans", "n_clusters": 4}
            })

        self.suggested_questions = questions[:10]


# =============================================================================
# CLASSIFIER ENGINE
# =============================================================================
class ColumnClassifier:
    @staticmethod
    def quintiles(series, labels=True):
        if labels:
            return pd.qcut(series, 5, labels=['Bottom 20%', 'Low', 'Middle', 'High', 'Top 20%'], duplicates='drop')
        return pd.qcut(series, 5, labels=False, duplicates='drop')

    @staticmethod
    def quartiles(series, labels=True):
        if labels:
            return pd.qcut(series, 4, labels=['Q1 (Bottom)', 'Q2', 'Q3', 'Q4 (Top)'], duplicates='drop')
        return pd.qcut(series, 4, labels=False, duplicates='drop')

    @staticmethod
    def deciles(series, labels=True):
        if labels:
            return pd.qcut(series, 10, labels=[f'D{i}' for i in range(1, 11)], duplicates='drop')
        return pd.qcut(series, 10, labels=False, duplicates='drop')

    @staticmethod
    def kmeans_cluster(df, columns, n_clusters=4):
        data = df[columns].dropna()
        if len(data) < n_clusters:
            return pd.Series(['Insufficient Data'] * len(df), index=df.index)
        scaler = StandardScaler()
        scaled = scaler.fit_transform(data)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(scaled)
        result = pd.Series(index=df.index, dtype=object)
        result[data.index] = [f'Cluster {c+1}' for c in clusters]
        return result.fillna('No Data')

    @staticmethod
    def statistical_class(series):
        mean, std = series.mean(), series.std()
        def classify(x):
            if pd.isna(x): return 'No Data'
            z = (x - mean) / std if std > 0 else 0
            if z < -2: return 'Very Low'
            elif z < -1: return 'Low'
            elif z < 1: return 'Average'
            elif z < 2: return 'High'
            return 'Very High'
        return series.apply(classify)


# =============================================================================
# PIVOT ENGINE
# =============================================================================
class PivotEngine:
    def __init__(self, df):
        self.df = df
        self.classified_columns = {}

    def add_classification(self, name, series):
        self.classified_columns[name] = series

    def create_pivot(self, rows, cols=None, values=None, aggfunc='sum', filters=None, weight_col=None):
        work_df = self.df.copy()
        for name, series in self.classified_columns.items():
            work_df[name] = series

        if filters:
            for col, vals in filters.items():
                if col in work_df.columns and vals:
                    work_df = work_df[work_df[col].isin(vals)]

        if len(work_df) == 0:
            return {"error": "No data after filters", "data": [], "columns": [], "has_col_dims": False}

        # Handle weighted average separately
        is_weighted_avg = aggfunc.lower() in ('wtd_avg', 'wtd avg', 'weighted_avg', 'weighted avg')

        if is_weighted_avg:
            if not weight_col or weight_col not in work_df.columns:
                return {"error": "Weighted average requires a valid weight column", "data": [], "columns": [], "has_col_dims": False}

        agg_map = {
            'sum': 'sum',
            'mean': 'mean',
            'avg': 'mean',
            'count': 'count',
            'min': 'min',
            'max': 'max',
            'median': 'median',
            'std': 'std',
            'var': 'var',
            'nunique': 'nunique',
            'first': 'first',
            'last': 'last',
            'p25': lambda x: x.quantile(0.25),
            'p75': lambda x: x.quantile(0.75),
            'p90': lambda x: x.quantile(0.90),
        }
        agg = agg_map.get(aggfunc.lower(), 'sum')

        if not values:
            values = [c for c in work_df.columns if pd.api.types.is_numeric_dtype(work_df[c])][:1]

        if len(values) == 1:
            values = values[0]

        try:
            # Handle weighted average with custom aggregation
            if is_weighted_avg:
                value_col = values if isinstance(values, str) else values[0]

                # Define weighted average function for groupby
                def weighted_avg(group):
                    weights = group[weight_col]
                    vals = group[value_col]
                    # Handle case where all weights are 0 or NaN
                    if weights.sum() == 0:
                        return np.nan
                    return (weights * vals).sum() / weights.sum()

                if cols and len(cols) > 0:
                    # For pivot with columns: manually compute weighted avg per group
                    group_cols = rows + cols
                    grouped = work_df.groupby(group_cols, as_index=False).apply(
                        lambda g: pd.Series({value_col: weighted_avg(g)})
                    ).reset_index(drop=True)

                    # Reconstruct the group columns from the groupby keys
                    pivot = grouped.pivot_table(
                        values=value_col, index=rows, columns=cols,
                        aggfunc='first', fill_value=0
                    )

                    # Add margins (totals) - calculate weighted avg for row/col totals
                    # Row totals (for each row dimension value)
                    row_totals = work_df.groupby(rows).apply(weighted_avg).rename('Total')
                    pivot['Total'] = row_totals

                    # Column totals (for each column dimension value)
                    col_totals = work_df.groupby(cols).apply(weighted_avg)
                    col_totals['Total'] = weighted_avg(work_df)  # Grand total
                    col_totals.name = 'Total'
                    pivot.loc['Total'] = col_totals

                    if isinstance(pivot.columns, pd.MultiIndex):
                        pivot.columns = [' | '.join(str(c) for c in col).strip() for col in pivot.columns.values]
                    else:
                        pivot.columns = [str(c) for c in pivot.columns]

                    pivot_reset = pivot.reset_index()
                    columns = [str(c) if not isinstance(c, tuple) else ' | '.join(str(x) for x in c) for c in pivot_reset.columns]
                    pivot_reset.columns = columns

                    return {
                        "data": clean_for_json(pivot_reset.to_dict('records')),
                        "columns": columns,
                        "shape": {"rows": len(pivot_reset), "cols": len(columns)},
                        "has_col_dims": True,
                        "row_dims": rows
                    }
                else:
                    # Simple groupby without column dimensions
                    pivot = work_df.groupby(rows, as_index=False).apply(
                        lambda g: pd.Series({value_col: weighted_avg(g)})
                    ).reset_index(drop=True)

                    # Reconstruct the row dimension columns
                    row_values = work_df.groupby(rows).first().reset_index()[rows]
                    pivot = pd.concat([row_values, pivot], axis=1)

                    # Calculate overall weighted average for total
                    totals = {'_is_total': True}
                    for col in pivot.columns:
                        if col in rows:
                            totals[col] = 'TOTAL'
                        else:
                            totals[col] = weighted_avg(work_df)

                    data = pivot.to_dict('records')
                    data.append(totals)
                    data = clean_for_json(data)

                    return {
                        "data": data,
                        "columns": list(pivot.columns),
                        "shape": {"rows": len(data), "cols": len(pivot.columns)},
                        "has_col_dims": False,
                        "row_dims": rows
                    }

            # Standard aggregation (non-weighted)
            if cols and len(cols) > 0:
                pivot = pd.pivot_table(
                    work_df, values=values, index=rows, columns=cols,
                    aggfunc=agg, margins=True, margins_name='Total', fill_value=0
                )

                if isinstance(pivot.columns, pd.MultiIndex):
                    pivot.columns = [' | '.join(str(c) for c in col).strip() for col in pivot.columns.values]
                else:
                    pivot.columns = [str(c) for c in pivot.columns]

                pivot_reset = pivot.reset_index()
                columns = [str(c) if not isinstance(c, tuple) else ' | '.join(str(x) for x in c) for c in pivot_reset.columns]
                pivot_reset.columns = columns

                return {
                    "data": clean_for_json(pivot_reset.to_dict('records')),
                    "columns": columns,
                    "shape": {"rows": len(pivot_reset), "cols": len(columns)},
                    "has_col_dims": True,
                    "row_dims": rows
                }
            else:
                pivot = work_df.groupby(rows, as_index=False).agg({values: agg} if isinstance(values, str) else {v: agg for v in values})

                totals = {'_is_total': True}
                for col in pivot.columns:
                    if col in rows:
                        totals[col] = 'TOTAL'
                    elif pd.api.types.is_numeric_dtype(pivot[col]):
                        totals[col] = float(pivot[col].sum())

                data = pivot.to_dict('records')
                data.append(totals)
                data = clean_for_json(data)

                return {
                    "data": data,
                    "columns": list(pivot.columns),
                    "shape": {"rows": len(data), "cols": len(pivot.columns)},
                    "has_col_dims": False,
                    "row_dims": rows
                }

        except Exception as e:
            return {"error": f"{str(e)}", "data": [], "columns": [], "has_col_dims": False}


# =============================================================================
# VISUALIZATION ENGINE
# =============================================================================
class VizEngine:
    @staticmethod
    def correlation_heatmap(df):
        numeric = df.select_dtypes(include=[np.number])
        if len(numeric.columns) < 2: return None
        corr = numeric.corr()
        fig, ax = plt.subplots(figsize=(10, 8))
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, cmap='RdBu_r', center=0, fmt='.2f', square=True, ax=ax)
        ax.set_title('Correlation Matrix', fontsize=14, fontweight='bold')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    @staticmethod
    def distribution_plot(series, title=''):
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        axes[0].hist(series.dropna(), bins=30, edgecolor='white', alpha=0.7, color='#4F46E5')
        axes[0].set_title(f'Distribution of {title}', fontweight='bold')
        axes[1].boxplot(series.dropna(), vert=True)
        axes[1].set_title(f'Box Plot of {title}', fontweight='bold')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    @staticmethod
    def scatter_plot(df, x, y, color=None):
        fig, ax = plt.subplots(figsize=(10, 6))
        if color and color in df.columns:
            for cat in df[color].unique():
                mask = df[color] == cat
                ax.scatter(df.loc[mask, x], df.loc[mask, y], label=str(cat), alpha=0.6)
            ax.legend(title=color, bbox_to_anchor=(1.05, 1))
        else:
            ax.scatter(df[x], df[y], alpha=0.6, color='#4F46E5')
        ax.set_xlabel(x); ax.set_ylabel(y)
        ax.set_title(f'{y} vs {x}', fontweight='bold')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    @staticmethod
    def bar_chart(df, x, y, top_n=20):
        plot_df = df.groupby(x)[y].mean().sort_values(ascending=False).head(top_n)
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(range(len(plot_df)), plot_df.values, color='#4F46E5', edgecolor='white')
        ax.set_xticks(range(len(plot_df)))
        ax.set_xticklabels(plot_df.index, rotation=45, ha='right')
        ax.set_xlabel(x); ax.set_ylabel(f'Average {y}')
        ax.set_title(f'Average {y} by {x}', fontweight='bold')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    @staticmethod
    def cluster_plot(df, x, y, cluster_col):
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set2(np.linspace(0, 1, df[cluster_col].nunique()))
        for i, cluster in enumerate(sorted(df[cluster_col].unique())):
            mask = df[cluster_col] == cluster
            ax.scatter(df.loc[mask, x], df.loc[mask, y], c=[colors[i]], label=str(cluster), alpha=0.6, s=50)
        ax.set_xlabel(x); ax.set_ylabel(y)
        ax.set_title(f'Cluster Analysis: {cluster_col}', fontweight='bold')
        ax.legend(title='Cluster', bbox_to_anchor=(1.05, 1))
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')


# =============================================================================
# ML MODELING ENGINE
# =============================================================================
class ModelEngine:
    """Handles ML model training, feature importance, and predictions"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.model = None
        self.feature_names = []
        self.target_name = None
        self.encoders = {}
        self.feature_info = {}
        self.scaler = None
        self.model_stats = {}

    def _classify_column(self, col: str, series: pd.Series) -> dict:
        """Intelligently classify a column's data type and recommend encoding strategy"""
        col_lower = col.lower()
        n_unique = series.nunique()
        n_total = len(series.dropna())
        unique_ratio = n_unique / n_total if n_total > 0 else 0

        result = {"original_name": col, "n_unique": n_unique, "n_total": n_total}

        # Check if numeric
        is_numeric = pd.api.types.is_numeric_dtype(series)

        # Detect pseudo-categorical numerics (zipcode, ID, year, FIPS, etc.)
        if is_numeric:
            id_hints = ['id', 'code', 'zip', 'postal', 'fips', 'zcta', 'phone', 'ssn', 'account', 'number']
            is_id_like = any(h in col_lower for h in id_hints)
            # Also detect if values look like codes: high cardinality integers with no meaningful numeric relationship
            all_ints = series.dropna().apply(lambda x: float(x).is_integer()).all() if n_total > 0 else False

            if is_id_like:
                result["detected_type"] = "id_like"
                if n_unique <= 50:
                    result["strategy"] = "dummy"
                    result["reason"] = f"ID-like column with {n_unique} unique values — one-hot encoding"
                elif n_unique <= 200:
                    result["strategy"] = "group"
                    result["reason"] = f"ID-like column with {n_unique} unique values — frequency-based grouping"
                else:
                    result["strategy"] = "drop"
                    result["reason"] = f"High-cardinality ID column ({n_unique} unique) — no predictive value"
                return result

            if all_ints and n_unique <= 20 and unique_ratio < 0.05:
                result["detected_type"] = "categorical_numeric"
                result["strategy"] = "dummy"
                result["reason"] = f"Numeric with only {n_unique} distinct values — treating as categories"
                return result

            if all_ints and 'year' in col_lower:
                result["detected_type"] = "ordinal"
                result["strategy"] = "numeric"
                result["reason"] = "Year column — keeping as ordinal numeric"
                return result

            result["detected_type"] = "continuous"
            result["strategy"] = "numeric"
            result["reason"] = "Continuous numeric — used as-is"
            return result

        # Non-numeric columns
        if n_unique <= 2:
            result["detected_type"] = "binary"
            result["strategy"] = "binary"
            result["reason"] = f"Binary column ({n_unique} values) — single 0/1 encoding"
        elif n_unique <= 15:
            result["detected_type"] = "low_cardinality"
            result["strategy"] = "dummy"
            result["reason"] = f"Low cardinality ({n_unique} categories) — one-hot encoding"
        elif n_unique <= 50:
            result["detected_type"] = "medium_cardinality"
            result["strategy"] = "dummy_top"
            result["reason"] = f"Medium cardinality ({n_unique}) — one-hot top 15 categories"
        elif n_unique <= 200:
            result["detected_type"] = "high_cardinality"
            result["strategy"] = "group"
            result["reason"] = f"High cardinality ({n_unique}) — frequency-based grouping into buckets"
        else:
            result["detected_type"] = "very_high_cardinality"
            result["strategy"] = "drop"
            result["reason"] = f"Very high cardinality ({n_unique} unique / {n_total} rows) — likely an identifier, dropping"

        # Override: detect name/address/description columns — always drop
        text_hints = ['name', 'description', 'address', 'comment', 'note', 'text', 'title', 'url', 'email', 'path']
        if any(h in col_lower for h in text_hints) and n_unique > 50:
            result["strategy"] = "drop"
            result["reason"] = f"Free-text column ({n_unique} unique values) — no predictive value"

        return result

    def _encode_feature(self, col: str, series: pd.Series, classification: dict) -> pd.DataFrame:
        """Encode a single feature based on its classification"""
        strategy = classification["strategy"]

        if strategy == "numeric":
            clean = series.fillna(series.median())
            return clean.to_frame(col)

        elif strategy == "binary":
            cats = series.dropna().unique()
            if len(cats) == 2:
                mapping = {cats[0]: 0, cats[1]: 1}
                encoded = series.map(mapping).fillna(0).astype(int)
                return encoded.to_frame(col)
            else:
                return series.fillna(0).astype(int).to_frame(col)

        elif strategy == "dummy":
            cats = series.dropna().unique().tolist()
            self.encoders[col] = cats
            dummies = pd.DataFrame()
            for cat in cats:
                dummies[f"{col}_encoded_{cat}"] = (series == cat).astype(int)
            return dummies

        elif strategy == "dummy_top":
            top_cats = series.value_counts().head(15).index.tolist()
            self.encoders[col] = top_cats
            dummies = pd.DataFrame()
            for cat in top_cats:
                dummies[f"{col}_encoded_{cat}"] = (series == cat).astype(int)
            return dummies

        elif strategy == "group":
            # Group into frequency-based buckets
            freq = series.value_counts()
            top_10 = freq.head(10).index.tolist()
            self.encoders[col] = top_10
            grouped = series.apply(lambda x: x if x in top_10 else '_OTHER_')
            dummies = pd.DataFrame()
            for cat in top_10 + ['_OTHER_']:
                dummies[f"{col}_encoded_{cat}"] = (grouped == cat).astype(int)
            return dummies

        else:  # drop
            return pd.DataFrame()

    def analyze_features(self, target_col: str) -> dict:
        """Deep feature analysis: correlation, covariance, mutual information, smart categorical handling"""
        if target_col not in self.df.columns:
            raise ValueError(f"Target column '{target_col}' not found")

        if not pd.api.types.is_numeric_dtype(self.df[target_col]):
            raise ValueError(f"Target column must be numeric")

        self.target_name = target_col
        y_full = self.df[target_col].dropna()

        feature_cols = [c for c in self.df.columns if c != target_col]

        # Step 1: Classify every column
        classifications = {}
        for col in feature_cols:
            classifications[col] = self._classify_column(col, self.df[col])

        # Step 2: Encode features based on classification
        encoded_dfs = []
        col_mapping = {}  # encoded_col -> original_col
        usable_cols = []
        dropped_cols = []

        for col in feature_cols:
            cls = classifications[col]
            if cls["strategy"] == "drop":
                dropped_cols.append({"feature": col, "reason": cls["reason"]})
                continue

            encoded = self._encode_feature(col, self.df[col], cls)
            if encoded.empty:
                dropped_cols.append({"feature": col, "reason": cls["reason"]})
                continue

            usable_cols.append(col)
            for enc_col in encoded.columns:
                col_mapping[enc_col] = col
            encoded_dfs.append(encoded)

        if not encoded_dfs:
            raise ValueError("No usable features found after classification")

        X = pd.concat(encoded_dfs, axis=1)
        valid_idx = y_full.index.intersection(X.index)
        X = X.loc[valid_idx]
        y = y_full.loc[valid_idx]

        # Drop any remaining NaN rows
        mask = X.notna().all(axis=1) & y.notna()
        X = X.loc[mask]
        y = y.loc[mask]

        if len(X) < 30:
            raise ValueError(f"Only {len(X)} complete rows available — need at least 30 for analysis")

        # Step 3: Correlation with target (for numeric features only)
        correlations = {}
        for col in usable_cols:
            if classifications[col]["strategy"] == "numeric":
                series = self.df[col].loc[y.index]
                corr_val = series.corr(y)
                if not np.isnan(corr_val):
                    correlations[col] = round(float(corr_val), 4)

        # Step 4: Mutual Information (captures non-linear relationships)
        try:
            mi_scores = mutual_info_regression(X, y, random_state=42, n_neighbors=5)
            mi_by_feature = {}
            for enc_col, mi in zip(X.columns, mi_scores):
                orig = col_mapping.get(enc_col, enc_col)
                mi_by_feature[orig] = mi_by_feature.get(orig, 0) + mi
            # Normalize
            mi_max = max(mi_by_feature.values()) if mi_by_feature else 1
            if mi_max > 0:
                mi_by_feature = {k: round(v / mi_max, 4) for k, v in mi_by_feature.items()}
        except Exception:
            mi_by_feature = {}

        # Step 5: Random Forest importance
        rf = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(X, y)

        rf_by_feature = {}
        for enc_col, imp in zip(X.columns, rf.feature_importances_):
            orig = col_mapping.get(enc_col, enc_col)
            rf_by_feature[orig] = rf_by_feature.get(orig, 0) + imp

        # Step 6: Detect multicollinearity between features
        # For numeric features, find pairs with |r| > 0.8
        numeric_usable = [c for c in usable_cols if classifications[c]["strategy"] == "numeric"]
        multicollinearity = []
        collinear_drop = set()

        if len(numeric_usable) >= 2:
            num_df = self.df[numeric_usable].loc[y.index]
            corr_matrix = num_df.corr()
            for i, c1 in enumerate(numeric_usable):
                for j, c2 in enumerate(numeric_usable):
                    if i < j:
                        r = corr_matrix.loc[c1, c2]
                        if not np.isnan(r) and abs(r) > 0.80:
                            # Keep the one with higher correlation to target
                            abs_corr_c1 = abs(correlations.get(c1, 0))
                            abs_corr_c2 = abs(correlations.get(c2, 0))
                            keep = c1 if abs_corr_c1 >= abs_corr_c2 else c2
                            drop = c2 if keep == c1 else c1
                            collinear_drop.add(drop)
                            multicollinearity.append({
                                "feature_a": c1,
                                "feature_b": c2,
                                "correlation": round(float(r), 3),
                                "recommendation": f"Keep '{keep}' (|r|={round(max(abs_corr_c1, abs_corr_c2), 3)} with target), drop '{drop}'"
                            })

        # Step 7: Combined scoring
        # Weight: 40% RF importance, 30% mutual information, 30% |correlation|
        rf_max = max(rf_by_feature.values()) if rf_by_feature else 1
        combined_scores = {}
        for col in usable_cols:
            rf_norm = (rf_by_feature.get(col, 0) / rf_max) if rf_max > 0 else 0
            mi_norm = mi_by_feature.get(col, 0)
            corr_norm = abs(correlations.get(col, 0))  # 0 for categoricals

            # For categorical features, boost MI weight since correlation doesn't apply
            if classifications[col]["strategy"] != "numeric":
                score = 0.5 * rf_norm + 0.5 * mi_norm
            else:
                score = 0.4 * rf_norm + 0.3 * mi_norm + 0.3 * corr_norm

            combined_scores[col] = round(score, 4)

        # Sort by combined score
        sorted_features = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

        total_score = sum(s for _, s in sorted_features)
        cumulative = 0
        feature_ranking = []
        for feat, score in sorted_features:
            cumulative += score
            pct = (score / total_score * 100) if total_score > 0 else 0
            cum_pct = (cumulative / total_score * 100) if total_score > 0 else 0
            cls = classifications[feat]

            feature_ranking.append({
                "feature": feat,
                "combined_score": score,
                "importance_pct": round(pct, 1),
                "cumulative_pct": round(cum_pct, 1),
                "correlation": correlations.get(feat, None),
                "mutual_info": mi_by_feature.get(feat, None),
                "rf_importance": round(rf_by_feature.get(feat, 0), 4),
                "encoding": cls["strategy"],
                "detected_type": cls["detected_type"],
                "recommendation": cls["reason"],
                "is_collinear": feat in collinear_drop
            })

        # Recommend features: top scorers up to 85% cumulative, excluding collinear duplicates
        recommended = []
        for f in feature_ranking:
            if f["is_collinear"]:
                continue
            recommended.append(f["feature"])
            if f["cumulative_pct"] > 85:
                break
        if len(recommended) < 2:
            recommended = [f["feature"] for f in feature_ranking if not f["is_collinear"]][:3]

        return {
            "target": target_col,
            "target_stats": {
                "mean": round(float(y.mean()), 2),
                "std": round(float(y.std()), 2),
                "min": round(float(y.min()), 2),
                "max": round(float(y.max()), 2)
            },
            "feature_ranking": feature_ranking,
            "recommended_features": recommended,
            "dropped_features": dropped_cols,
            "multicollinearity": multicollinearity,
            "total_features_analyzed": len(feature_ranking),
            "total_features_dropped": len(dropped_cols),
            "rows_analyzed": len(X),
            "scoring_method": "Combined: 40% Random Forest + 30% Mutual Information + 30% |Correlation|"
        }

    def train_model(self, target_col: str, feature_cols: list, model_type: str = "auto") -> dict:
        """Train a predictive model"""
        self.target_name = target_col

        X, self.feature_info = self._prepare_features(feature_cols)
        # Only keep features that survived preparation (not dropped)
        self.feature_names = [c for c in feature_cols if c in self.feature_info]
        y = self.df[target_col].dropna()

        valid_idx = y.index.intersection(X.index)
        X = X.loc[valid_idx]
        y = y.loc[valid_idx]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        models_to_test = []
        if model_type == "auto":
            models_to_test = [
                ("random_forest", RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)),
                ("gradient_boosting", GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)),
                ("linear_regression", LinearRegression())
            ]
        elif model_type == "gradient_boosting":
            models_to_test = [("gradient_boosting", GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42))]
        elif model_type == "linear_regression":
            models_to_test = [("linear_regression", LinearRegression())]
        else: # Default or random_forest
            models_to_test = [("random_forest", RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1))]

        best_model = None
        best_stats = None
        best_score = -float('inf')
        winning_type = ""

        # Test each model candidate
        for m_name, m_obj in models_to_test:
            try:
                m_obj.fit(X_train, y_train)
                train_p = m_obj.predict(X_train)
                test_p = m_obj.predict(X_test)
                score = r2_score(y_test, test_p)
                
                if score > best_score:
                    best_score = score
                    best_model = m_obj
                    winning_type = m_name
                    best_stats = {
                        "model_type": m_name,
                        "target": target_col,
                        "features": feature_cols,
                        "n_features": len(feature_cols),
                        "train_samples": len(X_train),
                        "test_samples": len(X_test),
                        "train_r2": round(r2_score(y_train, train_p), 3),
                        "test_r2": round(score, 3),
                        "test_mae": round(mean_absolute_error(y_test, test_p), 2),
                        "test_rmse": round(np.sqrt(mean_squared_error(y_test, test_p)), 2),
                        "target_mean": round(float(y.mean()), 2),
                        "target_std": round(float(y.std()), 2)
                    }
            except:
                continue

        if not best_model:
            raise ValueError("All model candidates failed training. Check data for missing values or non-numeric columns.")

        self.model = best_model
        self.model_stats = best_stats

        form_fields = self._build_form_fields()

        return {
            "success": True,
            "stats": self.model_stats,
            "form_fields": form_fields
        }

    def _prepare_features(self, feature_cols: list) -> tuple:
        """Prepare features for modeling using smart classification and encoding"""
        feature_info = {}
        processed_dfs = []

        for col in feature_cols:
            if col not in self.df.columns:
                continue

            series = self.df[col]
            classification = self._classify_column(col, series)

            if classification["strategy"] == "drop":
                continue

            encoded = self._encode_feature(col, series, classification)
            if encoded.empty:
                continue

            processed_dfs.append(encoded)

            # Build feature_info for prediction form
            info = {"original_name": col}

            if classification["strategy"] == "numeric":
                clean = series.dropna()
                q1, q2, q3 = clean.quantile([0.25, 0.5, 0.75]) if len(clean) > 0 else (0, 0, 0)
                info["type"] = "numeric"
                info["min"] = round(float(clean.min()), 2) if len(clean) > 0 else 0
                info["max"] = round(float(clean.max()), 2) if len(clean) > 0 else 0
                info["mean"] = round(float(clean.mean()), 2) if len(clean) > 0 else 0
                info["median"] = round(float(clean.median()), 2) if len(clean) > 0 else 0
                info["q1"] = round(float(q1), 2)
                info["q3"] = round(float(q3), 2)
                info["suggestions"] = [
                    {"label": "Low (25th percentile)", "value": round(float(q1), 2)},
                    {"label": "Medium (median)", "value": round(float(q2), 2)},
                    {"label": "High (75th percentile)", "value": round(float(q3), 2)}
                ]
            else:
                cats = self.encoders.get(col, series.dropna().unique().tolist()[:10])
                info["type"] = "categorical"
                info["categories"] = [{"label": str(c), "value": str(c)} for c in cats]

            feature_info[col] = info

        if processed_dfs:
            X = pd.concat(processed_dfs, axis=1)
        else:
            X = pd.DataFrame()

        return X, feature_info

    def _build_form_fields(self) -> list:
        """Build form field definitions for the prediction UI"""
        fields = []
        for col in self.feature_names:
            info = self.feature_info.get(col, {})
            field = {
                "name": col,
                "label": col.replace("_", " ").title(),
                "type": info.get("type", "numeric")
            }

            if info.get("type") == "numeric":
                field["input_type"] = "number"
                field["min"] = info.get("min", 0)
                field["max"] = info.get("max", 100)
                field["default"] = info.get("median", info.get("mean", 0))
                field["tooltip"] = f"Range: {info.get('min', '?')} - {info.get('max', '?')}, Typical: {info.get('median', '?')}"
                field["suggestions"] = info.get("suggestions", [])
            else:
                field["input_type"] = "select"
                field["options"] = info.get("categories", [])
                field["default"] = info.get("categories", [{}])[0].get("value", "")

            fields.append(field)

        return fields

    def predict(self, input_data: dict) -> dict:
        """Make a prediction with the trained model"""
        if self.model is None:
            raise ValueError("Model not trained yet")

        input_row = {}
        for col in self.feature_names:
            info = self.feature_info.get(col, {})
            value = input_data.get(col)

            if info.get("type") == "numeric":
                input_row[col] = float(value) if value is not None else info.get("median", 0)
            else:
                categories = self.encoders.get(col, [])
                for cat in categories:
                    col_name = f"{col}_encoded_{cat}"
                    input_row[col_name] = 1 if str(value) == str(cat) else 0

        X_pred = pd.DataFrame([input_row])

        model_features = self.model.feature_names_in_ if hasattr(self.model, 'feature_names_in_') else []
        for feat in model_features:
            if feat not in X_pred.columns:
                X_pred[feat] = 0
        X_pred = X_pred[model_features]

        prediction = self.model.predict(X_pred)[0]

        margin = self.model_stats.get("test_rmse", 0) * 1.5

        return {
            "prediction": round(float(prediction), 2),
            "lower_bound": round(float(prediction - margin), 2),
            "upper_bound": round(float(prediction + margin), 2),
            "confidence_note": f"+-{round(margin, 2)} based on model error",
            "model_r2": self.model_stats.get("test_r2", 0)
        }

    def export_model(self) -> bytes:
        """Export the trained model as a pickle file"""
        if self.model is None:
            raise ValueError("No model to export")

        export_data = {
            "model": self.model,
            "feature_names": self.feature_names,
            "target_name": self.target_name,
            "encoders": self.encoders,
            "feature_info": self.feature_info,
            "model_stats": self.model_stats
        }

        return pickle.dumps(export_data)


# =============================================================================
# PYDANTIC MODELS
# =============================================================================
class ClassifyRequest(BaseModel):
    filename: str
    column: str
    method: str
    new_name: str
    params: Optional[dict] = {}

class PivotRequest(BaseModel):
    filename: str
    rows: List[str]
    cols: Optional[List[str]] = None
    values: Optional[List[str]] = None
    aggfunc: str = "sum"
    filters: Optional[Dict[str, List]] = None
    weight_col: Optional[str] = None  # For weighted average: sum(weight*value)/sum(weight)

class VizRequest(BaseModel):
    filename: str
    chart_type: str
    x: Optional[str] = None
    y: Optional[str] = None
    color: Optional[str] = None
    column: Optional[str] = None

class FilterValuesRequest(BaseModel):
    filename: str
    column: str

class JoinCensusRequest(BaseModel):
    filename: str
    geography: str  # 'state', 'county', 'zip'
    join_column: str
    geography_format: str = "name" # 'name' or 'fips' (for state/county)



# =============================================================================
# ROUTER
# =============================================================================
router = APIRouter(tags=["Analyst"])

# Session storage
sessions = {}


def get_library():
    """Load the data library from disk"""
    if os.path.exists(LIBRARY_FILE):
        with open(LIBRARY_FILE, "r") as f:
            return json.load(f)
    return {}


def save_library(library):
    """Save the data library to disk"""
    with open(LIBRARY_FILE, "w") as f:
        json.dump(library, f, indent=2)


@router.get("/", response_class=HTMLResponse)
async def smart_analyst_home():
    """Serve the Smart Analyst frontend"""
    from .frontend import HTML_TEMPLATE
    return HTMLResponse(content=HTML_TEMPLATE)


@router.get("/library")
async def get_data_library():
    """Get list of available datasets"""
    library = get_library()

    # Add public datasets
    public_list = []
    for name, info in PUBLIC_DATASETS.items():
        public_list.append({
            "name": name,
            "category": info["category"],
            "description": info["description"],
            "source": "public"
        })

    # Add uploaded datasets
    uploaded_list = []
    for filename, info in library.items():
        uploaded_list.append({
            "name": filename,
            "rows": info.get("rows", 0),
            "cols": info.get("cols", 0),
            "uploaded": info.get("uploaded", ""),
            "source": "uploaded"
        })

    return {
        "public_datasets": public_list,
        "uploaded_datasets": uploaded_list
    }


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV/Excel file"""
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    try:
        content = await file.read()

        quoted_columns = set()
        if ext == '.csv':
            # Detect columns that have quoted numeric values (like zip codes, years)
            quoted_columns = detect_quoted_columns(content)
            # Read CSV with quoted numeric columns as strings
            dtype_overrides = {col: str for col in quoted_columns}
            df = pd.read_csv(io.BytesIO(content), dtype=dtype_overrides if dtype_overrides else None)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(io.BytesIO(content))
        elif ext == '.json':
            df = pd.read_json(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        # Save to uploads directory
        safe_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)

        with open(file_path, 'wb') as f:
            f.write(content)

        # Update library
        library = get_library()
        library[safe_filename] = {
            "original_name": filename,
            "path": file_path,
            "rows": len(df),
            "cols": len(df.columns),
            "uploaded": str(pd.Timestamp.now())
        }
        save_library(library)

        # Profile the data
        profiler = DataProfiler(df)
        profile = profiler.run_full_profile()

        # Store in session
        sessions[safe_filename] = {
            "df": df,
            "profile": profile,
            "classifications": {},
            "pivot_engine": PivotEngine(df),
            "model_engine": None
        }

        return {
            "success": True,
            "filename": safe_filename,
            "profile": profile,
            "preview": clean_for_json(df.head(100).where(df.head(100).notna(), None).to_dict('records'))
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/load-public")
async def load_public(name: str = Form(...)):
    """Load a public dataset"""
    try:
        df = load_public_dataset(name)

        profiler = DataProfiler(df)
        profile = profiler.run_full_profile()

        sessions[name] = {
            "df": df,
            "profile": profile,
            "classifications": {},
            "pivot_engine": PivotEngine(df),
            "model_engine": None
        }

        return {
            "success": True,
            "filename": name,
            "profile": profile,
            "preview": clean_for_json(df.head(100).where(df.head(100).notna(), None).to_dict('records'))
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/saved-datasets")
async def list_saved_datasets():
    """List available saved datasets from db/analyst folder"""
    try:
        datasets = []
        if os.path.exists(SAVED_DATA_DIR):
            # Find all data files (.csv, .txt)
            for filename in os.listdir(SAVED_DATA_DIR):
                base, ext = os.path.splitext(filename)
                if ext.lower() in ('.csv', '.txt', '.xlsx', '.xls'):
                    # Check for corresponding .md file for display name
                    md_file = os.path.join(SAVED_DATA_DIR, base + '.md')
                    if os.path.exists(md_file):
                        with open(md_file, 'r') as f:
                            display_name = f.read().strip()
                    else:
                        display_name = base  # Use filename without extension

                    datasets.append({
                        "filename": filename,
                        "display_name": display_name,
                        "base_name": base
                    })

        return {"datasets": datasets}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/load-saved")
async def load_saved(filename: str = Form(...)):
    """Load a saved dataset from db/analyst folder"""
    try:
        filepath = os.path.join(SAVED_DATA_DIR, filename)

        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"Dataset not found: {filename}")

        # Security check: ensure path is within SAVED_DATA_DIR
        real_path = os.path.realpath(filepath)
        if not real_path.startswith(os.path.realpath(SAVED_DATA_DIR)):
            raise HTTPException(status_code=403, detail="Access denied")

        # Load based on extension
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.csv':
            # Detect quoted numeric columns and keep them as strings
            with open(filepath, 'rb') as f:
                content = f.read()
            quoted_columns = detect_quoted_columns(content)
            dtype_overrides = {col: str for col in quoted_columns}
            df = pd.read_csv(filepath, dtype=dtype_overrides if dtype_overrides else None)
        elif ext == '.txt':
            # Try tab-separated first, then comma
            with open(filepath, 'rb') as f:
                content = f.read()
            quoted_columns = detect_quoted_columns(content)
            dtype_overrides = {col: str for col in quoted_columns}
            try:
                df = pd.read_csv(filepath, sep='\t', dtype=dtype_overrides if dtype_overrides else None)
                if len(df.columns) == 1:
                    df = pd.read_csv(filepath, dtype=dtype_overrides if dtype_overrides else None)
            except:
                df = pd.read_csv(filepath, dtype=dtype_overrides if dtype_overrides else None)
        elif ext in ('.xlsx', '.xls'):
            df = pd.read_excel(filepath)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        # Get display name from .md file if exists
        base = os.path.splitext(filename)[0]
        md_file = os.path.join(SAVED_DATA_DIR, base + '.md')
        if os.path.exists(md_file):
            with open(md_file, 'r') as f:
                display_name = f.read().strip()
        else:
            display_name = base

        profiler = DataProfiler(df)
        profile = profiler.run_full_profile()

        session_name = f"saved_{base}"
        sessions[session_name] = {
            "df": df,
            "profile": profile,
            "classifications": {},
            "pivot_engine": PivotEngine(df),
            "model_engine": None
        }

        # Convert to JSON-safe format - handle NaN, inf, and other non-serializable values
        preview_df = df.head(100).copy()
        for col in preview_df.columns:
            if preview_df[col].dtype in ['float64', 'float32']:
                preview_df[col] = preview_df[col].apply(lambda x: None if pd.isna(x) or np.isinf(x) else x)

        return clean_for_json({
            "success": True,
            "filename": session_name,
            "display_name": display_name,
            "profile": profile,
            "preview": preview_df.where(pd.notnull(preview_df), None).to_dict('records')
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/load-url")
async def load_url(url: str = Form(...)):
    """Load dataset from URL"""
    try:
        df = load_from_url(url)

        name = f"url_{uuid.uuid4().hex[:8]}"

        profiler = DataProfiler(df)
        profile = profiler.run_full_profile()

        sessions[name] = {
            "df": df,
            "profile": profile,
            "classifications": {},
            "pivot_engine": PivotEngine(df),
            "model_engine": None
        }

        return {
            "success": True,
            "filename": name,
            "profile": profile,
            "preview": clean_for_json(df.head(100).where(df.head(100).notna(), None).to_dict('records'))
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/classify")
async def classify_column(request: ClassifyRequest):
    """Create a new classification column"""
    if request.filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[request.filename]
    df = session["df"]

    if request.column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{request.column}' not found")

    series = df[request.column]

    try:
        if request.method == "quintiles":
            result = ColumnClassifier.quintiles(series)
        elif request.method == "quartiles":
            result = ColumnClassifier.quartiles(series)
        elif request.method == "deciles":
            result = ColumnClassifier.deciles(series)
        elif request.method == "statistical":
            result = ColumnClassifier.statistical_class(series)
        elif request.method == "kmeans":
            n_clusters = request.params.get("n_clusters", 4)
            numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            result = ColumnClassifier.kmeans_cluster(df, numeric_cols, n_clusters)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {request.method}")

        session["classifications"][request.new_name] = result
        session["pivot_engine"].add_classification(request.new_name, result)

        # Get distribution of the new classification
        dist = result.value_counts().to_dict()

        return {
            "success": True,
            "name": request.new_name,
            "distribution": {str(k): int(v) for k, v in dist.items()}
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pivot")
async def create_pivot(request: PivotRequest):
    """Create a pivot table"""
    if request.filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[request.filename]
    pivot_engine = session["pivot_engine"]

    result = pivot_engine.create_pivot(
        rows=request.rows,
        cols=request.cols,
        values=request.values,
        aggfunc=request.aggfunc,
        filters=request.filters,
        weight_col=request.weight_col
    )

    return result


@router.post("/visualize")
async def create_visualization(request: VizRequest):
    """Create a visualization"""
    if request.filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[request.filename]
    df = session["df"]

    try:
        if request.chart_type == "correlation":
            image = VizEngine.correlation_heatmap(df)
            return {"success": True, "image": image}
        elif request.chart_type == "distribution":
            if not request.column:
                raise HTTPException(status_code=400, detail="Column required for distribution plot")
            image = VizEngine.distribution_plot(df[request.column], request.column)
            return {"success": True, "image": image}
        elif request.chart_type == "scatter":
            if not request.x or not request.y:
                raise HTTPException(status_code=400, detail="X and Y columns required for scatter plot")
            image = VizEngine.scatter_plot(df, request.x, request.y, request.color)
            return {"success": True, "image": image}
        elif request.chart_type == "bar":
            if not request.x or not request.y:
                raise HTTPException(status_code=400, detail="X and Y columns required for bar chart")
            image = VizEngine.bar_chart(df, request.x, request.y)
            return {"success": True, "image": image}
        elif request.chart_type == "cluster":
            if not request.x or not request.y or not request.color:
                raise HTTPException(status_code=400, detail="X, Y, and color (cluster) columns required")
            work_df = df.copy()
            for name, series in session["classifications"].items():
                work_df[name] = series
            image = VizEngine.cluster_plot(work_df, request.x, request.y, request.color)
            return {"success": True, "image": image}
        elif request.chart_type == "map":
            # For map, we return raw data for Plotly.js to render
            has_coords = 'geo.latitude' in df.columns and 'geo.longitude' in df.columns
            work_df = df.copy()
            for name, series in session["classifications"].items():
                work_df[name] = series
            
            sample_size = min(len(work_df), 10000)
            map_data = work_df.sample(sample_size).to_dict('records')
            
            return {
                "success": True, 
                "map_data": map_data, 
                "has_coords": has_coords,
                "row_count": len(work_df)
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown chart type: {request.chart_type}")

        return {"success": True, "image": image}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/apply-filter")
async def apply_filter(filename: str = Form(...), column: str = Form(...), values: str = Form(...)):
    """Filter the session dataset in-place. values is a JSON array of allowed values."""
    if filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[filename]
    df = session["df"]

    if column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{column}' not found")

    try:
        allowed = json.loads(values)
    except Exception:
        raise HTTPException(status_code=400, detail="values must be a JSON array")

    # Store original df for reset
    if "original_df" not in session:
        session["original_df"] = df.copy()

    # Cast allowed values to match column dtype
    series = df[column]
    if pd.api.types.is_numeric_dtype(series):
        allowed_typed = []
        for v in allowed:
            try:
                allowed_typed.append(float(v))
            except (ValueError, TypeError):
                allowed_typed.append(v)
        filtered = df[df[column].isin(allowed_typed)]
    else:
        filtered = df[df[column].astype(str).isin([str(v) for v in allowed])]

    if len(filtered) == 0:
        raise HTTPException(status_code=400, detail="Filter removed all rows")

    session["df"] = filtered
    session["model_engine"] = None

    # Re-profile
    profiler = DataProfiler(filtered)
    profile = profiler.run_full_profile()
    session["profile"] = profile
    session["pivot_engine"] = PivotEngine(filtered)

    return {
        "success": True,
        "rows_before": len(df),
        "rows_after": len(filtered),
        "profile": profile,
        "preview": filtered.head(100).to_dict('records')
    }


@router.post("/reset-filter")
async def reset_filter(filename: str = Form(...)):
    """Reset dataset to original (unfiltered) state."""
    if filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[filename]
    if "original_df" not in session:
        return {"success": True, "message": "No filter to reset"}

    df = session["original_df"]
    session["df"] = df
    del session["original_df"]
    session["model_engine"] = None

    profiler = DataProfiler(df)
    profile = profiler.run_full_profile()
    session["profile"] = profile
    session["pivot_engine"] = PivotEngine(df)

    return {
        "success": True,
        "rows_after": len(df),
        "profile": profile,
        "preview": df.head(100).to_dict('records')
    }


@router.post("/filter-values")
async def get_filter_values(request: FilterValuesRequest):
    """Get unique values for a column (for filters)"""
    if request.filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[request.filename]
    df = session["df"]

    # Include classifications
    work_df = df.copy()
    for name, series in session["classifications"].items():
        work_df[name] = series

    if request.column not in work_df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{request.column}' not found")

    values = work_df[request.column].dropna().unique().tolist()
    values = [str(v) for v in sorted(values)[:100]]  # Limit to 100 values

    return {"values": values}


@router.get("/columns/{filename}")
async def get_columns(filename: str):
    """Get column information for a dataset"""
    if filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[filename]
    profile = session["profile"]
    classifications = list(session["classifications"].keys())

    return {
        "columns": profile["columns"],
        "classifications": classifications
    }


@router.post("/analyze-features")
async def analyze_features(filename: str = Form(...), target: str = Form(...)):
    """Analyze feature importance for a target variable"""
    if filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[filename]
    df = session["df"]

    try:
        model_engine = ModelEngine(df)
        result = model_engine.analyze_features(target)
        session["model_engine"] = model_engine
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/train-model")
async def train_model(
    filename: str = Form(...),
    target: str = Form(...),
    features: str = Form(...),
    model_type: str = Form("random_forest")
):
    """Train a predictive model"""
    if filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[filename]
    df = session["df"]

    feature_list = [f.strip() for f in features.split(",")]

    try:
        model_engine = ModelEngine(df)
        result = model_engine.train_model(target, feature_list, model_type)
        session["model_engine"] = model_engine
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/predict")
async def make_prediction(filename: str = Form(...), input_data: str = Form(...)):
    """Make a prediction using the trained model"""
    if filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[filename]
    model_engine = session.get("model_engine")

    if not model_engine or not model_engine.model:
        raise HTTPException(status_code=400, detail="No trained model available")

    try:
        data = json.loads(input_data)
        result = model_engine.predict(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/model-summary")
async def get_model_summary(filename: str = Form(...)):
    """Generate an AI executive summary for the trained model"""
    if filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[filename]
    model_engine = session.get("model_engine")

    if not model_engine or not model_engine.model_stats:
        raise HTTPException(status_code=400, detail="No trained model available")

    stats = model_engine.model_stats

    # Build prompt for LLM
    rows, cols = session["df"].shape
    insights = [i["detail"] for i in session["profile"].get("insights", [])[:3]]
    
    prompt = f"""Write a professional but plain-English executive summary for a predictive model within a data analytical dashboard.
    The goal is to explain the datasheet contents and the model's value to a stakeholder, avoiding heavy statistical jargon.

    DATASHEET CONTEXT:
    - Data Source: {filename}
    - Size: {rows} records and {cols} columns.
    - Key Observations found in data: {'; '.join(insights) if insights else 'General patterns observed across features.'}

    PREDICTIVE MODEL DETAILS:
    - We are predicting: {stats['target']}
    - Using these data points: {', '.join(stats['features'])}
    - Model Accuracy (R-squared): {stats['test_r2']} (Scale: 0 to 1, where 1 means it matches perfectly)
    - Average Margin of Error (MAE): {stats['test_mae']}
    - General Data Context: The value being predicted typically ranges around {stats['target_mean']} (Avg) with a standard deviation of {stats['target_std']}.

    PLEASE PROVIDE IN COMPACT PARAGRAPHS:
    1. A section on \"Datasheet Overview\": Explain what kind of data is here and what it tells us about the subject based on the features we used.
    2. A section on \"Model Performance\": Briefly explain the accuracy and error in real-world terms (e.g., \"the model is usually within X of the actual value\"). 
    3. A \"Bottom Line\": Is this model reliable enough for business decisions?

    Keep it concise (2-3 short paragraphs). Do NOT use technical jargon like \"RMSE\", \"z-score\", or \"heteroscedasticity\". Use business-friendly terms like \"accuracy\", \"margin of error\", and \"prediction quality\".
    """

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 512
            }
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        if response.status_code != 200:
            return {"summary": "Could not generate AI summary at this time (Ollama error)."}

        data = response.json()
        summary = data.get("response", "No summary generated.")

        return {"summary": summary}

    except Exception as e:
        return {"summary": f"Could not generate AI summary: {str(e)}"}


@router.post("/join-census")
async def join_census_data(req: JoinCensusRequest):
    """Join the current dataset with comprehensive Census Bureau demographics"""
    if req.filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[req.filename]
    df = session["df"].copy()

    try:
        # 1. Fetch comprehensive census data for the specified geography
        print(f"Fetching Census data for {req.geography}...")
        census_df = fetch_census_comprehensive(req.geography)
        
        # 2. Prepare join keys
        # Census API returns:
        # - 'state' (FIPS)
        # - 'county' (FIPS)
        # - 'zip code tabulation area' (5-digit)
        # - 'NAME' (Human readable name)
        
        census_join_col = None
        if req.geography == "zip":
            census_join_col = "zip code tabulation area"
        elif req.geography == "state":
            if req.geography_format == "fips":
                census_join_col = "state"
            else:
                census_join_col = "NAME"
        elif req.geography == "county":
            if req.geography_format == "fips":
                # Create 5-digit FIPS column in census_df if joining on county FIPS
                census_df["fips_full"] = census_df["state"].str.zfill(2) + census_df["county"].str.zfill(3)
                census_join_col = "fips_full"
            else:
                census_join_col = "NAME"

        if not census_join_col:
            raise ValueError(f"Unsupported geography or format for join: {req.geography}")

        # 3. Clean up user join column (ensure string for zip/fips/names)
        if req.geography == "zip" or req.geography_format == "fips":
             def clean_geo_code(val, geo_type):
                 if pd.isna(val) or val is None: return "nan"
                 s = str(val).split('.')[0].strip() # Remove decimal part
                 if s.lower() in ['nan', 'none', '']: return "nan"
                 
                 if geo_type == "zip":
                     # Handle ZIP+4 (49087-1158) or standard zip
                     s_zip = s.split('-')[0]
                     return s_zip.zfill(5)
                 if geo_type == "state": return s.zfill(2)
                 if geo_type == "county": return s.zfill(5)
                 return s

             df[req.join_column] = df[req.join_column].apply(lambda x: clean_geo_code(x, req.geography))
             # census_df columns are already clean strings from API, but ensure match
             if census_join_col in census_df.columns:
                census_df[census_join_col] = census_df[census_join_col].astype(str)
        
        elif req.geography_format == "name":
            # Normalize names for better matching
            state_abbrs = {
                'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
                'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
                'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
                'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
                'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
                'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
                'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
                'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
                'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
                'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
                'DC': 'District of Columbia', 'PR': 'Puerto Rico'
            }
            
            def normalize_name(name):
                if not name or pd.isna(name): return "nan"
                s = str(name).strip().upper()
                # Handle state abbreviations
                if req.geography == "state" and s in state_abbrs:
                    return state_abbrs[s].lower()
                return s.lower()
            
            df[req.join_column] = df[req.join_column].apply(normalize_name)
            census_df[census_join_col] = census_df[census_join_col].apply(normalize_name)

        # 4. Perform the join (Outer Join as requested)
        print(f"Joining on {req.join_column} == {census_join_col}...")
        
        # Track match success
        initial_rows = len(df)
        merged_df = pd.merge(df, census_df, left_on=req.join_column, right_on=census_join_col, how="outer")
        
        # Check how many rows actually matched (columns from census_df that are not null)
        # Pick one representative column from census_df that isn't the join key
        census_cols = [c for c in census_df.columns if c != census_join_col]
        if census_cols:
            matches = merged_df[census_cols[0]].notna().sum()
            match_pct = round(matches / initial_rows * 100, 1)
        else:
            matches = 0
            match_pct = 0

        # 5. Clean up duplicate columns if any
        if census_join_col != req.join_column and census_join_col in merged_df.columns:
            merged_df.drop(columns=[census_join_col], inplace=True)

        # 6. Update session with merged data
        session["df"] = merged_df
        profiler = DataProfiler(merged_df)
        session["profile"] = profiler.run_full_profile()
        session["pivot_engine"] = PivotEngine(merged_df)
        
        msg = f"Successfully joined with Census {req.geography} demographics. "
        msg += f"Matched {matches} of {initial_rows} rows ({match_pct}% success). "
        msg += f"Added {len(census_df.columns)-1} data points."

        return {
            "success": True,
            "filename": req.filename,
            "message": msg,
            "profile": session["profile"],
            "preview": merged_df.head(100).replace({np.nan: None}).to_dict('records')
        }

    except Exception as e:
        print(f"Join error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export/{filename}")

async def export_data(filename: str, format: str = "csv"):
    """Export the current dataset"""
    if filename not in sessions:
        raise HTTPException(status_code=404, detail="Dataset not found in session")

    session = sessions[filename]
    df = session["df"].copy()

    # Add classifications
    for name, series in session["classifications"].items():
        df[name] = series

    if format == "csv":
        output = df.to_csv(index=False)
        return JSONResponse(content={"data": output, "filename": f"{filename}.csv"})
    elif format == "json":
        output = df.to_json(orient="records")
        return JSONResponse(content={"data": output, "filename": f"{filename}.json"})
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
