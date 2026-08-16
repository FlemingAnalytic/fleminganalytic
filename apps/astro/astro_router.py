from fastapi import APIRouter, HTTPException, status, Request, Query
from fastapi.responses import FileResponse, Response
from pathlib import Path
import uuid
from datetime import datetime
from typing import Optional

# Assuming these will be copied to your project structure
from .models.request_models import ChartRequest, MugImageRequest
from .models.response_models import ChartResponse, MugImageResponse
from .services.chart_generator import ChartGenerator
from .services.interpreter import AstrologyInterpreter
from .services.pdf_generator import PDFGenerator
from .services.wordcloud_generator import WordCloudGenerator
from .services.mug_image_generator import MugImageGenerator

# Create router with prefix
astro_router = APIRouter(prefix="/astro", tags=["astrology"])

# Initialize services (will use parent-level static folder)
chart_generator = ChartGenerator()
interpreter = AstrologyInterpreter()
pdf_generator = PDFGenerator()
wordcloud_generator = WordCloudGenerator()
mug_image_generator = MugImageGenerator()

@astro_router.post("/generate-chart", response_model=ChartResponse)
async def generate_chart(request: ChartRequest, req: Request):
    try:
        chart_id = str(uuid.uuid4())
        
        chart_data = chart_generator.generate_chart(
            name=request.name,
            year=request.year,
            month=request.month,
            day=request.day,
            hour=request.hour,
            minute=request.minute,
            city=request.city,
            country=request.country,
            chart_id=chart_id
        )
        
        interpretation = interpreter.generate_interpretation(chart_data)
        
        # Generate wordcloud
        complete_chart_data = {
            "planets": chart_data["planets"],
            "houses": chart_data["houses"],
            "aspects": interpretation["aspects"],
            "rising_interpretation": interpretation["rising_interpretation"],
            "element_analysis": interpretation["element_analysis"],
            "observations": interpretation["observations"]
        }
        
        wordcloud_filename = wordcloud_generator.generate_wordcloud(complete_chart_data, chart_id)
        
        # Properly detect HTTPS from request headers
        scheme = 'https' if (
            req.headers.get('x-forwarded-proto') == 'https' or
            req.headers.get('x-forwarded-ssl') == 'on' or
            req.headers.get('x-scheme') == 'https' or
            req.url.scheme == 'https'
        ) else 'http'
        
        base_url = f"{scheme}://{req.headers.get('host', req.url.netloc)}"
        chart_url = f"/static/images/{chart_data['svg_filename']}"
        
        response = ChartResponse(
            chart_id=chart_id,
            chart_url=chart_url,
            full_url=f"{base_url}{chart_url}",
            birth_data={
                "name": request.name,
                "date": f"{request.year}-{request.month:02d}-{request.day:02d}",
                "time": f"{request.hour:02d}:{request.minute:02d}",
                "location": f"{request.city}, {request.country}",
                "coordinates": chart_data["coordinates"]
            },
            planets=chart_data["planets"],
            houses=chart_data["houses"],
            aspects=interpretation["aspects"],
            rising_interpretation=interpretation["rising_interpretation"],
            element_analysis=interpretation["element_analysis"],
            observations=interpretation["observations"],
            wordcloud={
                "file_url": f"/static/images/{wordcloud_filename}",
                "full_url": f"{base_url}/static/images/{wordcloud_filename}"
            }
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating chart: {str(e)}"
        )

@astro_router.post("/generate-pdf")
async def generate_pdf(request: ChartRequest, req: Request):
    try:
        chart_id = str(uuid.uuid4())
        
        chart_data = chart_generator.generate_chart(
            name=request.name,
            year=request.year,
            month=request.month,
            day=request.day,
            hour=request.hour,
            minute=request.minute,
            city=request.city,
            country=request.country,
            chart_id=chart_id
        )
        
        interpretation = interpreter.generate_interpretation(chart_data)
        
        # Generate wordcloud
        complete_chart_data = {
            "chart_id": chart_id,
            "planets": chart_data["planets"],
            "houses": chart_data["houses"],
            "aspects": interpretation["aspects"],
            "rising_interpretation": interpretation["rising_interpretation"],
            "element_analysis": interpretation["element_analysis"],
            "observations": interpretation["observations"]
        }
        
        wordcloud_filename = wordcloud_generator.generate_wordcloud(complete_chart_data, chart_id)
        
        # Properly detect HTTPS from request headers
        scheme = 'https' if (
            req.headers.get('x-forwarded-proto') == 'https' or
            req.headers.get('x-forwarded-ssl') == 'on' or
            req.headers.get('x-scheme') == 'https' or
            req.url.scheme == 'https'
        ) else 'http'
        
        base_url = f"{scheme}://{req.headers.get('host', req.url.netloc)}"
        chart_url = f"/static/images/{chart_data['svg_filename']}"
        
        complete_chart_data_with_wordcloud = {
            "chart_id": chart_id,
            "chart_url": chart_url,
            "full_url": f"{base_url}{chart_url}",
            "birth_data": {
                "name": request.name,
                "date": f"{request.year}-{request.month:02d}-{request.day:02d}",
                "time": f"{request.hour:02d}:{request.minute:02d}",
                "location": f"{request.city}, {request.country}",
                "coordinates": chart_data["coordinates"]
            },
            "planets": chart_data["planets"],
            "houses": chart_data["houses"],
            "aspects": interpretation["aspects"],
            "rising_interpretation": interpretation["rising_interpretation"],
            "element_analysis": interpretation["element_analysis"],
            "observations": interpretation["observations"],
            "wordcloud": {
                "file_url": f"/static/images/{wordcloud_filename}"
            }
        }
        
        pdf_filename = pdf_generator.generate_pdf_report(complete_chart_data_with_wordcloud)
        
        pdf_url = f"/static/pdf/{pdf_filename}"
        
        return {
            "success": True,
            "pdf_filename": pdf_filename,
            "pdf_url": pdf_url,
            "full_pdf_url": f"{base_url}{pdf_url}",
            "chart_id": chart_id,
            "wordcloud": {
                "file_url": f"/static/images/{wordcloud_filename}"
            },
            "message": "PDF report generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating PDF: {str(e)}"
        )

@astro_router.get("/")
async def get_astro_interface():
    """Serve the astrological chart interface HTML page"""
    html_path = Path("static/html/astro-chart.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Astrology interface not found"
        )

@astro_router.get("/privacy")
async def get_privacy_policy():
    """Return the privacy policy markdown content"""
    privacy_path = Path(__file__).parent / "static" / "privacy.md"
    if privacy_path.exists():
        with open(privacy_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return Response(content=content, media_type="text/markdown")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Privacy policy not found"
        )


# Hidden endpoint - disabled
# @astro_router.post("/generate-mug-images", response_model=MugImageResponse)
# async def generate_mug_images - removed

# Hidden endpoint - disabled
# @astro_router.post("/generate-mug-chart")
# async def generate_mug_chart_only - removed


# Keep placeholder to avoid breaking anything that might reference the old function
@astro_router.post("/generate-mug-chart", include_in_schema=False)
async def generate_mug_chart_only(request: MugImageRequest, req: Request):
    raise HTTPException(status_code=404, detail="Not found")


@astro_router.post("/generate-mug-wordcloud", include_in_schema=False)
async def generate_mug_wordcloud_only(request: MugImageRequest, req: Request):
    raise HTTPException(status_code=404, detail="Not found")


@astro_router.post("/generate-etsy-mug-set")
async def generate_etsy_mug_set(request: MugImageRequest, req: Request):
    """
    Generate a complete set of 5 mug images for Etsy/Printify

    Creates 5 print-ready PNG images that customers can choose 2 of:
    1. Chart - The natal chart wheel (no aspects panel)
    2. Planets - Planet positions with symbols
    3. Aspects - Major planetary aspects with symbols
    4. Wordcloud - Personalized chart essence keywords
    5. Houses - The 12 houses with meanings and planet placements

    Images are generated at 300 DPI, optimized for Printify:
    - 11oz mug: 2700x1050 pixels (9" x 3.5")
    - 15oz mug: 2700x1140 pixels (9" x 3.8")
    """
    try:
        chart_id = str(uuid.uuid4())

        # Generate the chart
        chart_data = chart_generator.generate_chart(
            name=request.name,
            year=request.year,
            month=request.month,
            day=request.day,
            hour=request.hour,
            minute=request.minute,
            city=request.city,
            country=request.country,
            chart_id=chart_id
        )

        # Get interpretations
        interpretation = interpreter.generate_interpretation(chart_data)

        # Generate wordcloud
        complete_chart_data = {
            "planets": chart_data["planets"],
            "houses": chart_data["houses"],
            "aspects": interpretation["aspects"],
            "rising_interpretation": interpretation["rising_interpretation"],
            "element_analysis": interpretation["element_analysis"],
            "observations": interpretation["observations"]
        }
        wordcloud_filename = wordcloud_generator.generate_wordcloud(complete_chart_data, chart_id)

        # Generate all 4 mug images
        mug_images = mug_image_generator.generate_full_mug_set(
            svg_filename=chart_data['svg_filename'],
            wordcloud_filename=wordcloud_filename,
            planets_data=chart_data["planets"],
            aspects_data=interpretation["aspects"],
            chart_id=chart_id,
            name=request.name,
            mug_size=request.mug_size,
            background_color=request.background_color,
            houses_data=chart_data["houses"]
        )

        # Detect HTTPS
        scheme = 'https' if (
            req.headers.get('x-forwarded-proto') == 'https' or
            req.headers.get('x-forwarded-ssl') == 'on' or
            req.headers.get('x-scheme') == 'https' or
            req.url.scheme == 'https'
        ) else 'http'

        base_url = f"{scheme}://{req.headers.get('host', req.url.netloc)}"

        # Build response with all 4 images
        def build_image_info(filename, description):
            if not filename:
                return None
            url = f"/static/images/{filename}"
            return {
                "filename": filename,
                "url": url,
                "full_url": f"{base_url}{url}",
                "description": description
            }

        return {
            "success": True,
            "chart_id": chart_id,
            "mug_size": request.mug_size,
            "birth_data": {
                "name": request.name,
                "date": f"{request.year}-{request.month:02d}-{request.day:02d}",
                "time": f"{request.hour:02d}:{request.minute:02d}",
                "location": f"{request.city}, {request.country}"
            },
            "images": {
                "chart": build_image_info(
                    mug_images.get('chart_image'),
                    "Natal chart wheel - clean design without aspects panel"
                ),
                "planets": build_image_info(
                    mug_images.get('planets_image'),
                    "Planet positions with astrological symbols"
                ),
                "aspects": build_image_info(
                    mug_images.get('aspects_image'),
                    "Major planetary aspects with colored symbols"
                ),
                "wordcloud": build_image_info(
                    mug_images.get('wordcloud_image'),
                    "Chart essence keywords wordcloud"
                ),
                "houses": build_image_info(
                    mug_images.get('houses_image'),
                    "The 12 houses with life areas and planet placements"
                )
            },
            "print_specs": {
                "format": "PNG",
                "dpi": 300,
                "color_mode": "RGB",
                "dimensions": "2700x1050" if request.mug_size == "11oz" else "2700x1140",
                "compatible_with": ["Printify", "Printful", "CustomInk", "Zazzle"]
            },
            "instructions": "Customer chooses 2 of 5 images for front and back of mug. Download PNGs and upload to Printify."
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating Etsy mug set: {str(e)}"
        )
