from kerykeion import AstrologicalSubject, KerykeionChartSVG, SynastryAspects
from pathlib import Path
from typing import Dict, Any
import os
import time

class ChartGenerator:
    """Service for generating astrological charts using Kerykeion"""
    
    def __init__(self):
        # Ensure static directories exist
        self.static_dir = Path("static")
        self.static_dir.mkdir(exist_ok=True)
        self.images_dir = Path("static") / "images"
        self.images_dir.mkdir(exist_ok=True)
    
    def generate_chart(
        self, 
        name: str, 
        year: int, 
        month: int, 
        day: int, 
        hour: int, 
        minute: int, 
        city: str,
        country: str,
        chart_id: str
    ) -> Dict[str, Any]:
        """
        Generate an astrological chart and save as SVG
        
        Args:
            name: Person's name
            year: Birth year
            month: Birth month
            day: Birth day
            hour: Birth hour
            minute: Birth minute
            city: Birth city
            country: Birth country
            chart_id: Unique identifier for the chart
            
        Returns:
            Dictionary containing chart data (planets, houses, aspects)
        """
        try:
            # Set HOME environment variable to a writable directory to avoid permission issues
            import os
            from pathlib import Path
            import shutil
            
            original_home = os.environ.get('HOME')
            os.environ['HOME'] = str(Path.cwd())  # Set HOME to current working directory
            
            try:
                # Create astrological subject using kerykeion's built-in location lookup
                subject = AstrologicalSubject(
                    name=name,
                    year=year,
                    month=month,
                    day=day,
                    hour=hour,
                    minute=minute,
                    city=city,
                    nation=country,
                    geonames_username="fleminganalytic"
                )
                
                # Generate SVG chart
                chart = KerykeionChartSVG(subject)
                chart.makeSVG()
            finally:
                # Restore original HOME environment variable
                if original_home:
                    os.environ['HOME'] = original_home
                else:
                    os.environ.pop('HOME', None)
            
            # Move the generated SVG to the correct location with unique number filename
            
            # Generate unique number based on timestamp
            unique_number = int(time.time() * 1000000)  # Microsecond timestamp for uniqueness
            
            # kerykeion saves to home directory, but we need to handle different users
            # When running as www-data, home might not be writable, so check multiple locations
            possible_locations = [
                Path.home() / f"{subject.name} - Natal Chart.svg",
                Path.cwd() / f"{subject.name} - Natal Chart.svg",
                Path("/tmp") / f"{subject.name} - Natal Chart.svg"
            ]
            
            generated_file = None
            for location in possible_locations:
                if location.exists():
                    generated_file = location
                    break
            
            if generated_file is None:
                raise Exception(f"Generated SVG file not found in any of these locations: {[str(loc) for loc in possible_locations]}")
            target_file = self.images_dir / f"{unique_number}.svg"
            
            if generated_file.exists():
                shutil.move(str(generated_file), str(target_file))
            else:
                raise Exception(f"Generated SVG file not found: {generated_file}")
            
            # Extract chart data
            chart_data = {
                "planets": self._extract_planets_data(subject),
                "houses": self._extract_houses_data(subject),
                "aspects": self._extract_aspects_data(subject),
                "subject_info": {
                    "name": subject.name,
                    "julian_day": subject.julian_day,
                    "sun_sign": subject.sun["sign"],
                    "moon_sign": subject.moon["sign"],
                    "rising_sign": subject.first_house["sign"]
                },
                "coordinates": {
                    "latitude": subject.lat,
                    "longitude": subject.lng,
                    "city": subject.city,
                    "nation": subject.nation
                },
                "svg_filename": f"{unique_number}.svg"
            }
            
            return chart_data
            
        except Exception as e:
            raise Exception(f"Error generating chart: {str(e)}")
    
    def _extract_planets_data(self, subject: AstrologicalSubject) -> Dict[str, Any]:
        """Extract planetary positions and data"""
        planets = {}
        
        # List of planets to extract
        planet_names = [
            'sun', 'moon', 'mercury', 'venus', 'mars', 
            'jupiter', 'saturn', 'uranus', 'neptune', 'pluto'
        ]
        
        for planet in planet_names:
            if hasattr(subject, planet):
                planet_data = getattr(subject, planet)
                planets[planet] = {
                    "sign": planet_data.get("sign", ""),
                    "position": planet_data.get("pos", 0),
                    "house": planet_data.get("house", 0),
                    "retrograde": planet_data.get("retrograde", False)
                }
        
        return planets
    
    def _extract_houses_data(self, subject: AstrologicalSubject) -> Dict[str, Any]:
        """Extract house positions and data"""
        houses = {}
        
        # Extract house data
        for i in range(1, 13):
            house_attr = f"house_{i}" if i > 1 else "first_house"
            if hasattr(subject, house_attr):
                house_data = getattr(subject, house_attr)
                houses[f"house_{i}"] = {
                    "sign": house_data.get("sign", ""),
                    "position": house_data.get("pos", 0)
                }
        
        return houses
    
    def _extract_aspects_data(self, subject: AstrologicalSubject) -> list:
        """Extract aspects data using SynastryAspects"""
        aspects = []

        try:
            # Use SynastryAspects to calculate natal aspects (subject with itself)
            synastry = SynastryAspects(subject, subject)

            # Get the relevant aspects from synastry
            if hasattr(synastry, 'relevant_aspects') and synastry.relevant_aspects:
                for aspect in synastry.relevant_aspects:
                    # Kerykeion returns dicts, handle both dict and object access
                    if isinstance(aspect, dict):
                        p1_name = aspect.get('p1_name', '')
                        p2_name = aspect.get('p2_name', '')
                        aspect_type = aspect.get('aspect', '')
                        orbit = aspect.get('orbit', 0)
                        diff = aspect.get('diff', 0)
                    else:
                        p1_name = aspect.p1_name
                        p2_name = aspect.p2_name
                        aspect_type = aspect.aspect
                        orbit = aspect.orbit
                        diff = aspect.diff

                    # Skip self-aspects (planet with itself)
                    if p1_name != p2_name:
                        aspects.append({
                            "planet1": p1_name.lower(),
                            "planet2": p2_name.lower(),
                            "aspect": aspect_type.lower(),
                            "orb": round(orbit, 2),
                            "applying": diff < 0  # Negative diff means applying
                        })

        except Exception as e:
            print(f"Error extracting aspects: {e}")
            # Return empty list if aspect calculation fails
            aspects = []

        return aspects
