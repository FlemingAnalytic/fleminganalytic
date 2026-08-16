"""
News API Router
Endpoints for news analysis dashboard and archives.
"""
import os
import json
import glob
import datetime
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

router = APIRouter(tags=["News"])
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)


@router.get('/', response_class=HTMLResponse)
async def news_dashboard(request: Request):
    """Serve the news analysis dashboard"""
    return templates.TemplateResponse("news.html", {"request": request})


@router.get('/archives', response_class=HTMLResponse)
async def news_archives():
    """Serve the news archives index page"""
    with open("news/archives.html", "r") as f:
        return HTMLResponse(content=f.read())


@router.get('/dates', response_class=JSONResponse)
async def get_news_dates():
    """Get list of available news archive dates (most recent 20)"""
    try:
        archive_pattern = "news/archives/daily_archive_*.json"
        archive_files = glob.glob(archive_pattern)

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
        dates = dates[:20]
        return dates

    except Exception as e:
        logger.error(f"Error getting news dates: {e}")
        return []


@router.get('/date/{date}', response_class=JSONResponse)
async def get_news_data(date: str):
    """Get news data for a specific date"""
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
        file_path = f"news/archives/daily_archive_{date}.json"

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"No data found for date {date}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        response = JSONResponse(content=data)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No data found for date {date}")
    except Exception as e:
        logger.error(f"Error getting news data for {date}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/archives/{filename}", response_class=JSONResponse)
async def get_news_archive_file(filename: str):
    """Serve news archive JSON files directly"""
    try:
        if not filename.startswith("daily_archive_") or not filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="Invalid filename format")

        date_part = filename[14:-5]
        try:
            datetime.datetime.strptime(date_part, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date in filename")

        file_path = f"news/archives/{filename}"

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Archive file not found")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        response = JSONResponse(content=data)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving archive file {filename}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
