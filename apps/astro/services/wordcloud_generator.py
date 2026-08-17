import uuid
from pathlib import Path
from .. import transient
from typing import Dict, Any, List
from wordcloud import WordCloud

class WordCloudGenerator:
    """Service for generating wordclouds from astrological chart data"""

    # Astrological keywords for each sign
    SIGN_KEYWORDS = {
        "aries": ["bold", "pioneering", "assertive", "courageous", "independent", "passionate", "dynamic", "warrior"],
        "taurus": ["stable", "sensual", "grounded", "patient", "reliable", "luxurious", "steadfast", "determined"],
        "gemini": ["curious", "versatile", "communicative", "witty", "adaptable", "intellectual", "expressive", "social"],
        "cancer": ["nurturing", "protective", "intuitive", "emotional", "caring", "sensitive", "maternal", "nostalgic"],
        "leo": ["creative", "confident", "generous", "dramatic", "regal", "charismatic", "proud", "radiant"],
        "virgo": ["analytical", "practical", "meticulous", "helpful", "precise", "organized", "skilled", "devoted"],
        "libra": ["harmonious", "diplomatic", "artistic", "balanced", "romantic", "charming", "refined", "graceful"],
        "scorpio": ["intense", "transformative", "passionate", "magnetic", "mysterious", "powerful", "perceptive", "deep"],
        "sagittarius": ["adventurous", "optimistic", "philosophical", "expansive", "jovial", "wise", "explorer", "seeker"],
        "capricorn": ["ambitious", "disciplined", "responsible", "strategic", "authoritative", "persistent", "mature", "successful"],
        "aquarius": ["innovative", "humanitarian", "independent", "visionary", "unconventional", "progressive", "original", "rebel"],
        "pisces": ["imaginative", "compassionate", "dreamy", "spiritual", "artistic", "intuitive", "mystical", "empathic"]
    }

    # Keywords for each planet's energy
    PLANET_KEYWORDS = {
        "sun": ["identity", "vitality", "purpose", "willpower", "core"],
        "moon": ["emotions", "instincts", "nurturing", "comfort", "soul"],
        "mercury": ["communication", "thinking", "learning", "wit", "mind"],
        "venus": ["love", "beauty", "harmony", "pleasure", "values"],
        "mars": ["action", "drive", "courage", "energy", "ambition"],
        "jupiter": ["growth", "abundance", "wisdom", "expansion", "fortune"],
        "saturn": ["discipline", "structure", "responsibility", "mastery", "lessons"],
        "uranus": ["innovation", "revolution", "freedom", "awakening", "change"],
        "neptune": ["dreams", "spirituality", "imagination", "transcendence", "inspiration"],
        "pluto": ["transformation", "power", "rebirth", "intensity", "evolution"]
    }

    # Keywords for each element
    ELEMENT_KEYWORDS = {
        "fire": ["passionate", "energetic", "inspired", "dynamic", "enthusiastic", "bold"],
        "earth": ["grounded", "practical", "reliable", "stable", "sensual", "productive"],
        "air": ["intellectual", "communicative", "social", "curious", "analytical", "adaptable"],
        "water": ["emotional", "intuitive", "empathic", "sensitive", "imaginative", "deep"]
    }

    # Keywords for aspect types
    ASPECT_KEYWORDS = {
        "conjunction": ["unified", "focused", "intense", "merged"],
        "trine": ["harmonious", "flowing", "talented", "blessed"],
        "sextile": ["opportunistic", "creative", "supportive", "skilled"],
        "square": ["challenging", "driven", "dynamic", "motivated"],
        "opposition": ["balanced", "aware", "integrating", "perspective"],
        "quincunx": ["adjusting", "refining", "adapting", "evolving"]
    }

    # Sign abbreviation mapping
    SIGN_MAPPING = {
        'ari': 'aries', 'tau': 'taurus', 'gem': 'gemini', 'can': 'cancer',
        'leo': 'leo', 'vir': 'virgo', 'lib': 'libra', 'sco': 'scorpio',
        'sag': 'sagittarius', 'cap': 'capricorn', 'aqu': 'aquarius', 'pis': 'pisces'
    }

    def __init__(self):
        # One-shot directory, not static/ - same reasoning as the chart SVG.
        self.static_images_path = transient.ensure_dir()

    def _normalize_sign(self, sign: str) -> str:
        """Convert abbreviated or varied sign names to standard form"""
        sign_lower = sign.lower().strip()
        return self.SIGN_MAPPING.get(sign_lower, sign_lower)

    def generate_wordcloud(self, chart_data: Dict[str, Any], chart_id: str) -> str:
        """Generate wordcloud from chart data and return filename"""

        word_weights = {}

        # Extract from planets - these are the most important
        if "planets" in chart_data:
            planets = chart_data["planets"]

            # Sun sign gets highest weight (core identity)
            if "sun" in planets:
                sun_sign = self._normalize_sign(planets["sun"].get("sign", ""))
                if sun_sign in self.SIGN_KEYWORDS:
                    for keyword in self.SIGN_KEYWORDS[sun_sign][:4]:  # Top 4 keywords
                        word_weights[keyword] = word_weights.get(keyword, 0) + 100

            # Moon sign gets high weight (emotional nature)
            if "moon" in planets:
                moon_sign = self._normalize_sign(planets["moon"].get("sign", ""))
                if moon_sign in self.SIGN_KEYWORDS:
                    for keyword in self.SIGN_KEYWORDS[moon_sign][:3]:  # Top 3 keywords
                        word_weights[keyword] = word_weights.get(keyword, 0) + 80

            # Rising sign (from first house)
            if "houses" in chart_data and "house_1" in chart_data["houses"]:
                rising_sign = self._normalize_sign(chart_data["houses"]["house_1"].get("sign", ""))
                if rising_sign in self.SIGN_KEYWORDS:
                    for keyword in self.SIGN_KEYWORDS[rising_sign][:3]:
                        word_weights[keyword] = word_weights.get(keyword, 0) + 70

            # Other planets get medium weight
            for planet, data in planets.items():
                if planet not in ["sun", "moon"]:
                    planet_sign = self._normalize_sign(data.get("sign", ""))
                    if planet_sign in self.SIGN_KEYWORDS:
                        # Add 1-2 keywords per planet
                        for keyword in self.SIGN_KEYWORDS[planet_sign][:2]:
                            word_weights[keyword] = word_weights.get(keyword, 0) + 40

                    # Add planet-specific keywords
                    if planet in self.PLANET_KEYWORDS:
                        for keyword in self.PLANET_KEYWORDS[planet][:2]:
                            word_weights[keyword] = word_weights.get(keyword, 0) + 30

        # Extract from element analysis
        if "element_analysis" in chart_data:
            ea = chart_data["element_analysis"]
            dominant = ea.get("dominant_element", "").lower()
            if dominant in self.ELEMENT_KEYWORDS:
                for keyword in self.ELEMENT_KEYWORDS[dominant]:
                    word_weights[keyword] = word_weights.get(keyword, 0) + 60

            # Add keywords from element distribution
            if "detailed_analysis" in ea:
                for element, details in ea["detailed_analysis"].items():
                    count = details.get("count", 0)
                    if count >= 3 and element in self.ELEMENT_KEYWORDS:
                        for keyword in self.ELEMENT_KEYWORDS[element][:3]:
                            word_weights[keyword] = word_weights.get(keyword, 0) + count * 15

        # Extract from aspects
        if "aspects" in chart_data:
            for aspect in chart_data["aspects"][:8]:  # Top 8 aspects
                if isinstance(aspect, dict):
                    # Check the 'planets' field which contains "Planet1 aspect Planet2"
                    aspect_str = aspect.get("planets", "").lower()
                    for asp_name in self.ASPECT_KEYWORDS.keys():
                        if asp_name in aspect_str:
                            for keyword in self.ASPECT_KEYWORDS[asp_name][:2]:
                                word_weights[keyword] = word_weights.get(keyword, 0) + 25
                            break

        # Ensure we have meaningful content
        if not word_weights or sum(word_weights.values()) < 100:
            # Fallback with meaningful astrological terms
            word_weights = {
                "transformative": 100,
                "intuitive": 80,
                "passionate": 70,
                "creative": 60,
                "growth": 50,
                "harmony": 40,
                "wisdom": 35,
                "inspired": 30
            }

        # Generate wordcloud with cosmic color scheme
        # Sized larger for mug printing - will scale to fit mug dimensions
        wc = WordCloud(
            width=1200,
            height=900,
            background_color="white",
            colormap="plasma",  # Cosmic purple/pink/orange palette
            prefer_horizontal=0.8,
            relative_scaling=0.4,
            margin=15,
            max_words=18,  # Fewer words = larger each word
            min_font_size=28,  # Larger minimum for mug readability
            max_font_size=160
        ).generate_from_frequencies(word_weights)

        # Save to static/images folder
        filename = f"wordcloud_{chart_id}.png"
        filepath = self.static_images_path / filename
        wc.to_file(str(filepath))

        return filename
