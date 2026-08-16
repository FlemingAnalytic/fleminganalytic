from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, FileResponse
import os
import json
import logging
import httpx
import pandas as pd
import datetime
import glob

# Import actual logic if possible (these should have been in the server folder)
try:
    import today as td
    import swing
except ImportError:
    # If they are not in the path yet, we need to ensure the CWD is correct
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import today as td
    import swing

router = APIRouter(tags=["Legacy Compatibility"])
logger = logging.getLogger(__name__)

# Configurable paths
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "db")
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static")

@router.get("/getsp500")
async def legacy_getsp500():
    return td.get_tickers()

@router.get("/plot_pie")
async def legacy_plot_pie():
    return td.plot_pie()

@router.get("/ytd")
async def legacy_ytd():
    return td.ytd()

@router.get("/ef/gettoday/")
async def legacy_ef_today():
    return td.gettoday()

@router.get("/ef/getytd/{tickers}")
async def legacy_ef_ytd(tickers: str):
    ticks = tickers.strip().split(',')
    a = []
    b = []
    for i in range(len(ticks)):
        k, v = ticks[i].split(':')
        a.append(k.strip())
        b.append(float(v.strip()))
    return swing.get_ytd(a, b)

@router.get("/swing/status/{tick}")
async def legacy_swing_status(tick: str):
    return swing.analyze(tick)

@router.get("/biblewordclouds/{testament}")
async def legacy_bible_testament(testament: str):
    csv_path = os.path.join(DB_DIR, 'wordcloud.csv')
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Wordcloud data not found")
    df = pd.read_csv(csv_path)
    df = df[df['testament'] == testament.lower()]
    df.sort_values(by='book', ascending=True, inplace=True)
    return json.loads(df.to_json(orient='records'))

@router.get("/shakespearewordclouds")
async def legacy_shakespeare():
    csv_path = os.path.join(DB_DIR, 'shakespeare.csv')
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Shakespeare data not found")
    df = pd.read_csv(csv_path)
    return json.loads(df.to_json(orient='records'))

@router.get('/news/dates')
async def legacy_news_dates():
    try:
        archive_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "news", "archives", "daily_archive_*.json")
        archive_files = glob.glob(archive_path)
        dates = []
        for file_path in archive_files:
            filename = os.path.basename(file_path)
            if filename.startswith('daily_archive_') and filename.endswith('.json'):
                date_part = filename[14:-5]
                try:
                    datetime.datetime.strptime(date_part, '%Y-%m-%d')
                    dates.append(date_part)
                except ValueError:
                    continue
        dates.sort(reverse=True)
        return dates[:20]
    except Exception as e:
        logger.error(f"Error getting news dates: {e}")
        return []
