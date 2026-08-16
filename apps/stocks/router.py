"""
Stocks & Trading API Router
Endpoints for stock analysis, swing trading, and efficient frontier calculations.
"""
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

import today as td
import swing

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Stocks"])
templates = Jinja2Templates(directory="templates")


# S&P 500 Routes
@router.get("/sp500", tags=["Get best of S & P 500, takes quite a while.."])
async def getsp500():
    """Ranked S&P 500 tickers, or an honest 503 when the upstream is down.

    This reads prices from Yahoo through yfinance, which is an unauthenticated
    scrape of somebody else's website and fails accordingly: it currently
    returns a JSONDecodeError for SPY, leaving an empty frame that the ranking
    code then indexes into and dies on. That surfaced as a 500 with a
    traceback, so the page consuming it showed nothing and gave no reason.

    A 503 with a sentence says the same thing usefully - the service is fine,
    its data source is not, and it is worth trying later. Nothing here retries
    or caches; that would be a real fix rather than an honest failure.
    """
    try:
        return td.get_tickers()
    except (IndexError, KeyError, ValueError) as exc:
        # The shapes an empty upstream frame produces downstream.
        logger.warning(f"/stocks/sp500: upstream market data unavailable ({type(exc).__name__}: {exc})")
        raise HTTPException(
            status_code=503,
            detail="Market data is unavailable right now — the upstream price feed "
                   "did not return data. Try again later.",
        )


@router.get("/plot_pie")
async def plot_pie():
    return td.plot_pie()


@router.get("/comps")
async def get_comps():
    return td.comps()


@router.get("/short")
async def get_short():
    return td.lines(1)


@router.get("/details")
async def get_details():
    return td.servit("details")


@router.get("/ytd")
async def get_ytd():
    return td.ytd()


@router.get("/long")
async def get_long():
    return td.lines(5)


@router.get("/list")
async def get_stocks():
    return td.servit("stocks")


# Efficient Frontier Routes
@router.get("/ef/today/", tags=["Get today's stock recommendations"])
async def get_today():
    return td.gettoday()


@router.get("/ef/ly/")
async def get_ly():
    return swing.get_ly()


@router.get("/ef/ytd/{tickers}")
async def get_ytdt(tickers: str):
    ticks = tickers.strip().split(',')
    a = []
    b = []
    for i in range(len(ticks)):
        k, v = ticks[i].split(':')
        a.append(k.strip())
        b.append(float(v.strip()))
    return swing.get_ytd(a, b)


@router.get('/ef', response_class=HTMLResponse)
async def getef(request: Request):
    return templates.TemplateResponse("ef.html", {"request": request})


# Swing Trading Routes
@router.get("/swing/status/{tick}")
async def swing_status(tick: str):
    return swing.analyze(tick)


@router.get("/swing/buys/{tick}")
async def swing_buys_tick(tick: str):
    return swing.get_buys(tick)


@router.get("/swing/buys")
async def swing_buys():
    return swing.buys()


@router.get('/swing', response_class=HTMLResponse)
async def getswing(request: Request):
    return templates.TemplateResponse("swinger.html", {"request": request})

@router.get("/momentum")
async def getmomentum():
    return FileResponse("static/momentum/strategy_report.pdf", media_type="application/pdf")
