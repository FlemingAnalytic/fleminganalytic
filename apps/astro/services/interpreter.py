import pandas as pd
from typing import Dict, Any, List
import csv
from pathlib import Path

class AstrologyInterpreter:
    """Service for generating astrological interpretations using interps.csv"""
    
    def __init__(self):
        self.interpretations_df = self._load_interpretations()
        self.risings_df = self._load_risings()
        self.aspects_df = self._load_aspects()
        self.sign_mapping = {
            'ari': 'aries', 'tau': 'taurus', 'gem': 'gemini', 'can': 'cancer',
            'leo': 'leo', 'vir': 'virgo', 'lib': 'libra', 'sco': 'scorpio',
            'sag': 'sagittarius', 'cap': 'capricorn', 'aqu': 'aquarius', 'pis': 'pisces'
        }
        self.house_mapping = {
            'first_house': 1, 'second_house': 2, 'third_house': 3, 'fourth_house': 4,
            'fifth_house': 5, 'sixth_house': 6, 'seventh_house': 7, 'eighth_house': 8,
            'ninth_house': 9, 'tenth_house': 10, 'eleventh_house': 11, 'twelfth_house': 12
        }
    
    def _load_interpretations(self) -> pd.DataFrame:
        """Load interpretation data from interps.csv"""
        try:
            # Load the comprehensive interpretations CSV
            interps_file = Path("astro/interps.csv")
            if interps_file.exists():
                df = pd.read_csv(interps_file)
                print(f"Loaded {len(df)} interpretations from interps.csv")
                return df
            else:
                print("Warning: interps.csv not found, using empty DataFrame")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading interpretations: {e}")
            return pd.DataFrame()
    
    def _load_risings(self) -> pd.DataFrame:
        """Load rising sign interpretation data from risings.csv"""
        try:
            # Load the rising sign interpretations CSV
            risings_file = Path("astro/risings.csv")
            if risings_file.exists():
                df = pd.read_csv(risings_file)
                print(f"Loaded {len(df)} rising sign interpretations from risings.csv")
                return df
            else:
                print("Warning: risings.csv not found, using empty DataFrame")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading rising interpretations: {e}")
            return pd.DataFrame()
    
    def _load_aspects(self) -> pd.DataFrame:
        """Load aspect interpretation data from aspects.csv"""
        try:
            # Load the aspect interpretations CSV
            aspects_file = Path("astro/aspects.csv")
            if aspects_file.exists():
                df = pd.read_csv(aspects_file)
                print(f"Loaded {len(df)} aspect interpretations from aspects.csv")
                return df
            else:
                print("Warning: aspects.csv not found, using empty DataFrame")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading aspect interpretations: {e}")
            return pd.DataFrame()
    
    def generate_interpretation(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive astrological interpretation
        
        Args:
            chart_data: Chart data from ChartGenerator
            
        Returns:
            Dictionary containing interpretations
        """
        try:
            interpretation = {
                "overview": self._generate_overview(chart_data),
                "planets": self._interpret_planets(chart_data.get("planets", {})),
                "houses": self._interpret_houses(chart_data.get("houses", {})),
                "aspects": self._interpret_aspects(chart_data.get("aspects", [])),
                "rising_interpretation": self._get_rising_interpretation(chart_data),
                "element_analysis": self._generate_element_analysis(chart_data),
                "observations": self._generate_observations(chart_data),
                "summary": self._generate_summary(chart_data)
            }
            
            return interpretation
            
        except Exception as e:
            print(f"Error generating interpretation: {e}")
            return {
                "overview": "Chart interpretation is being processed.",
                "planets": {},
                "houses": {},
                "aspects": [],
                "rising_interpretation": "Rising sign interpretation will be available shortly.",
                "element_analysis": {},
                "observations": [],
                "summary": "Detailed interpretation will be available shortly."
            }
    
    def _generate_overview(self, chart_data: Dict[str, Any]) -> str:
        """Generate overall chart overview"""
        subject_info = chart_data.get("subject_info", {})
        sun_sign = subject_info.get("sun_sign", "Unknown")
        moon_sign = subject_info.get("moon_sign", "Unknown")
        rising_sign = subject_info.get("rising_sign", "Unknown")
        
        overview = f"This is a natal chart for someone with Sun in {sun_sign}, Moon in {moon_sign}, and {rising_sign} rising. "
        overview += f"This combination creates a unique personality blend of {sun_sign} core identity, {moon_sign} emotional nature, and {rising_sign} outward expression."
        
        return overview
    
    def _interpret_planets(self, planets: Dict[str, Any]) -> Dict[str, str]:
        """Interpret planetary positions using interps.csv data"""
        interpretations = {}
        
        for planet, data in planets.items():
            sign_raw = data.get("sign", "").lower()
            house_raw = data.get("house", 0)
            
            # Convert abbreviated sign to full name
            sign = self.sign_mapping.get(sign_raw, sign_raw)
            
            # Convert house name to number
            if isinstance(house_raw, str):
                house = self.house_mapping.get(house_raw.lower(), 0)
            else:
                house = house_raw
            
            # Get planet in sign in house interpretation (combined)
            planet_interpretation = self._get_planet_sign_house_interpretation(planet, sign, house)
            
            if planet_interpretation:
                interpretations[planet] = planet_interpretation
            else:
                interpretations[planet] = f"{planet.title()} in {sign.title()} in House {house} brings unique energy to your chart."
        
        return interpretations
    
    def _get_planet_sign_house_interpretation(self, planet: str, sign: str, house: int) -> str:
        """Get interpretation for planet in sign in house combination"""
        if self.interpretations_df.empty or house == 0:
            return ""
        
        try:
            # Filter for exact planet, sign, and house combination
            mask = (self.interpretations_df['planet'].str.lower() == planet.lower()) & \
                   (self.interpretations_df['sign'].str.lower() == sign.lower()) & \
                   (self.interpretations_df['house'] == house)
            
            matches = self.interpretations_df[mask]
            
            if not matches.empty:
                return matches.iloc[0]['interpretation']
            
        except Exception as e:
            print(f"Error getting planet-sign-house interpretation: {e}")
        
        return ""
    
    def _interpret_houses(self, houses: Dict[str, Any]) -> Dict[str, str]:
        """Interpret house positions"""
        interpretations = {}
        
        for house, data in houses.items():
            sign = data.get("sign", "")
            house_num = house.replace("house_", "").replace("first_house", "1")
            
            interpretation = f"Your {house} is in {sign}. "
            interpretation += f"This brings {sign} energy to the themes of the {house_num}{'st' if house_num == '1' else 'nd' if house_num == '2' else 'rd' if house_num == '3' else 'th'} house, "
            interpretation += "influencing how you approach this area of life."
            
            interpretations[house] = interpretation
        
        return interpretations
    
    def _interpret_aspects(self, aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Interpret planetary aspects"""
        interpreted_aspects = []
        
        for aspect in aspects[:10]:  # Limit to top 10 aspects
            planet1 = aspect.get("planet1", "")
            planet2 = aspect.get("planet2", "")
            aspect_type = aspect.get("aspect", "")
            orb = aspect.get("orb", 0)
            applying = aspect.get("applying", False)
            
            # Generate interpretation based on aspect type
            interpretation = self._get_aspect_interpretation(planet1, planet2, aspect_type)
            
            interpreted_aspects.append({
                "planets": f"{planet1.title()} {aspect_type} {planet2.title()}",
                "orb": round(orb, 2),
                "applying": applying,
                "interpretation": interpretation,
                "strength": self._calculate_aspect_strength(orb)
            })
        
        return interpreted_aspects
    
    def _get_aspect_interpretation(self, planet1: str, planet2: str, aspect_type: str) -> str:
        """Get aspect interpretation from aspects.csv"""
        if self.aspects_df.empty:
            # Fallback to generic interpretation
            aspect_meanings = {
                "conjunction": "creates a powerful blending of energies",
                "opposition": "creates tension that seeks balance and integration",
                "trine": "creates harmonious flow and natural talent",
                "square": "creates dynamic tension that motivates growth",
                "sextile": "creates opportunities for positive expression",
                "quincunx": "creates a need for adjustment and adaptation"
            }
            base_meaning = aspect_meanings.get(aspect_type.lower(), "creates a significant interaction")
            return f"The {aspect_type} between {planet1.title()} and {planet2.title()} {base_meaning}. This aspect influences how these planetary energies work together in your personality and life experiences."
        
        try:
            # Try to find exact match first (planet1, planet2, aspect)
            mask1 = (self.aspects_df['planet1'].str.lower() == planet1.lower()) & \
                    (self.aspects_df['planet2'].str.lower() == planet2.lower()) & \
                    (self.aspects_df['aspect'].str.lower() == aspect_type.lower())
            
            matches1 = self.aspects_df[mask1]
            
            if not matches1.empty:
                return matches1.iloc[0]['interpretation']
            
            # Try reverse order (planet2, planet1, aspect)
            mask2 = (self.aspects_df['planet1'].str.lower() == planet2.lower()) & \
                    (self.aspects_df['planet2'].str.lower() == planet1.lower()) & \
                    (self.aspects_df['aspect'].str.lower() == aspect_type.lower())
            
            matches2 = self.aspects_df[mask2]
            
            if not matches2.empty:
                return matches2.iloc[0]['interpretation']
            
            # If no specific interpretation found, return generic
            aspect_meanings = {
                "conjunction": "creates a powerful blending of energies",
                "opposition": "creates tension that seeks balance and integration",
                "trine": "creates harmonious flow and natural talent",
                "square": "creates dynamic tension that motivates growth",
                "sextile": "creates opportunities for positive expression",
                "quincunx": "creates a need for adjustment and adaptation"
            }
            base_meaning = aspect_meanings.get(aspect_type.lower(), "creates a significant interaction")
            return f"The {aspect_type} between {planet1.title()} and {planet2.title()} {base_meaning}. This aspect influences how these planetary energies work together in your personality and life experiences."
            
        except Exception as e:
            print(f"Error getting aspect interpretation: {e}")
            return f"The {aspect_type} between {planet1.title()} and {planet2.title()} creates a significant interaction in your chart."
    
    def _calculate_aspect_strength(self, orb: float) -> str:
        """Calculate aspect strength based on orb"""
        abs_orb = abs(orb)
        if abs_orb <= 1:
            return "Very Strong"
        elif abs_orb <= 3:
            return "Strong"
        elif abs_orb <= 6:
            return "Moderate"
        else:
            return "Weak"
    
    def _get_rising_interpretation(self, chart_data: Dict[str, Any]) -> str:
        """Get rising sign interpretation based on sun sign and rising sign combination"""
        if self.risings_df.empty:
            return "Rising sign interpretation is being processed."
        
        try:
            subject_info = chart_data.get("subject_info", {})
            sun_sign_raw = subject_info.get("sun_sign", "").lower()
            rising_sign_raw = subject_info.get("rising_sign", "").lower()
            
            # Convert abbreviated signs to full names
            sun_sign = self.sign_mapping.get(sun_sign_raw, sun_sign_raw)
            rising_sign = self.sign_mapping.get(rising_sign_raw, rising_sign_raw)
            
            # Filter for sun sign and rising sign combination
            mask = (self.risings_df['sun_sign'].str.lower() == sun_sign.lower()) & \
                   (self.risings_df['rising_sign'].str.lower() == rising_sign.lower())
            
            matches = self.risings_df[mask]
            
            if not matches.empty:
                return matches.iloc[0]['interpretation']
            else:
                return f"Your {sun_sign.title()} Sun with {rising_sign.title()} Rising creates a unique blend of core identity and outward expression."
            
        except Exception as e:
            print(f"Error getting rising interpretation: {e}")
            return "Rising sign interpretation is being processed."
    
    def _generate_element_analysis(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive element analysis (Fire, Earth, Air, Water)"""
        element_analysis = {
            "element_distribution": {},
            "dominant_element": "",
            "lacking_element": "",
            "element_balance": "",
            "detailed_analysis": {}
        }
        
        try:
            planets = chart_data.get("planets", {})
            
            # Element mapping
            element_mapping = {
                "aries": "fire", "leo": "fire", "sagittarius": "fire",
                "taurus": "earth", "virgo": "earth", "capricorn": "earth", 
                "gemini": "air", "libra": "air", "aquarius": "air",
                "cancer": "water", "scorpio": "water", "pisces": "water"
            }
            
            # Count planets in each element
            element_counts = {"fire": 0, "earth": 0, "air": 0, "water": 0}
            element_planets = {"fire": [], "earth": [], "air": [], "water": []}
            
            for planet, data in planets.items():
                sign_raw = data.get("sign", "").lower()
                sign = self.sign_mapping.get(sign_raw, sign_raw)
                element = element_mapping.get(sign, "")
                
                if element:
                    element_counts[element] += 1
                    element_planets[element].append(planet.title())
            
            # Calculate percentages
            total_planets = sum(element_counts.values())
            element_percentages = {}
            for element, count in element_counts.items():
                percentage = (count / total_planets * 100) if total_planets > 0 else 0
                element_percentages[element] = round(percentage, 1)
            
            # Find dominant and lacking elements
            dominant_element = max(element_counts, key=element_counts.get)
            lacking_element = min(element_counts, key=element_counts.get)
            
            # Determine balance
            max_count = max(element_counts.values())
            min_count = min(element_counts.values())
            
            if max_count - min_count <= 1:
                balance = "Well-balanced"
            elif max_count >= 4:
                balance = f"Heavily {dominant_element.title()}-dominant"
            elif min_count == 0:
                balance = f"Lacking {lacking_element.title()}"
            else:
                balance = f"{dominant_element.title()}-dominant"
            
            # Generate detailed analysis for each element
            element_descriptions = {
                "fire": {
                    "keywords": "Energy, passion, enthusiasm, leadership, spontaneity",
                    "traits": "Dynamic, assertive, confident, pioneering, impulsive",
                    "high": "You have abundant energy and enthusiasm. You're naturally assertive, confident, and ready to take action. You tend to be spontaneous and passionate in your approach to life.",
                    "low": "You may need to cultivate more confidence and assertiveness. Working on taking initiative and expressing your passionate nature could be beneficial.",
                    "balanced": "You have a healthy amount of fire energy, giving you good motivation and enthusiasm while maintaining balance."
                },
                "earth": {
                    "keywords": "Practicality, stability, reliability, materialism, persistence",
                    "traits": "Grounded, practical, reliable, patient, methodical",
                    "high": "You are highly practical and grounded. You value stability, security, and tangible results. You're reliable, patient, and methodical in your approach.",
                    "low": "You may benefit from developing more practical skills and grounding techniques. Focus on building stability and following through on commitments.",
                    "balanced": "You have a good balance of practical earth energy, making you both grounded and flexible."
                },
                "air": {
                    "keywords": "Communication, intellect, ideas, social connection, adaptability",
                    "traits": "Intellectual, communicative, social, adaptable, curious",
                    "high": "You are highly intellectual and communicative. You love ideas, social connections, and mental stimulation. You're adaptable and curious about the world.",
                    "low": "You might benefit from developing your communication skills and engaging more with ideas and social connections. Cultivating curiosity could be helpful.",
                    "balanced": "You have a healthy balance of air energy, giving you good communication skills and intellectual curiosity."
                },
                "water": {
                    "keywords": "Emotion, intuition, empathy, sensitivity, imagination",
                    "traits": "Emotional, intuitive, empathetic, sensitive, imaginative",
                    "high": "You are highly emotional and intuitive. You're deeply empathetic, sensitive to others' feelings, and have a rich imagination and inner life.",
                    "low": "You may benefit from developing your emotional intelligence and intuitive abilities. Learning to trust your feelings and imagination could be valuable.",
                    "balanced": "You have a healthy balance of water energy, giving you good emotional awareness and intuition."
                }
            }
            
            detailed_analysis = {}
            for element, count in element_counts.items():
                desc = element_descriptions[element]
                
                if count >= 4:
                    analysis = desc["high"]
                elif count == 0:
                    analysis = desc["low"]
                else:
                    analysis = desc["balanced"]
                
                detailed_analysis[element] = {
                    "count": count,
                    "percentage": element_percentages[element],
                    "planets": element_planets[element],
                    "keywords": desc["keywords"],
                    "traits": desc["traits"],
                    "interpretation": analysis
                }
            
            # Generate unique element mix summary
            element_summary = self._generate_element_mix_summary(element_counts, element_percentages, dominant_element, lacking_element)
            
            element_analysis = {
                "element_distribution": element_counts,
                "element_percentages": element_percentages,
                "dominant_element": dominant_element,
                "lacking_element": lacking_element if element_counts[lacking_element] == 0 else None,
                "element_balance": balance,
                "element_summary": element_summary,
                "detailed_analysis": detailed_analysis
            }
            
        except Exception as e:
            print(f"Error generating element analysis: {e}")
            element_analysis = {
                "element_distribution": {"fire": 0, "earth": 0, "air": 0, "water": 0},
                "element_percentages": {"fire": 0, "earth": 0, "air": 0, "water": 0},
                "dominant_element": "unknown",
                "lacking_element": None,
                "element_balance": "Analysis in progress",
                "detailed_analysis": {}
            }
        
        return element_analysis
    
    def _generate_element_mix_summary(self, element_counts: Dict[str, int], element_percentages: Dict[str, float], dominant_element: str, lacking_element: str) -> str:
        """Generate a unique summary based on the specific element mix"""
        try:
            fire_count = element_counts["fire"]
            earth_count = element_counts["earth"]
            air_count = element_counts["air"]
            water_count = element_counts["water"]
            
            # Create element mix signature
            total_planets = sum(element_counts.values())
            
            # Determine the element mix pattern
            if max(element_counts.values()) - min(element_counts.values()) <= 1:
                # Well-balanced chart
                summary = "Your chart shows a remarkably balanced elemental distribution, creating a well-rounded personality. "
                summary += "You have the ability to adapt to different situations by drawing on the strengths of all four elements. "
                summary += "This balance gives you versatility in how you approach life - you can be practical when needed (Earth), "
                summary += "passionate when inspired (Fire), intellectual when challenged (Air), and intuitive when guided by feelings (Water). "
                summary += "This elemental harmony suggests a natural ability to understand and work with diverse types of people and situations."
                
            elif element_counts[lacking_element] == 0:
                # Missing element entirely
                missing_element = lacking_element
                summary = f"Your chart is notably missing {missing_element.title()} element energy, creating a unique personality pattern. "
                
                if missing_element == "fire":
                    summary += "Without Fire energy, you may approach life more cautiously and thoughtfully. You likely prefer to plan rather than act impulsively, "
                    summary += "and may need to consciously cultivate confidence and assertiveness. However, this gives you the gift of careful consideration and measured responses."
                    
                elif missing_element == "earth":
                    summary += "Without Earth energy, you may be more idealistic and less concerned with practical matters. You likely live more in the realm of ideas, "
                    summary += "emotions, and possibilities rather than focusing on material security. This gives you freedom from conventional limitations but may require "
                    summary += "conscious effort to ground your visions in reality."
                    
                elif missing_element == "air":
                    summary += "Without Air energy, you may be less focused on intellectual analysis and social networking. You likely prefer direct experience "
                    summary += "over theoretical discussion and may communicate more through actions and feelings than words. This gives you authenticity and depth "
                    summary += "but may require developing communication skills."
                    
                elif missing_element == "water":
                    summary += "Without Water energy, you may approach life more rationally and less emotionally. You likely prefer logic over intuition "
                    summary += "and may need to consciously develop your emotional intelligence and empathy. This gives you objectivity and clarity "
                    summary += "but may require learning to trust your feelings."
                    
            elif max(element_counts.values()) >= 4:
                # Heavily dominant element
                summary = f"Your chart is heavily dominated by {dominant_element.title()} energy ({element_percentages[dominant_element]}%), creating a strong elemental signature. "
                
                if dominant_element == "fire":
                    summary += "This Fire dominance makes you naturally dynamic, enthusiastic, and action-oriented. You're likely a natural leader who inspires others "
                    summary += "with your passion and confidence. You prefer to act quickly and trust your instincts. The challenge is learning patience and considering "
                    summary += "the practical details and emotional impact of your actions."
                    
                elif dominant_element == "earth":
                    summary += "This Earth dominance makes you naturally practical, reliable, and focused on tangible results. You're likely excellent at building "
                    summary += "stable foundations and following through on commitments. You prefer proven methods and gradual progress. The challenge is remaining "
                    summary += "open to new ideas and not becoming too rigid in your approach."
                    
                elif dominant_element == "air":
                    summary += "This Air dominance makes you naturally intellectual, communicative, and socially oriented. You're likely excellent at seeing connections "
                    summary += "between ideas and people. You prefer mental stimulation and variety. The challenge is grounding your ideas in practical action "
                    summary += "and not getting lost in endless possibilities."
                    
                elif dominant_element == "water":
                    summary += "This Water dominance makes you naturally intuitive, empathetic, and emotionally aware. You're likely highly sensitive to others' feelings "
                    summary += "and have a rich inner life. You prefer to follow your heart and trust your instincts. The challenge is not becoming overwhelmed "
                    summary += "by emotions and learning to set healthy boundaries."
                    
            else:
                # Moderate dominance - create custom interpretation based on the specific mix
                sorted_elements = sorted(element_counts.items(), key=lambda x: x[1], reverse=True)
                primary = sorted_elements[0]
                secondary = sorted_elements[1]
                
                summary = f"Your chart shows a {primary[0].title()}-{secondary[0].title()} emphasis, creating a unique personality blend. "
                
                # Fire-Earth combinations
                if (primary[0] == "fire" and secondary[0] == "earth") or (primary[0] == "earth" and secondary[0] == "fire"):
                    summary += "This Fire-Earth combination gives you the ability to turn passionate visions into practical reality. You can be both inspiring "
                    summary += "and reliable, bringing enthusiasm to your work while maintaining focus on tangible results. You're likely a natural entrepreneur "
                    summary += "or leader who can motivate others while keeping projects grounded."
                    
                # Fire-Air combinations  
                elif (primary[0] == "fire" and secondary[0] == "air") or (primary[0] == "air" and secondary[0] == "fire"):
                    summary += "This Fire-Air combination creates a dynamic, expressive personality. You're likely quick-thinking, articulate, and inspiring "
                    summary += "in your communication. You excel at generating and sharing ideas with enthusiasm. You may be drawn to teaching, writing, "
                    summary += "or any field where you can combine intellectual creativity with passionate expression."
                    
                # Fire-Water combinations
                elif (primary[0] == "fire" and secondary[0] == "water") or (primary[0] == "water" and secondary[0] == "fire"):
                    summary += "This Fire-Water combination creates an intensely passionate and intuitive nature. You're likely driven by strong emotions "
                    summary += "and deep convictions. You can be both fiery and compassionate, fighting for causes you believe in. This combination "
                    summary += "often indicates artistic or healing abilities, as you can channel intense feelings into creative expression."
                    
                # Earth-Air combinations
                elif (primary[0] == "earth" and secondary[0] == "air") or (primary[0] == "air" and secondary[0] == "earth"):
                    summary += "This Earth-Air combination gives you the ability to communicate practical wisdom effectively. You're likely skilled at "
                    summary += "organizing information and presenting complex ideas in understandable ways. You excel at research, planning, and any work "
                    summary += "that requires both intellectual rigor and practical application."
                    
                # Earth-Water combinations
                elif (primary[0] == "earth" and secondary[0] == "water") or (primary[0] == "water" and secondary[0] == "earth"):
                    summary += "This Earth-Water combination creates a nurturing, supportive nature with strong practical instincts. You're likely excellent "
                    summary += "at creating security and comfort for others. You combine emotional sensitivity with practical wisdom, making you a natural "
                    summary += "caregiver, counselor, or anyone who helps others build stable, emotionally fulfilling lives."
                    
                # Air-Water combinations
                elif (primary[0] == "air" and secondary[0] == "water") or (primary[0] == "water" and secondary[0] == "air"):
                    summary += "This Air-Water combination creates a highly intuitive and communicative nature. You're likely skilled at understanding "
                    summary += "and expressing complex emotions and psychological insights. You may be drawn to counseling, writing, or any field where "
                    summary += "you can help others understand themselves and their relationships better."
                    
            # Add general guidance based on the mix
            summary += f" Understanding your elemental nature can help you make choices that align with your natural strengths while "
            summary += f"consciously developing areas where you have less elemental support."
            
            return summary
            
        except Exception as e:
            print(f"Error generating element mix summary: {e}")
            return "Your unique elemental combination creates a distinctive personality pattern that influences how you approach life, relationships, and personal growth."
    
    def _generate_observations(self, chart_data: Dict[str, Any]) -> List[str]:
        """Generate observations using planet-sign-house interpretations from interps.csv"""
        observations = []
        
        try:
            planets = chart_data.get("planets", {})
            
            # Get interpretations for each planet-sign-house combination
            for planet, data in planets.items():
                sign_raw = data.get("sign", "").lower()
                house_raw = data.get("house", 0)
                
                # Convert abbreviated sign to full name
                sign = self.sign_mapping.get(sign_raw, sign_raw)
                
                # Convert house name to number
                if isinstance(house_raw, str):
                    house = self.house_mapping.get(house_raw.lower(), 0)
                else:
                    house = house_raw
                
                # Get the interpretation from interps.csv
                interpretation = self._get_planet_sign_house_interpretation(planet, sign, house)
                
                if interpretation:
                    # Format as "Planet in Sign in House: interpretation"
                    observation = f"{planet.title()} in {sign.title()} in House {house}: {interpretation}"
                    observations.append(observation)
                else:
                    # Fallback if no interpretation found
                    observation = f"{planet.title()} in {sign.title()} in House {house}: Brings unique energy to your chart."
                    observations.append(observation)
            
        except Exception as e:
            print(f"Error generating observations: {e}")
            observations.append("Chart analysis in progress")
        
        return observations
    
    def _generate_summary(self, chart_data: Dict[str, Any]) -> str:
        """Generate chart summary"""
        subject_info = chart_data.get("subject_info", {})
        planets = chart_data.get("planets", {})
        aspects = chart_data.get("aspects", [])
        
        summary = "This natal chart reveals a complex and unique individual with distinct strengths and areas for growth. "
        
        # Add some specific observations
        retrograde_planets = [planet for planet, data in planets.items() if data.get("retrograde", False)]
        if retrograde_planets:
            summary += f"Notable features include {len(retrograde_planets)} retrograde planet(s): {', '.join(retrograde_planets)}. "
        
        summary += f"The chart contains {len(aspects)} significant aspects, creating a rich tapestry of personality traits and life themes. "
        summary += "The planetary positions and aspects work together to create your unique cosmic blueprint."
        
        return summary
