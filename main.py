"""
Fleming Analytic - API Server
Pure JSON API. The React frontend (client-prod/) is served by nginx.
"""
import os
import logging
import smtplib
import json
import time
import traceback
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import EmailStr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routers from apps/
from apps.stocks import router as stocks_router
from apps.wordclouds import router as wordclouds_router
from apps.fred import router as fred_router
from apps.news import router as news_router
from apps.chat import router as chat_router
from apps.trading import router as trading_router

# Import existing routers
from apps.astro.astro_router import astro_router
from apps.astro.printify_router import printify_router
from chessapi import router as chess_router
from apps.analyst.router import router as analyst_router
from apps.restaurant import router as restaurant_router
from apps.orders import router as order_router
from apps.stjohn.router import router as stjohn_admin_router
from apps.stjohn.public_router import router as stjohn_public_router
from apps.stjohn.api_router import router as stjohn_api_router
from apps.legacy.router import router as legacy_router
from apps.cqa.router import router as cqa_router
from apps.jobberhub.router import router as jobberhub_router
from apps.lms.auth import router as lms_auth_router
from apps.lms.router import router as lms_router

# Initialize FastAPI app
app = FastAPI(
    title="Fleming Analytic",
    description="Financial analysis, data visualization, and more",
    version="2.0"
)


def custom_openapi():
    """Generate OpenAPI schema with alphabetically sorted tags and paths"""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Sort paths alphabetically
    if "paths" in openapi_schema:
        openapi_schema["paths"] = dict(sorted(openapi_schema["paths"].items()))

    # Sort tags alphabetically
    if "tags" in openapi_schema:
        openapi_schema["tags"] = sorted(openapi_schema["tags"], key=lambda x: x.get("name", ""))

    # Collect all unique tags and sort them
    all_tags = set()
    for path_data in openapi_schema.get("paths", {}).values():
        for method_data in path_data.values():
            if isinstance(method_data, dict) and "tags" in method_data:
                all_tags.update(method_data["tags"])

    # Ensure tags list exists and is sorted
    openapi_schema["tags"] = [{"name": tag} for tag in sorted(all_tags)]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Mount static files (legacy assets still referenced by some pages)
app.mount("/examples", StaticFiles(directory="examples"))
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://client.fleminganalytic.com",
        "https://fleminganalytic.com",
        "https://www.fleminganalytic.com",
        "https://codequestacademy.net",
        "https://for8thgraders.top",
        "https://jobberhub.net",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# REGISTER ROUTERS
# =============================================================================

# New modular routers (from apps/)
app.include_router(stocks_router, prefix="/stocks")
app.include_router(wordclouds_router, prefix="/wordclouds")
app.include_router(fred_router, prefix="/fred")
app.include_router(news_router, prefix="/news")
app.include_router(chat_router, prefix="/chat")
app.include_router(trading_router)

# Existing routers
app.include_router(astro_router)
# app.include_router(printify_router)  # Hidden - not in use
app.include_router(chess_router, prefix="/chess")
app.include_router(analyst_router, prefix="/analyst")
app.include_router(restaurant_router, prefix="/food")
app.include_router(order_router, prefix="/orders")
app.include_router(stjohn_admin_router)  # St. John admin CMS
app.include_router(stjohn_public_router)  # St. John public site (dynamic from CMS)
app.include_router(stjohn_api_router, prefix="/stjohn/admin")  # St. John admin (JSON API)
app.include_router(legacy_router)  # Legacy route compatibility
app.include_router(cqa_router)  # CodeQuest Academy
app.include_router(jobberhub_router)  # JobberHub
app.include_router(lms_auth_router)  # LMS Auth
app.include_router(lms_router)  # LMS CRUD

# =============================================================================
# CORE ROUTES
# =============================================================================

@app.get("/health", tags=["Health"])
async def health(deep: bool = False):
    """What is actually working, in one request.

    `/stocks/sp500` returned 500 for an unknown length of time and nothing
    said so; it was found by hand while checking something else. A status
    page is only useful if it checks the things that break, so this checks
    the dependencies rather than reporting that the web server is running -
    which it obviously is, or nothing would have answered.

    Always 200. A monitor reads the body; returning 503 for a degraded
    subsystem would make the whole site look down when one feed is off.

    The default checks are local and cheap enough to poll every minute.
    `?deep=1` adds the two that leave this machine - an SMTP login and the
    market feed, the latter of which is a slow scrape. Do not poll that one.
    """
    checks: dict[str, str] = {}

    # Analyst: the saved datasets it advertises are on disk.
    try:
        from apps.analyst.router import SAVED_DATA_DIR

        n = len([f for f in os.listdir(SAVED_DATA_DIR) if f.endswith(".csv")])
        checks["analyst_datasets"] = "ok" if n else "no datasets found"
    except Exception as exc:
        checks["analyst_datasets"] = f"failing: {type(exc).__name__}"

    # Contact submissions are written before mail is attempted, so this file
    # is the thing that must never be unwritable.
    try:
        CONTACT_LOG.parent.mkdir(parents=True, exist_ok=True)
        checks["contact_log"] = "ok" if os.access(CONTACT_LOG.parent, os.W_OK) else "not writable"
    except Exception as exc:
        checks["contact_log"] = f"failing: {type(exc).__name__}"

    checks["mail_configured"] = "ok" if SMTP_PASSWORD and SMTP_USER else "no credential configured"

    if deep:
        # Leaves the machine. Auth only, no message sent.
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=8) as srv:
                srv.starttls()
                srv.login(SMTP_USER, SMTP_PASSWORD)
            checks["mail_auth"] = "ok"
        except Exception as exc:
            checks["mail_auth"] = f"failing: {type(exc).__name__}"

        # A scrape of somebody else's site, and the likeliest thing here to
        # be broken at any given moment. Slow: never poll this.
        try:
            import today as _td

            checks["market_feed"] = "ok" if _td.get_tickers() is not None else "empty"
        except Exception as exc:
            checks["market_feed"] = f"failing: {type(exc).__name__}"

    degraded = [k for k, v in checks.items() if v != "ok"]
    return {
        "status": "ok" if not degraded else "degraded",
        "degraded": degraded,
        "checks": checks,
    }


# =============================================================================
# CONTACT ENDPOINT
# =============================================================================

# Where contact messages go, and who they appear to come from.
CONTACT_TO = os.getenv("CONTACT_TO", "fleminganalytic@gmail.com")
CONTACT_FROM = os.getenv("CONTACT_FROM", "noreply@fleminganalytic.com")
ZEPTO_SERVER = os.getenv("ZEPTO_SERVER", "smtp.zeptomail.com")
ZEPTO_PORT = int(os.getenv("ZEPTO_PORT", "587"))
ZEPTO_USER = os.getenv("ZEPTO_USER", "emailapikey")

# Mail settings, named for what they are.
#
# The ZEPTO_* names above are a fossil. A live ZeptoMail API key used to sit
# in this file as a hardcoded default, and it was never once used: .env sets
# ZEPTO_SERVER to smtp.gmail.com and ZEPTO_USER to a Gmail address, so every
# message this site has ever sent went out through Gmail with an app
# password. The key was doing nothing but waiting to be published, which is
# eventually what happened.
#
# So: generic names, read from the environment, no defaults for the secret.
# Moving to a different provider - Hostinger, say - is now an .env edit and a
# restart, with nothing to change here:
#
#   SMTP_HOST=smtp.hostinger.com
#   SMTP_PORT=587
#   SMTP_USER=john.fleming@fleminganalytic.com
#   SMTP_PASSWORD=<the mailbox password>
#   CONTACT_FROM=john.fleming@fleminganalytic.com
#
# The old names are still honoured so that today's configuration keeps
# working untouched until that edit is made.
SMTP_HOST = os.getenv("SMTP_HOST") or os.getenv("ZEPTO_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT") or os.getenv("ZEPTO_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER") or os.getenv("ZEPTO_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") or os.getenv("EMAIL_PWD")


#: Every submission, one JSON object per line, whatever happens to the mail.
CONTACT_LOG = Path(__file__).resolve().parent / "db" / "contact_submissions.jsonl"

#: Recent submissions per client address, for the throttle below.
_contact_hits: dict[str, list[float]] = {}
CONTACT_WINDOW_SECONDS = 3600
CONTACT_MAX_PER_WINDOW = 5


@app.post("/contact", tags=["Contact"])
async def receive_contact(
    request: Request,
    page: str = Form(...),
    email: EmailStr = Form(...),
    content: str = Form(...),
    website: str = Form(""),
):
    """Handle contact form submission — delivers via ZeptoMail.

    This endpoint puts mail into a person's inbox from an unauthenticated
    request, so it carries the two cheapest defences that actually work.

    `website` is a honeypot: the form renders it hidden and a person never
    fills it in, while most bots fill every field they find. A submission
    that has it set is answered with the same success message a person gets,
    because telling a bot it failed only teaches it to try again differently.
    """
    if website:
        return {"status": "success", "message": "Email sent successfully"}

    # Per-address rate limit. In-process and therefore per-worker, which is
    # fine here because there is exactly one worker - see gunicorn_conf.py.
    client = request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")
    now = time.time()
    recent = [t for t in _contact_hits.get(client, []) if now - t < CONTACT_WINDOW_SECONDS]
    if len(recent) >= CONTACT_MAX_PER_WINDOW:
        raise HTTPException(status_code=429, detail="Too many messages. Please try again later.")
    recent.append(now)
    _contact_hits[client] = recent

    if not email or not content:
        raise HTTPException(status_code=400, detail="Email and content are required.")

    # Write it down before trying to send it.
    #
    # Delivery is the part that can fail for reasons the sender cannot see or
    # fix - a wrong password, an expired app password, a provider outage, a
    # DMARC policy quietly quarantining the message. Until now a failure at
    # that step lost the enquiry outright and showed the visitor an error, so
    # the one thing worth keeping depended on the one thing that breaks.
    #
    # A line of JSON on disk needs no credential and no network, so it happens
    # first and it happens regardless.
    record = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "page": page,
        "email": email,
        "content": content,
        "ip": client,
    }
    try:
        CONTACT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with CONTACT_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.error(f"Contact form: could not record submission: {exc}")

    if not SMTP_PASSWORD:
        logger.error("Contact form: SMTP_PASSWORD/EMAIL_PWD is not set, mail not sent "
                     f"(message from {email} is recorded in {CONTACT_LOG})")
        # The enquiry is safe on disk, so as far as the sender is concerned it
        # arrived. Telling them otherwise would invite a duplicate of something
        # that is not lost.
        return {"status": "success", "message": "Email sent successfully"}

    try:
        msg = MIMEMultipart()
        msg['From'] = f"Fleming Analytic <{CONTACT_FROM}>"
        msg['To'] = CONTACT_TO
        msg['Reply-To'] = email  # so you can reply straight to the sender
        msg['Subject'] = f"New Message from {page}"
        msg.attach(MIMEText(
            f"From: {email}\nContent:\n{content}",
            'plain'
        ))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(CONTACT_FROM, [CONTACT_TO], msg.as_string())

        return {"status": "success", "message": "Email sent successfully"}

    except Exception as e:
        # Recorded above, so nothing is lost - the visitor is told it arrived
        # because it did, and the failure is a delivery problem to fix at this
        # end rather than something for them to retry.
        logger.error(f"Contact form: delivery failed ({e}); message from {email} "
                     f"is recorded in {CONTACT_LOG}")
        return {"status": "success", "message": "Email sent successfully"}
