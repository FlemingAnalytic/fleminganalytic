
"""
Fleming Analytic - St. John Dedicated Application
Runs on port 8001 to serve St. John site at root.
"""
import logging
from sqlalchemy.orm import Session
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routers & models
from apps.stjohn.router import router as stjohn_admin_router
from apps.stjohn.public_router import router as stjohn_public_router
from apps.stjohn.public_router import home, page
from apps.stjohn.models import get_db

app = FastAPI(
    title="St. John Lutheran Church",
    description="CMS and Public Site for St. John Lutheran Church",
    version="1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# 1. Admin Router (keeps /stjohn/admin prefix)
app.include_router(stjohn_admin_router)

# 2. Public Router (keeps /stjohn prefix for backward compatibility)
app.include_router(stjohn_public_router)

# 3. Root Router (for stjohn.fleminganalytic.com/)
@app.get("/", response_class=HTMLResponse)
async def root_home(request: Request, db: Session = Depends(get_db)):
    return await home(request, db)

@app.get("/manual")
async def get_manual():
    return RedirectResponse(url="/static/stjohn/St_John_CMS_Manual.pptx")

@app.get("/{slug}", response_class=HTMLResponse)
async def root_page(request: Request, slug: str, db: Session = Depends(get_db)):
    # Avoid conflict with reserved paths
    reserved = ["stjohn", "static", "favicon.ico", "docs", "openapi.json", "manual"]
    if slug in reserved:
        # If execution reaches here for reserved words, likely handled by other routes
        # But if not, we should return 404 or pass
        return HTMLResponse("Not Found", status_code=404)
        
    return await page(request, slug, db)
