"""
FRED API Router
Endpoints for Federal Reserve Economic Data (GDP, Debt, Inflation, etc.)
"""
import logging
import httpx
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from config import settings

router = APIRouter(tags=["FRED Economic Data"])
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

FRED_API_URL = "https://api.stlouisfed.org/fred/series/observations"


@router.get("/data", response_class=JSONResponse)
async def get_fred_data(
    request: Request,
    series_id: str = Query("FYGDP", description="Series ID for the FRED API")
):
    """Fetch data from FRED API for a given series."""
    try:
        logger.info(f"Fetching data from FRED API for series_id: {series_id}...")

        async with httpx.AsyncClient() as client:
            response = await client.get(FRED_API_URL, params={
                "series_id": series_id,
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "observation_start": "1999-01-01"
            })

        logger.info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                return {"observations": data.get("observations", [])}
            except ValueError as json_error:
                logger.error(f"Error parsing JSON: {json_error}")
                return {"error": f"Failed to parse JSON: {str(json_error)}"}
        else:
            logger.error(f"Failed to fetch data. Status code: {response.status_code}")
            return {"error": f"Failed to fetch data. Status code: {response.status_code}"}

    except httpx.RequestError as req_error:
        logger.error(f"Request Error: {req_error}")
        return {"error": f"Request error: {str(req_error)}"}
    except Exception as e:
        logger.error(f"General Exception: {e}")
        return {"error": str(e)}


@router.get("/debt_gdp", response_class=HTMLResponse)
async def get_debt_gdp_page(request: Request):
    return templates.TemplateResponse("debt_gdp.html", {"request": request})


@router.get("/gdp", response_class=HTMLResponse)
async def get_gdp_page(request: Request):
    return templates.TemplateResponse("gdp.html", {"request": request})


@router.get("/debt", response_class=HTMLResponse)
async def get_debt_page(request: Request):
    return templates.TemplateResponse("debt.html", {"request": request})
