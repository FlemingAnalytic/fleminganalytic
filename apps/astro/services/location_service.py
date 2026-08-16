from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import asyncio
from typing import Dict

class LocationService:
    """Service for converting location names to coordinates"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="astro_chart_generator")
    
    async def get_coordinates(self, city: str, country: str) -> Dict[str, float]:
        """
        Get latitude and longitude for a given city and country
        
        Args:
            city: City name
            country: Country name
            
        Returns:
            Dictionary with latitude and longitude
            
        Raises:
            Exception: If location cannot be found or geocoding fails
        """
        try:
            # Combine city and country for better accuracy
            location_query = f"{city}, {country}"
            
            # Run the geocoding in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            location = await loop.run_in_executor(
                None, 
                self.geolocator.geocode, 
                location_query
            )
            
            if location is None:
                # Try with just the city if full query fails
                location = await loop.run_in_executor(
                    None, 
                    self.geolocator.geocode, 
                    city
                )
            
            if location is None:
                raise Exception(f"Could not find coordinates for {city}, {country}")
            
            return {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "address": location.address
            }
            
        except GeocoderTimedOut:
            raise Exception("Geocoding service timed out. Please try again.")
        except GeocoderServiceError as e:
            raise Exception(f"Geocoding service error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error getting coordinates: {str(e)}")
