"""
Fleming Analytic - API Server
Pure JSON API. The React frontend (client-prod/) is served by nginx.
"""
import os
import logging
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import FastAPI, Form, HTTPException
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

# Contact form delivery via ZeptoMail (transactional email — same service smtpit.py uses)
CONTACT_TO = os.getenv("CONTACT_TO", "fleminganalytic@gmail.com")
CONTACT_FROM = os.getenv("CONTACT_FROM", "noreply@fleminganalytic.com")
ZEPTO_SERVER = os.getenv("ZEPTO_SERVER", "smtp.zeptomail.com")
ZEPTO_PORT = int(os.getenv("ZEPTO_PORT", "587"))
ZEPTO_USER = os.getenv("ZEPTO_USER", "emailapikey")
ZEPTO_PWD = os.getenv("EMAIL_PWD", "REMOVED_SEE_ENV")


@app.post("/contact", tags=["Contact"])
async def receive_contact(
    page: str = Form(...),
    email: EmailStr = Form(...),
    content: str = Form(...)
):
    """Handle contact form submission — delivers via ZeptoMail."""
    if not email or not content:
        raise HTTPException(status_code=400, detail="Email and content are required.")

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

        with smtplib.SMTP(ZEPTO_SERVER, ZEPTO_PORT) as server:
            server.starttls()
            server.login(ZEPTO_USER, ZEPTO_PWD)
            server.sendmail(CONTACT_FROM, [CONTACT_TO], msg.as_string())

        return {"status": "success", "message": "Email sent successfully"}

    except Exception as e:
        logger.error(f"Contact form error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
