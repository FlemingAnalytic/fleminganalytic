from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class ChartResponse(BaseModel):
    """Response model for astrological chart generation"""

    chart_id: str = Field(..., description="Unique identifier for the chart")
    chart_url: str = Field(..., description="URL to access the generated SVG chart")
    full_url: str = Field(..., description="Complete URL to access the generated SVG chart")
    birth_data: Dict[str, Any] = Field(..., description="Birth data used for chart generation")
    planets: Dict[str, Any] = Field(..., description="Planetary positions and data")
    houses: Dict[str, Any] = Field(..., description="House positions and data")
    aspects: List[Dict[str, Any]] = Field(..., description="Astrological aspects analysis")
    rising_interpretation: str = Field(..., description="Rising sign interpretation")
    element_analysis: Dict[str, Any] = Field(..., description="Element analysis (Fire, Earth, Air, Water)")
    observations: List[str] = Field(..., description="General astrological observations")
    wordcloud: Dict[str, str] = Field(..., description="Wordcloud file URL as separate JSON dictionary")

    class Config:
        json_schema_extra = {
            "example": {
                "chart_id": "123e4567-e89b-12d3-a456-426614174000",
                "chart_url": "/static/images/123e4567-e89b-12d3-a456-426614174000.svg",
                "full_url": "https://fleminganalytic.com/static/images/123e4567-e89b-12d3-a456-426614174000.svg",
                "birth_data": {
                    "name": "John Doe",
                    "date": "1990-06-15",
                    "time": "14:30",
                    "location": "New York, USA",
                    "coordinates": {
                        "latitude": 40.7128,
                        "longitude": -74.0060
                    }
                },
                "planets": {},
                "houses": {},
                "aspects": [],
                "rising_interpretation": "Your rising sign interpretation...",
                "element_analysis": {},
                "observations": ["Observation 1", "Observation 2"],
                "wordcloud": {
                    "file_url": "/static/images/wordcloud_abc123.png",
                    "full_url": "https://fleminganalytic.com/static/images/wordcloud_abc123.png"
                }
            }
        }


class MugImageInfo(BaseModel):
    """Information about a generated mug image"""

    filename: str = Field(..., description="Filename of the generated PNG")
    url: str = Field(..., description="Relative URL path to the image")
    full_url: Optional[str] = Field(None, description="Complete URL to access the image")
    description: str = Field(..., description="Description of the image purpose")


class MugImageResponse(BaseModel):
    """Response model for mug image generation

    Contains URLs to download print-ready PNG images for mug printing.
    Images are optimized for Printful/Printify at 300 DPI.
    """

    chart_id: str = Field(..., description="Unique identifier for this chart")
    mug_size: str = Field(..., description="Mug size (11oz or 15oz)")
    chart_image: Optional[Dict[str, Any]] = Field(
        None,
        description="Chart image info (natal wheel) - for mug front"
    )
    aspects_image: Optional[Dict[str, Any]] = Field(
        None,
        description="Aspects image info (planetary aspects) - for mug back"
    )
    birth_data: Dict[str, Any] = Field(..., description="Birth data used for generation")
    print_specifications: Dict[str, Any] = Field(
        ...,
        description="Print specifications (format, DPI, dimensions, compatible services)"
    )
    message: str = Field(..., description="Status message with instructions")

    class Config:
        json_schema_extra = {
            "example": {
                "chart_id": "abc123-def456",
                "mug_size": "11oz",
                "chart_image": {
                    "filename": "mug_chart_abc123.png",
                    "url": "/static/images/mug_chart_abc123.png",
                    "full_url": "https://example.com/static/images/mug_chart_abc123.png",
                    "description": "Natal chart wheel - designed for mug front"
                },
                "aspects_image": {
                    "filename": "mug_aspects_abc123.png",
                    "url": "/static/images/mug_aspects_abc123.png",
                    "full_url": "https://example.com/static/images/mug_aspects_abc123.png",
                    "description": "Planetary aspects grid - designed for mug back"
                },
                "birth_data": {
                    "name": "Jane Smith",
                    "date": "1985-03-21",
                    "time": "09:15",
                    "location": "Los Angeles, US"
                },
                "print_specifications": {
                    "format": "PNG",
                    "dpi": 300,
                    "color_mode": "RGB",
                    "dimensions": {
                        "11oz": "2700x1050 pixels (9\" x 3.5\")",
                        "15oz": "2700x1140 pixels (9\" x 3.8\")"
                    },
                    "compatible_with": ["Printful", "Printify", "CustomInk", "Zazzle"]
                },
                "message": "Mug images generated successfully. Download the PNG files and upload to your print-on-demand provider."
            }
        }
