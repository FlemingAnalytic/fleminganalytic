"""
Fleming Analytic - API Server
Pure JSON API. The React frontend (client-prod/) is served by nginx.
"""
import os
import logging
import smtplib
import time
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

    if not SMTP_PASSWORD:
        # Say the actual cause in the log, and nothing useful to the caller.
        logger.error("Contact form: SMTP_PASSWORD/EMAIL_PWD is not set, cannot send mail")
        raise HTTPException(status_code=503, detail="Contact is temporarily unavailable.")

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
        logger.error(f"Contact form error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
