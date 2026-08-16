from typing import Dict, Any
import os
import time
from pathlib import Path

class ChartGenerator:
    """Safe wrapper for ChartGenerator that handles missing kerykeion dependency"""
    
    def __init__(self):
        # Ensure static directories exist
        self.static_dir = Path("static")
        self.static_dir.mkdir(exist_ok=True)
        self.images_dir = Path("static") / "images"
        self.images_dir.mkdir(exist_ok=True)
        
        # Check if kerykeion is available
        self.kerykeion_available = False
        try:
            from kerykeion import AstrologicalSubject, KerykeionChartSVG, SynastryAspects
            self.AstrologicalSubject = AstrologicalSubject
            self.KerykeionChartSVG = KerykeionChartSVG
            self.SynastryAspects = SynastryAspects
            self.kerykeion_available = True
        except ImportError:
            print("Warning: kerykeion not available. Chart generation will return mock data.")
    
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
        Returns mock data if kerykeion is not available
        """
        
        if not self.kerykeion_available:
            return self._generate_mock_chart_data(name, year, month, day, hour, minute, city, country, chart_id)
        
        try:
            # Create astrological subject using kerykeion's built-in location lookup
            subject = self.AstrologicalSubject(
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
            chart = self.KerykeionChartSVG(subject)
            chart.makeSVG()
            
            # Move the generated SVG to the correct location with unique number filename
            import shutil
            from pathlib import Path
            
            # Generate unique number based on timestamp
            unique_number = int(time.time() * 1000000)  # Microsecond timestamp for uniqueness
            
            # kerykeion saves to home directory, so check there
            home_dir = Path.home()
            generated_file = home_dir / f"{subject.name} - Natal Chart.svg"
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
            print(f"Error generating chart with kerykeion: {e}")
            return self._generate_mock_chart_data(name, year, month, day, hour, minute, city, country, chart_id)
    
    def _generate_mock_chart_data(self, name, year, month, day, hour, minute, city, country, chart_id):
        """Generate mock chart data when kerykeion is not available"""
        return {
            "planets": {
                "sun": {"sign": "leo", "position": 120.5, "house": 5, "retrograde": False},
                "moon": {"sign": "cancer", "position": 95.2, "house": 4, "retrograde": False},
                "mercury": {"sign": "virgo", "position": 150.8, "house": 6, "retrograde": False},
                "venus": {"sign": "libra", "position": 180.3, "house": 7, "retrograde": False},
                "mars": {"sign": "aries", "position": 15.7, "house": 1, "retrograde": False}
            },
            "houses": {
                "house_1": {"sign": "aries", "position": 0.0},
                "house_2": {"sign": "taurus", "position": 30.0},
                "house_3": {"sign": "gemini", "position": 60.0},
                "house_4": {"sign": "cancer", "position": 90.0},
                "house_5": {"sign": "leo", "position": 120.0},
                "house_6": {"sign": "virgo", "position": 150.0},
                "house_7": {"sign": "libra", "position": 180.0},
                "house_8": {"sign": "scorpio", "position": 210.0},
                "house_9": {"sign": "sagittarius", "position": 240.0},
                "house_10": {"sign": "capricorn", "position": 270.0},
                "house_11": {"sign": "aquarius", "position": 300.0},
                "house_12": {"sign": "pisces", "position": 330.0}
            },
            "aspects": [
                {"planet1": "sun", "planet2": "moon", "aspect": "trine", "orb": 2.5, "applying": True},
                {"planet1": "venus", "planet2": "mars", "aspect": "square", "orb": 3.2, "applying": False}
            ],
            "subject_info": {
                "name": name,
                "julian_day": 2459000.0,  # Mock julian day
                "sun_sign": "leo",
                "moon_sign": "cancer",
                "rising_sign": "aries"
            },
            "coordinates": {
                "latitude": 40.7128,  # Mock coordinates (NYC)
                "longitude": -74.0060,
                "city": city,
                "nation": country
            },
            "svg_filename": "mock_chart.svg"
        }
    
    def _extract_planets_data(self, subject):
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
    
    def _extract_houses_data(self, subject):
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
    
    def _extract_aspects_data(self, subject):
        """Extract aspects data using SynastryAspects"""
        aspects = []
        
        try:
            # Use SynastryAspects to calculate natal aspects (subject with itself)
            synastry = self.SynastryAspects(subject, subject)
            
            # Get the relevant aspects from synastry
            if hasattr(synastry, 'relevant_aspects') and synastry.relevant_aspects:
                for aspect in synastry.relevant_aspects:
                    # Skip self-aspects (planet with itself)
                    if aspect.p1_name != aspect.p2_name:
                        aspects.append({
                            "planet1": aspect.p1_name.lower(),
                            "planet2": aspect.p2_name.lower(),
                            "aspect": aspect.aspect.lower(),
                            "orb": round(aspect.orbit, 2),
                            "applying": aspect.diff < 0  # Negative diff means applying
                        })
        
        except Exception as e:
            print(f"Error extracting aspects: {e}")
            # Return empty list if aspect calculation fails
            aspects = []
        
        return aspects