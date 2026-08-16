"""
Mug Image Generator Service

Generates high-resolution PNG images optimized for print-on-demand mug printing.
Supports both Printful and Printify specifications.

Mug Specifications:
- 11oz mug: 2700x1050 pixels (9" x 3.5" at 300 DPI)
- 15oz mug: 2700x1140 pixels
- Format: PNG with transparent background
- Color: RGB
"""

import cairosvg
from PIL import Image, ImageDraw, ImageFont
import io
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import math


class MugImageGenerator:
    """Service for generating mug-ready PNG images from astrology charts"""

    # Mug print area dimensions (in pixels at 300 DPI)
    MUG_DIMENSIONS = {
        "11oz": (2700, 1050),  # 9" x 3.5"
        "15oz": (2700, 1140),  # 9" x 3.8"
    }

    # Chart image will be square, sized to fit the mug height with padding
    PADDING = 50  # pixels

    # Aspect symbols for display
    ASPECT_SYMBOLS = {
        "conjunction": "☌",
        "opposition": "☍",
        "trine": "△",
        "square": "□",
        "sextile": "⚹",
        "quincunx": "⚻",
        "quintile": "Q",
        "biquintile": "bQ",
        "semisextile": "⚺",
        "semisquare": "∠",
        "sesquiquadrate": "⚼",
    }

    # Planet symbols for display
    PLANET_SYMBOLS = {
        "sun": "☉",
        "moon": "☽",
        "mercury": "☿",
        "venus": "♀",
        "mars": "♂",
        "jupiter": "♃",
        "saturn": "♄",
        "uranus": "♅",
        "neptune": "♆",
        "pluto": "♇",
        "chiron": "⚷",
        "mean_node": "☊",
        "true_node": "☊",
    }

    # Zodiac symbols
    ZODIAC_SYMBOLS = {
        "aries": "♈", "taurus": "♉", "gemini": "♊", "cancer": "♋",
        "leo": "♌", "virgo": "♍", "libra": "♎", "scorpio": "♏",
        "sagittarius": "♐", "capricorn": "♑", "aquarius": "♒", "pisces": "♓"
    }

    # Color scheme for aspects
    ASPECT_COLORS = {
        "conjunction": "#5757e2",  # Blue-purple
        "opposition": "#510060",   # Purple
        "trine": "#36d100",        # Green
        "square": "#dc0000",       # Red
        "sextile": "#d59e28",      # Gold
        "quincunx": "#1f99b3",     # Teal
    }

    # CSS variable replacements for SVG conversion
    CSS_COLOR_REPLACEMENTS = {
        'var(--kerykeion-chart-color-paper-0)': '#000000',
        'var(--kerykeion-chart-color-paper-1)': '#ffffff',
        'var(--kerykeion-chart-color-zodiac-bg-0)': '#ff7200',
        'var(--kerykeion-chart-color-zodiac-bg-1)': '#6b3d00',
        'var(--kerykeion-chart-color-zodiac-bg-2)': '#69acf1',
        'var(--kerykeion-chart-color-zodiac-bg-3)': '#2b4972',
        'var(--kerykeion-chart-color-zodiac-bg-4)': '#ff7200',
        'var(--kerykeion-chart-color-zodiac-bg-5)': '#6b3d00',
        'var(--kerykeion-chart-color-zodiac-bg-6)': '#69acf1',
        'var(--kerykeion-chart-color-zodiac-bg-7)': '#2b4972',
        'var(--kerykeion-chart-color-zodiac-bg-8)': '#ff7200',
        'var(--kerykeion-chart-color-zodiac-bg-9)': '#6b3d00',
        'var(--kerykeion-chart-color-zodiac-bg-10)': '#69acf1',
        'var(--kerykeion-chart-color-zodiac-bg-11)': '#2b4972',
        'var(--kerykeion-chart-color-zodiac-icon-0)': '#ff7200',
        'var(--kerykeion-chart-color-zodiac-icon-1)': '#6b3d00',
        'var(--kerykeion-chart-color-zodiac-icon-2)': '#69acf1',
        'var(--kerykeion-chart-color-zodiac-icon-3)': '#2b4972',
        'var(--kerykeion-chart-color-zodiac-icon-4)': '#ff7200',
        'var(--kerykeion-chart-color-zodiac-icon-5)': '#6b3d00',
        'var(--kerykeion-chart-color-zodiac-icon-6)': '#69acf1',
        'var(--kerykeion-chart-color-zodiac-icon-7)': '#2b4972',
        'var(--kerykeion-chart-color-zodiac-icon-8)': '#ff7200',
        'var(--kerykeion-chart-color-zodiac-icon-9)': '#6b3d00',
        'var(--kerykeion-chart-color-zodiac-icon-10)': '#69acf1',
        'var(--kerykeion-chart-color-zodiac-icon-11)': '#2b4972',
        'var(--kerykeion-chart-color-conjunction)': '#5757e2',
        'var(--kerykeion-chart-color-sextile)': '#d59e28',
        'var(--kerykeion-chart-color-square)': '#dc0000',
        'var(--kerykeion-chart-color-trine)': '#36d100',
        'var(--kerykeion-chart-color-opposition)': '#510060',
        'var(--kerykeion-chart-color-quintile)': '#1f99b3',
        'var(--kerykeion-chart-color-sun)': '#984b00',
        'var(--kerykeion-chart-color-moon)': '#150052',
        'var(--kerykeion-chart-color-mercury)': '#520800',
        'var(--kerykeion-chart-color-venus)': '#400052',
        'var(--kerykeion-chart-color-mars)': '#540000',
        'var(--kerykeion-chart-color-jupiter)': '#47133d',
        'var(--kerykeion-chart-color-saturn)': '#124500',
        'var(--kerykeion-chart-color-uranus)': '#6f0766',
        'var(--kerykeion-chart-color-neptune)': '#06537f',
        'var(--kerykeion-chart-color-pluto)': '#713f04',
        'var(--kerykeion-chart-color-mean-node)': '#4c1541',
        'var(--kerykeion-chart-color-chiron)': '#666f06',
        'var(--kerykeion-chart-color-first-house)': '#ff7e00',
        'var(--kerykeion-chart-color-tenth-house)': '#ff0000',
        'var(--kerykeion-chart-color-seventh-house)': '#0000ff',
        'var(--kerykeion-chart-color-fourth-house)': '#000000',
        'var(--kerykeion-chart-color-house-number)': '#f00',
        'var(--kerykeion-chart-color-zodiac-radix-ring-0)': '#ff0000',
        'var(--kerykeion-chart-color-zodiac-radix-ring-1)': '#ff0000',
        'var(--kerykeion-chart-color-zodiac-radix-ring-2)': '#ff0000',
        'var(--kerykeion-chart-color-houses-radix-line)': '#ff0000',
        'var(--kerykeion-chart-color-lunar-phase-0)': '#000000',
        'var(--kerykeion-chart-color-lunar-phase-1)': '#ffffff'
    }

    # Sun-Rising combinations: The Sun is WHO you are, Rising is HOW you appear
    # Format: (sun_sign, rising_sign): "brief saying"
    SUN_RISING_COMBOS = {
        # Aries Sun
        ('aries', 'aries'): "A warrior through and through - bold inside and out",
        ('aries', 'taurus'): "Fire in the soul, steady on the surface",
        ('aries', 'gemini'): "Quick-witted pioneer with endless curiosity",
        ('aries', 'cancer'): "Fierce protector with a nurturing shell",
        ('aries', 'leo'): "Born leader who commands every room",
        ('aries', 'virgo'): "Passionate spirit, meticulous presentation",
        ('aries', 'libra'): "Inner warrior wearing diplomatic armor",
        ('aries', 'scorpio'): "Intense fire burning with magnetic power",
        ('aries', 'sagittarius'): "Adventurous soul with an inspiring presence",
        ('aries', 'capricorn'): "Ambitious pioneer with executive polish",
        ('aries', 'aquarius'): "Independent trailblazer ahead of the times",
        ('aries', 'pisces'): "Courageous heart wrapped in gentle mystery",
        # Taurus Sun
        ('taurus', 'aries'): "Steady soul with a bold first impression",
        ('taurus', 'taurus'): "Grounded through and through - reliable and real",
        ('taurus', 'gemini'): "Sensual nature with a quick, curious mind",
        ('taurus', 'cancer'): "Comfort-seeker with a nurturing presence",
        ('taurus', 'leo'): "Luxury lover who radiates warmth and style",
        ('taurus', 'virgo'): "Practical perfectionist with quiet strength",
        ('taurus', 'libra'): "Beauty lover with natural grace and charm",
        ('taurus', 'scorpio'): "Deep sensuality beneath magnetic intensity",
        ('taurus', 'sagittarius'): "Earthy soul with an adventurous spirit",
        ('taurus', 'capricorn'): "Builder of empires - patient and powerful",
        ('taurus', 'aquarius'): "Traditional values, unconventional style",
        ('taurus', 'pisces'): "Sensual dreamer with artistic soul",
        # Gemini Sun
        ('gemini', 'aries'): "Quick mind with bold, direct delivery",
        ('gemini', 'taurus'): "Curious intellect, grounded presence",
        ('gemini', 'gemini'): "Mercurial mind - witty and ever-changing",
        ('gemini', 'cancer'): "Clever communicator with emotional depth",
        ('gemini', 'leo'): "Brilliant storyteller who loves the spotlight",
        ('gemini', 'virgo'): "Sharp analyst with attention to every detail",
        ('gemini', 'libra'): "Social butterfly with natural charm",
        ('gemini', 'scorpio'): "Quick wit masking profound depths",
        ('gemini', 'sagittarius'): "Eternal student, inspiring teacher",
        ('gemini', 'capricorn'): "Versatile mind with serious ambitions",
        ('gemini', 'aquarius'): "Innovative thinker, ahead of the crowd",
        ('gemini', 'pisces'): "Imaginative wordsmith with poetic soul",
        # Cancer Sun
        ('cancer', 'aries'): "Protective heart with warrior courage",
        ('cancer', 'taurus'): "Nurturing soul seeking comfort and security",
        ('cancer', 'gemini'): "Emotional depth expressed through words",
        ('cancer', 'cancer'): "Deep feeler - intuitive and protective",
        ('cancer', 'leo'): "Caring heart that loves to shine for others",
        ('cancer', 'virgo'): "Devoted helper with healing instincts",
        ('cancer', 'libra'): "Emotional nature seeking harmony in all",
        ('cancer', 'scorpio'): "Profound emotional depths and loyalty",
        ('cancer', 'sagittarius'): "Homebody heart with wandering spirit",
        ('cancer', 'capricorn'): "Sensitive soul with ambitious drive",
        ('cancer', 'aquarius'): "Family-oriented with humanitarian ideals",
        ('cancer', 'pisces'): "Deeply intuitive, compassionate dreamer",
        # Leo Sun
        ('leo', 'aries'): "Born to lead with courage and confidence",
        ('leo', 'taurus'): "Regal soul who appreciates life's luxuries",
        ('leo', 'gemini'): "Creative entertainer with sparkling wit",
        ('leo', 'cancer'): "Warm heart that nurtures with generosity",
        ('leo', 'leo'): "Pure sunshine - dramatic, proud, and warm",
        ('leo', 'virgo'): "Creative spirit with perfectionist edge",
        ('leo', 'libra'): "Natural star with irresistible charm",
        ('leo', 'scorpio'): "Powerful presence with magnetic intensity",
        ('leo', 'sagittarius'): "Inspiring leader with boundless optimism",
        ('leo', 'capricorn'): "Creative authority with executive power",
        ('leo', 'aquarius'): "Unique star who stands out from the crowd",
        ('leo', 'pisces'): "Creative dreamer with generous heart",
        # Virgo Sun
        ('virgo', 'aries'): "Analytical mind with assertive action",
        ('virgo', 'taurus'): "Practical perfectionist, steady and reliable",
        ('virgo', 'gemini'): "Brilliant analyst with quick communication",
        ('virgo', 'cancer'): "Helpful soul with nurturing instincts",
        ('virgo', 'leo'): "Detail master who presents with confidence",
        ('virgo', 'virgo'): "Precision personified - helpful and humble",
        ('virgo', 'libra'): "Discerning eye for beauty and balance",
        ('virgo', 'scorpio'): "Sharp mind with investigative depth",
        ('virgo', 'sagittarius'): "Critical thinker with philosophical bent",
        ('virgo', 'capricorn'): "Masterful worker building lasting success",
        ('virgo', 'aquarius'): "Analytical mind serving humanitarian goals",
        ('virgo', 'pisces'): "Practical helper with compassionate heart",
        # Libra Sun
        ('libra', 'aries'): "Peacemaker with surprising assertiveness",
        ('libra', 'taurus'): "Harmony seeker who values beauty and comfort",
        ('libra', 'gemini'): "Charming diplomat with clever conversation",
        ('libra', 'cancer'): "Relationship-focused with nurturing care",
        ('libra', 'leo'): "Social star radiating warmth and grace",
        ('libra', 'virgo'): "Balanced mind with attention to detail",
        ('libra', 'libra'): "Grace personified - fair, charming, refined",
        ('libra', 'scorpio'): "Diplomatic surface, intense underneath",
        ('libra', 'sagittarius'): "Justice seeker with optimistic vision",
        ('libra', 'capricorn'): "Fair-minded with ambitious goals",
        ('libra', 'aquarius'): "Idealist championing equality for all",
        ('libra', 'pisces'): "Romantic soul seeking beauty and peace",
        # Scorpio Sun
        ('scorpio', 'aries'): "Intense power with bold, direct action",
        ('scorpio', 'taurus'): "Deep passion grounded in sensuality",
        ('scorpio', 'gemini'): "Penetrating mind with quick adaptability",
        ('scorpio', 'cancer'): "Profound emotional depth and loyalty",
        ('scorpio', 'leo'): "Magnetic power that commands attention",
        ('scorpio', 'virgo'): "Investigative mind with precise analysis",
        ('scorpio', 'libra'): "Intense soul behind a charming facade",
        ('scorpio', 'scorpio'): "Powerfully transformative - nothing hidden",
        ('scorpio', 'sagittarius'): "Deep seeker of truth and meaning",
        ('scorpio', 'capricorn'): "Strategic power building lasting legacy",
        ('scorpio', 'aquarius'): "Revolutionary transformer of systems",
        ('scorpio', 'pisces'): "Psychic depths and spiritual power",
        # Sagittarius Sun
        ('sagittarius', 'aries'): "Adventurer charging boldly forward",
        ('sagittarius', 'taurus'): "Philosophical soul grounded in pleasure",
        ('sagittarius', 'gemini'): "Eternal student teaching eternal truths",
        ('sagittarius', 'cancer'): "Explorer who always finds their way home",
        ('sagittarius', 'leo'): "Inspiring teacher who lights up the world",
        ('sagittarius', 'virgo'): "Wisdom seeker with practical application",
        ('sagittarius', 'libra'): "Truth seeker with diplomatic delivery",
        ('sagittarius', 'scorpio'): "Deep philosopher exploring life's mysteries",
        ('sagittarius', 'sagittarius'): "Free spirit - optimistic and unstoppable",
        ('sagittarius', 'capricorn'): "Visionary building real-world success",
        ('sagittarius', 'aquarius'): "Progressive idealist expanding horizons",
        ('sagittarius', 'pisces'): "Spiritual adventurer seeking meaning",
        # Capricorn Sun
        ('capricorn', 'aries'): "Ambitious achiever with bold initiative",
        ('capricorn', 'taurus'): "Patient builder creating lasting wealth",
        ('capricorn', 'gemini'): "Strategic mind with versatile approach",
        ('capricorn', 'cancer'): "Success-driven with family at the core",
        ('capricorn', 'leo'): "Authority figure who leads with dignity",
        ('capricorn', 'virgo'): "Masterful worker - disciplined and precise",
        ('capricorn', 'libra'): "Ambitious diplomat climbing with grace",
        ('capricorn', 'scorpio'): "Powerful strategist playing the long game",
        ('capricorn', 'sagittarius'): "Goal-setter with expansive vision",
        ('capricorn', 'capricorn'): "Mountain climber - determined and dignified",
        ('capricorn', 'aquarius'): "Traditional achiever with modern methods",
        ('capricorn', 'pisces'): "Practical dreamer building real results",
        # Aquarius Sun
        ('aquarius', 'aries'): "Revolutionary taking bold action for change",
        ('aquarius', 'taurus'): "Innovative mind with grounded approach",
        ('aquarius', 'gemini'): "Brilliant original with endless ideas",
        ('aquarius', 'cancer'): "Humanitarian heart caring for community",
        ('aquarius', 'leo'): "Unique individual who stands out proudly",
        ('aquarius', 'virgo'): "Progressive thinker with practical solutions",
        ('aquarius', 'libra'): "Social visionary promoting equality",
        ('aquarius', 'scorpio'): "Deep reformer transforming society",
        ('aquarius', 'sagittarius'): "Freedom fighter with global vision",
        ('aquarius', 'capricorn'): "Innovator building structures for tomorrow",
        ('aquarius', 'aquarius'): "True original - eccentric and electric",
        ('aquarius', 'pisces'): "Visionary dreamer serving humanity",
        # Pisces Sun
        ('pisces', 'aries'): "Dreamer who acts on intuition boldly",
        ('pisces', 'taurus'): "Artistic soul grounded in sensory beauty",
        ('pisces', 'gemini'): "Imaginative storyteller with many voices",
        ('pisces', 'cancer'): "Deeply intuitive, emotionally attuned",
        ('pisces', 'leo'): "Creative dreamer who shines compassionately",
        ('pisces', 'virgo'): "Spiritual healer with practical service",
        ('pisces', 'libra'): "Romantic idealist seeking beauty and peace",
        ('pisces', 'scorpio'): "Profound psychic depths and spiritual power",
        ('pisces', 'sagittarius'): "Mystical seeker of universal truth",
        ('pisces', 'capricorn'): "Dreamer who manifests visions into reality",
        ('pisces', 'aquarius'): "Compassionate visionary serving all",
        ('pisces', 'pisces'): "Pure mystic - boundless compassion and intuition",
    }

    def __init__(self):
        self.images_dir = Path("static") / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def _get_aspect_meaning(self, planet1: str, planet2: str, aspect_type: str) -> str:
        """Get a specific meaning based on the planet pair and aspect type"""
        # Normalize planet names
        p1, p2 = planet1.lower(), planet2.lower()
        # Create sorted key so Sun-Moon == Moon-Sun
        pair = tuple(sorted([p1, p2]))

        # Planet pair specific interpretations for harmonious aspects (trine, sextile)
        harmonious_meanings = {
            ('moon', 'sun'): "emotional and identity in sync",
            ('mercury', 'sun'): "clear self-expression",
            ('sun', 'venus'): "natural charm and warmth",
            ('mars', 'sun'): "confident action-taker",
            ('jupiter', 'sun'): "optimistic and fortunate",
            ('saturn', 'sun'): "disciplined success over time",
            ('sun', 'uranus'): "authentic individuality",
            ('neptune', 'sun'): "creative vision and inspiration",
            ('pluto', 'sun'): "powerful presence and depth",
            ('mercury', 'moon'): "intuitive communication",
            ('moon', 'venus'): "emotionally affectionate",
            ('mars', 'moon'): "emotionally motivated action",
            ('jupiter', 'moon'): "generous emotional nature",
            ('moon', 'saturn'): "emotionally mature and stable",
            ('moon', 'uranus'): "emotionally independent",
            ('moon', 'neptune'): "deeply empathic and intuitive",
            ('moon', 'pluto'): "intense emotional depth",
            ('mercury', 'venus'): "graceful communicator",
            ('mars', 'mercury'): "quick-witted and decisive",
            ('jupiter', 'mercury'): "big-picture thinking",
            ('mercury', 'saturn'): "methodical, structured mind",
            ('mercury', 'uranus'): "inventive, original ideas",
            ('mercury', 'neptune'): "imaginative storyteller",
            ('mercury', 'pluto'): "penetrating insight",
            ('mars', 'venus'): "passionate and magnetic",
            ('jupiter', 'venus'): "generous in love",
            ('saturn', 'venus'): "loyal, enduring affection",
            ('uranus', 'venus'): "unconventional in love",
            ('neptune', 'venus'): "romantic idealist",
            ('pluto', 'venus'): "transformative relationships",
            ('jupiter', 'mars'): "enthusiastic achiever",
            ('mars', 'saturn'): "disciplined energy and drive",
            ('mars', 'uranus'): "bold, sudden actions",
            ('mars', 'neptune'): "inspired action, spiritual drive",
            ('mars', 'pluto'): "powerful determination",
            ('jupiter', 'saturn'): "balanced growth and structure",
            ('jupiter', 'uranus'): "lucky breakthroughs",
            ('jupiter', 'neptune'): "spiritual expansion",
            ('jupiter', 'pluto'): "transformative success",
            ('saturn', 'uranus'): "innovative within structure",
            ('neptune', 'saturn'): "dreams made real",
            ('pluto', 'saturn'): "profound endurance",
            ('neptune', 'uranus'): "visionary generation",
            ('pluto', 'uranus'): "revolutionary transformation",
            ('neptune', 'pluto'): "deep collective unconscious",
            ('chiron', 'sun'): "healing through self-expression",
            ('chiron', 'moon'): "emotional healing gifts",
            ('chiron', 'mercury'): "healing through words",
            ('chiron', 'venus'): "healing through love",
            ('chiron', 'mars'): "healing through action",
            ('sun', 'true_node'): "destined path aligns with self",
            ('moon', 'true_node'): "emotional growth is your path",
            ('mercury', 'true_node'): "communication supports destiny",
            ('venus', 'true_node'): "love leads you forward",
            ('mars', 'true_node'): "actions align with purpose",
            ('jupiter', 'true_node'): "expansion on your path",
            ('saturn', 'true_node'): "karmic lessons support growth",
            ('sun', 'mean_node'): "destined path aligns with self",
            ('moon', 'mean_node'): "emotional growth is your path",
            # Ascendant/Rising aspects - critical for personality expression
            ('ascendant', 'sun'): "identity shines through persona",
            ('asc', 'sun'): "identity shines through persona",
            ('ascendant', 'moon'): "emotions easily expressed",
            ('asc', 'moon'): "emotions easily expressed",
            ('ascendant', 'mercury'): "articulate first impression",
            ('asc', 'mercury'): "articulate first impression",
            ('ascendant', 'venus'): "charming, attractive presence",
            ('asc', 'venus'): "charming, attractive presence",
            ('ascendant', 'mars'): "dynamic, energetic presence",
            ('asc', 'mars'): "dynamic, energetic presence",
            ('ascendant', 'jupiter'): "optimistic, generous aura",
            ('asc', 'jupiter'): "optimistic, generous aura",
            ('ascendant', 'saturn'): "mature, responsible demeanor",
            ('asc', 'saturn'): "mature, responsible demeanor",
            ('ascendant', 'uranus'): "unique, eccentric style",
            ('asc', 'uranus'): "unique, eccentric style",
            ('ascendant', 'neptune'): "dreamy, artistic appearance",
            ('asc', 'neptune'): "dreamy, artistic appearance",
            ('ascendant', 'pluto'): "intense, magnetic presence",
            ('asc', 'pluto'): "intense, magnetic presence",
        }

        # Planet pair specific for challenging aspects (square, opposition)
        challenging_meanings = {
            ('moon', 'sun'): "inner conflict drives growth",
            ('mercury', 'sun'): "mind and ego at odds",
            ('sun', 'venus'): "values challenge identity",
            ('mars', 'sun'): "willpower needs directing",
            ('jupiter', 'sun'): "overconfidence to overcome",
            ('saturn', 'sun'): "self-doubt to master",
            ('sun', 'uranus'): "rebellion vs. stability",
            ('neptune', 'sun'): "illusion vs. reality",
            ('pluto', 'sun'): "power struggles transform you",
            ('mercury', 'moon'): "head vs. heart tension",
            ('moon', 'venus'): "emotional needs vs. desires",
            ('mars', 'moon'): "emotions trigger reactions",
            ('jupiter', 'moon'): "emotional excess to balance",
            ('moon', 'saturn'): "emotional restriction to heal",
            ('moon', 'uranus'): "emotional unpredictability",
            ('moon', 'neptune'): "emotional boundaries needed",
            ('moon', 'pluto'): "intense emotional patterns",
            ('mercury', 'venus'): "communication in relationships",
            ('mars', 'mercury'): "impulsive words to tame",
            ('jupiter', 'mercury'): "details vs. big picture",
            ('mercury', 'saturn'): "mental blocks to overcome",
            ('mercury', 'uranus'): "scattered thinking to focus",
            ('mercury', 'neptune'): "confusion seeking clarity",
            ('mercury', 'pluto'): "obsessive thoughts to release",
            ('mars', 'venus'): "passion vs. harmony",
            ('jupiter', 'venus'): "excess in pleasure",
            ('saturn', 'venus'): "love feels restricted",
            ('uranus', 'venus'): "commitment vs. freedom",
            ('neptune', 'venus'): "idealized love vs. reality",
            ('pluto', 'venus'): "intense attachments",
            ('jupiter', 'mars'): "energy needs channeling",
            ('mars', 'saturn'): "frustrated ambition fuels drive",
            ('mars', 'uranus'): "impulsive risk-taking",
            ('mars', 'neptune'): "misdirected energy",
            ('mars', 'pluto'): "power and anger to master",
            ('jupiter', 'saturn'): "expansion vs. limitation",
            ('jupiter', 'uranus'): "restless for change",
            ('jupiter', 'neptune'): "unrealistic expectations",
            ('jupiter', 'pluto'): "ambition needs ethics",
            ('saturn', 'uranus'): "tradition vs. innovation",
            ('neptune', 'saturn'): "fear vs. faith",
            ('pluto', 'saturn'): "control issues to release",
            ('neptune', 'uranus'): "idealism meets disruption",
            ('pluto', 'uranus'): "radical transformation",
            ('neptune', 'pluto'): "generation's unconscious",
            ('chiron', 'sun'): "core wound seeking healing",
            ('chiron', 'moon'): "emotional wounds surface",
            ('chiron', 'mercury'): "communication wounds",
            ('chiron', 'venus'): "relationship wounds",
            ('chiron', 'mars'): "wounds around assertion",
            ('sun', 'true_node'): "ego challenges your path",
            ('moon', 'true_node'): "emotions resist destiny",
            ('mercury', 'true_node'): "overthinking blocks growth",
            ('venus', 'true_node'): "comfort zone vs. growth",
            ('mars', 'true_node'): "actions misaligned, recalibrate",
            ('saturn', 'true_node'): "fear blocks your purpose",
            ('sun', 'mean_node'): "ego challenges your path",
            ('moon', 'mean_node'): "emotions resist destiny",
            # Ascendant challenges
            ('ascendant', 'sun'): "identity vs. how you appear",
            ('asc', 'sun'): "identity vs. how you appear",
            ('ascendant', 'moon'): "emotions hidden from others",
            ('asc', 'moon'): "emotions hidden from others",
            ('ascendant', 'mercury'): "misunderstood communication",
            ('asc', 'mercury'): "misunderstood communication",
            ('ascendant', 'venus'): "love life affects image",
            ('asc', 'venus'): "love life affects image",
            ('ascendant', 'mars'): "aggressive first impression",
            ('asc', 'mars'): "aggressive first impression",
            ('ascendant', 'jupiter'): "overconfident appearance",
            ('asc', 'jupiter'): "overconfident appearance",
            ('ascendant', 'saturn'): "reserved, guarded persona",
            ('asc', 'saturn'): "reserved, guarded persona",
            ('ascendant', 'uranus'): "disruptive to others",
            ('asc', 'uranus'): "disruptive to others",
            ('ascendant', 'neptune'): "confusing self-presentation",
            ('asc', 'neptune'): "confusing self-presentation",
            ('ascendant', 'pluto'): "power struggles in relating",
            ('asc', 'pluto'): "power struggles in relating",
        }

        # Conjunction meanings (blending)
        conjunction_meanings = {
            ('moon', 'sun'): "new moon soul, fresh starts",
            ('mercury', 'sun'): "mind merged with identity",
            ('sun', 'venus'): "identity through beauty/love",
            ('mars', 'sun'): "action-oriented identity",
            ('jupiter', 'sun'): "expansive, lucky personality",
            ('saturn', 'sun'): "serious, responsible nature",
            ('sun', 'uranus'): "unique, unconventional self",
            ('neptune', 'sun'): "dreamy, artistic identity",
            ('pluto', 'sun'): "intense, powerful presence",
            ('mercury', 'moon'): "feelings shape thoughts",
            ('moon', 'venus'): "nurturing, loving nature",
            ('mars', 'moon'): "emotionally driven action",
            ('jupiter', 'moon'): "generous, optimistic feelings",
            ('moon', 'saturn'): "cautious emotional nature",
            ('moon', 'uranus'): "emotionally unpredictable",
            ('moon', 'neptune'): "highly intuitive, empathic",
            ('moon', 'pluto'): "deep emotional intensity",
            ('mercury', 'venus'): "charming communicator",
            ('mars', 'mercury'): "sharp, quick mind",
            ('jupiter', 'mercury'): "optimistic thinker",
            ('mercury', 'saturn'): "serious, careful thinker",
            ('mercury', 'uranus'): "brilliant, inventive mind",
            ('mercury', 'neptune'): "imaginative, poetic mind",
            ('mercury', 'pluto'): "probing, research mind",
            ('mars', 'venus'): "passionate nature",
            ('jupiter', 'venus'): "generous, loving heart",
            ('saturn', 'venus'): "serious about love",
            ('uranus', 'venus'): "unconventional tastes",
            ('neptune', 'venus'): "romantic, artistic soul",
            ('pluto', 'venus'): "intense attractions",
            ('jupiter', 'mars'): "bold, enthusiastic action",
            ('mars', 'saturn'): "controlled, persistent effort",
            ('mars', 'uranus'): "sudden, explosive energy",
            ('mars', 'neptune'): "inspired, spiritual action",
            ('mars', 'pluto'): "powerful drive and will",
            ('jupiter', 'saturn'): "measured expansion",
            ('jupiter', 'uranus'): "sudden opportunities",
            ('jupiter', 'neptune'): "spiritual seeker",
            ('jupiter', 'pluto'): "powerful ambition",
            ('saturn', 'uranus'): "structured innovation",
            ('neptune', 'saturn'): "practical dreams",
            ('pluto', 'saturn'): "deep transformation",
            ('neptune', 'uranus'): "visionary ideals",
            ('pluto', 'uranus'): "revolutionary force",
            ('neptune', 'pluto'): "generational depth",
        }

        # Select meaning based on aspect type
        if aspect_type in ('trine', 'sextile'):
            meanings = harmonious_meanings
        elif aspect_type in ('square', 'opposition'):
            meanings = challenging_meanings
        elif aspect_type == 'conjunction':
            meanings = conjunction_meanings
        else:
            # For minor aspects, use harmonious for quintile/semisextile, challenging for others
            if aspect_type in ('quintile', 'biquintile', 'semisextile'):
                meanings = harmonious_meanings
            else:
                meanings = challenging_meanings

        # Look up specific meaning
        meaning = meanings.get(pair, '')

        # Fallback to generic if no specific meaning found
        if not meaning:
            generic = {
                'conjunction': 'energies fused together',
                'opposition': 'awareness through tension',
                'trine': 'natural flow and ease',
                'square': 'growth through challenge',
                'sextile': 'opportunity through effort',
                'quintile': 'creative talent',
                'quincunx': 'adjustment required',
                'semisextile': 'subtle growth',
                'semisquare': 'minor friction',
                'sesquiquadrate': 'persistent tension'
            }
            meaning = generic.get(aspect_type, '')

        return meaning

    def _convert_svg_to_png(self, svg_path: str, output_size: int, crop_to_wheel: bool = False) -> Optional[bytes]:
        """Convert SVG file to PNG with specified size

        Args:
            svg_path: Path to the SVG file
            output_size: Output image size in pixels
            crop_to_wheel: If True, crop to just the chart wheel (remove info panel)
        """
        try:
            with open(svg_path, 'r', encoding='utf-8') as svg_file:
                svg_content = svg_file.read()

            # Replace CSS variables with actual colors
            for css_var, color_value in self.CSS_COLOR_REPLACEMENTS.items():
                svg_content = svg_content.replace(css_var, color_value)

            if crop_to_wheel:
                # Render at higher resolution then crop to wheel
                # SVG is 772x546, wheel is at (50,50) with size 480x480
                # Scale factor to render wheel portion at desired output_size
                scale = output_size / 480.0
                render_width = int(772 * scale)
                render_height = int(546 * scale)

                png_data = cairosvg.svg2png(
                    bytestring=svg_content.encode('utf-8'),
                    output_width=render_width,
                    output_height=render_height
                )

                # Crop to just the wheel
                img = Image.open(io.BytesIO(png_data))
                # Wheel starts at (50,50) in SVG coords, scaled
                crop_x = int(50 * scale)
                crop_y = int(50 * scale)
                crop_size = int(480 * scale)
                cropped = img.crop((crop_x, crop_y, crop_x + crop_size, crop_y + crop_size))

                # Save cropped image to bytes
                output = io.BytesIO()
                cropped.save(output, format='PNG')
                return output.getvalue()
            else:
                # Convert to PNG normally
                png_data = cairosvg.svg2png(
                    bytestring=svg_content.encode('utf-8'),
                    output_width=output_size,
                    output_height=output_size
                )
                return png_data

        except Exception as e:
            print(f"Error converting SVG to PNG: {e}")
            return None

    def generate_clean_chart_wheel(
        self,
        planets_data: Dict[str, Any],
        houses_data: Dict[str, Any],
        chart_size: int = 900,
        name: str = ""
    ) -> Image.Image:
        """
        Generate a clean chart wheel image from planet/house data (no extra info)

        Args:
            planets_data: Planet positions from chart generator
            houses_data: House cusps from chart generator
            chart_size: Output size in pixels
            name: Person's name (optional)

        Returns:
            PIL Image of the chart wheel
        """
        import math

        # Create canvas with white background
        img = Image.new('RGBA', (chart_size, chart_size), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)

        center = chart_size // 2
        outer_radius = int(chart_size * 0.45)
        zodiac_radius = int(outer_radius * 0.85)
        inner_radius = int(outer_radius * 0.65)
        planet_radius = int(outer_radius * 0.50)

        # Sign colors (fire, earth, air, water)
        sign_colors = {
            'aries': '#ff7200', 'leo': '#ff7200', 'sagittarius': '#ff7200',  # Fire
            'taurus': '#6b3d00', 'virgo': '#6b3d00', 'capricorn': '#6b3d00',  # Earth
            'gemini': '#69acf1', 'libra': '#69acf1', 'aquarius': '#69acf1',  # Air
            'cancer': '#2b4972', 'scorpio': '#2b4972', 'pisces': '#2b4972'   # Water
        }

        sign_order = ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                      'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces']

        # Load font
        try:
            symbol_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(chart_size * 0.04))
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(chart_size * 0.025))
        except:
            symbol_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Draw zodiac wheel segments (12 signs, 30 degrees each)
        for i, sign in enumerate(sign_order):
            start_angle = i * 30 - 90  # Start from top
            end_angle = start_angle + 30
            color = sign_colors.get(sign, '#cccccc')

            # Draw pie slice
            draw.pieslice(
                [center - outer_radius, center - outer_radius,
                 center + outer_radius, center + outer_radius],
                start_angle, end_angle,
                fill=color, outline='#333333', width=1
            )

            # Draw zodiac symbol at middle of segment
            mid_angle = math.radians(start_angle + 15)
            symbol_r = (outer_radius + zodiac_radius) // 2
            sx = center + int(symbol_r * math.cos(mid_angle))
            sy = center + int(symbol_r * math.sin(mid_angle))

            zodiac_sym = self.ZODIAC_SYMBOLS.get(sign, sign[:2].upper())
            bbox = draw.textbbox((0, 0), zodiac_sym, font=symbol_font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((sx - tw//2, sy - th//2), zodiac_sym, fill='white', font=symbol_font)

        # Draw inner circle (house area)
        draw.ellipse(
            [center - zodiac_radius, center - zodiac_radius,
             center + zodiac_radius, center + zodiac_radius],
            fill='#f5f5f5', outline='#333333', width=2
        )

        # Draw innermost circle
        draw.ellipse(
            [center - inner_radius, center - inner_radius,
             center + inner_radius, center + inner_radius],
            fill='#fafafa', outline='#666666', width=1
        )

        # Draw planets
        sign_to_index = {s: i for i, s in enumerate(sign_order)}
        sign_abbrev = {
            'ari': 'aries', 'tau': 'taurus', 'gem': 'gemini', 'can': 'cancer',
            'leo': 'leo', 'vir': 'virgo', 'lib': 'libra', 'sco': 'scorpio',
            'sag': 'sagittarius', 'cap': 'capricorn', 'aqu': 'aquarius', 'pis': 'pisces'
        }

        planet_positions = []
        for planet_name, pdata in planets_data.items():
            sign_raw = pdata.get('sign', '').lower()
            sign = sign_abbrev.get(sign_raw, sign_raw)
            if sign in sign_to_index:
                # Place planet at middle of its sign (simplified)
                sign_idx = sign_to_index[sign]
                angle = math.radians(sign_idx * 30 + 15 - 90)
                planet_positions.append((planet_name, angle))

        # Draw planet symbols
        for planet_name, angle in planet_positions:
            px = center + int(planet_radius * math.cos(angle))
            py = center + int(planet_radius * math.sin(angle))

            planet_sym = self.PLANET_SYMBOLS.get(planet_name, planet_name[:2].upper())
            bbox = draw.textbbox((0, 0), planet_sym, font=symbol_font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

            # Draw planet symbol
            draw.text((px - tw//2, py - th//2), planet_sym, fill='#4a0080', font=symbol_font)

        return img

    def generate_chart_mug_image(
        self,
        svg_filename: str,
        chart_id: str,
        name: str = "",
        mug_size: str = "11oz",
        background_color: str = "transparent",
        planets_data: Dict[str, Any] = None,
        houses_data: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Generate a mug-ready PNG of just the natal chart (for front of mug)

        Args:
            svg_filename: The SVG chart filename (used as fallback)
            chart_id: Unique chart identifier
            name: Person's name to display (optional)
            mug_size: "11oz" or "15oz"
            background_color: "transparent", "white", or hex color
            planets_data: Planet positions (if provided, generates clean wheel)
            houses_data: House cusps (if provided, generates clean wheel)

        Returns:
            Filename of generated PNG or None on failure
        """
        try:
            mug_full_width, mug_height = self.MUG_DIMENSIONS.get(mug_size, self.MUG_DIMENSIONS["11oz"])
            
            # Since these are separate uploads for front/back, we should use a square canvas
            # matched to the mug height. This ensures centering on the face.
            mug_width = mug_height

            # Chart will be square, maximize size to fill the height (minimal padding)
            chart_size = mug_height - 20  # Just 10px padding top and bottom

            # Read SVG and remove birth info text before rendering
            svg_path = self.images_dir / svg_filename
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()

            # Replace CSS variables with actual colors
            for css_var, color_value in self.CSS_COLOR_REPLACEMENTS.items():
                svg_content = svg_content.replace(css_var, color_value)

            # Remove the name from inside the chart (we add it centered at top)
            svg_content = re.sub(r"<text x='20' y='30'[^>]*>[^<]*</text>", "", svg_content)

            # Remove birth info text elements (lines with date, location, lat/lng, type)
            svg_content = re.sub(r"<text x='20' y='50'[^>]*>[^<]*</text>", "", svg_content)  # Info:
            svg_content = re.sub(r"<text x='20' y='62'[^>]*>[^<]*</text>", "", svg_content)  # Location
            svg_content = re.sub(r"<text x='20' y='74'[^>]*>[^<]*</text>", "", svg_content)  # Date/time
            svg_content = re.sub(r"<text x='20' y='86'[^>]*>[^<]*</text>", "", svg_content)  # Latitude
            svg_content = re.sub(r"<text x='20' y='98'[^>]*>[^<]*</text>", "", svg_content)  # Longitude
            svg_content = re.sub(r"<text x='20' y='110'[^>]*>[^<]*</text>", "", svg_content)  # Type

            # Remove bottom-left info (Tropic, Lunar phase text)
            svg_content = re.sub(r"<text x='20' y='480'[^>]*>[^<]*</text>", "", svg_content)
            svg_content = re.sub(r"<text x='20' y='494'[^>]*>[^<]*</text>", "", svg_content)
            svg_content = re.sub(r"<text x='20' y='508'[^>]*>[^<]*</text>", "", svg_content)
            svg_content = re.sub(r"<text x='20' y='522'[^>]*>[^<]*</text>", "", svg_content)

            # Remove lunar phase graphic (the g element after translate(20,518))
            svg_content = re.sub(r"<g transform='translate\(20,518\)'>[^<]*<g[^>]*>.*?</g>\s*</g>", "", svg_content, flags=re.DOTALL)

            # Remove Planet Grid section (right side planet positions list)
            svg_content = re.sub(r"<!-- Planet Grid -->.*?<!-- Houses Grid -->", "<!-- Houses Grid -->", svg_content, flags=re.DOTALL)

            # Remove Houses Grid section (cusp positions list on right)
            # Handle both formats by removing the entire translate(6x0,-20) section
            before_len = len(svg_content)
            # Find and remove the houses grid section - it's always after Houses Grid comment
            # and is the g element with translate(600,-20) or translate(650,-20)
            def remove_houses_grid(content):
                idx = content.find('<!-- Houses Grid -->')
                if idx == -1:
                    return content
                # Find the <g transform='translate(6x0,-20)'> after the comment
                search_start = idx + 20
                match = re.search(r"<g transform='translate\(6[05]0,-20\)'>", content[search_start:])
                if not match:
                    # Try with kr:node wrapper
                    match = re.search(r"<g kr:node='Houses_Grid'>", content[search_start:])
                if not match:
                    return content
                g_start = search_start + match.start()
                # Now count nested g tags to find the matching </g>
                g_count = 0
                i = g_start
                while i < len(content):
                    if content[i:i+2] == '<g':
                        g_count += 1
                    elif content[i:i+4] == '</g>':
                        g_count -= 1
                        if g_count == 0:
                            # Found matching close - remove from g_start to end of </g>
                            return content[:g_start] + content[i+4:]
                    i += 1
                return content
            svg_content = remove_houses_grid(svg_content)

            # Remove AspectGrid section (bottom right triangle)
            svg_content = re.sub(r"<!-- AspectGrid -->.*?<!-- Elements -->", "<!-- Elements -->", svg_content, flags=re.DOTALL)

            # Remove Elements section (Fire/Earth/Air/Water percentages)
            svg_content = re.sub(r"<!-- Elements -->.*?<!-- Planet Grid -->", "<!-- Planet Grid -->", svg_content, flags=re.DOTALL)

            # Also remove the elements g tag directly if comment approach didn't work
            svg_content = re.sub(r"<g transform='translate\(-30,79\)'><text[^>]*>Fire[^<]*</text>.*?</g>", "", svg_content, flags=re.DOTALL)

            # Convert cleaned SVG to PNG - crop to just the wheel
            # SVG is 772x546, wheel is centered around (290, 273) with radius ~250
            # Add padding around the wheel for planet symbols that extend beyond the wheel edge
            wheel_diameter = 520  # Wheel + padding for outer symbols
            scale = chart_size / wheel_diameter
            render_width = int(772 * scale)
            render_height = int(546 * scale)

            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=render_width,
                output_height=render_height
            )
            full_img = Image.open(io.BytesIO(png_data))

            # Crop to the wheel - wheel center is at approximately (290, 273) in SVG coords
            wheel_center_x = int(290 * scale)
            wheel_center_y = int(273 * scale)
            half_size = int(wheel_diameter * scale / 2)

            crop_left = wheel_center_x - half_size
            crop_top = wheel_center_y - half_size
            crop_right = wheel_center_x + half_size
            crop_bottom = wheel_center_y + half_size

            # Ensure we don't go out of bounds
            crop_left = max(0, crop_left)
            crop_top = max(0, crop_top)
            crop_right = min(render_width, crop_right)
            crop_bottom = min(render_height, crop_bottom)

            chart_img = full_img.crop((crop_left, crop_top, crop_right, crop_bottom))

            # Resize to desired chart_size if needed
            if chart_img.size[0] != chart_size or chart_img.size[1] != chart_size:
                chart_img = chart_img.resize((chart_size, chart_size), Image.Resampling.LANCZOS)

            # Create mug canvas
            if background_color == "transparent":
                canvas = Image.new('RGBA', (mug_width, mug_height), (0, 0, 0, 0))
            elif background_color == "white":
                canvas = Image.new('RGBA', (mug_width, mug_height), (255, 255, 255, 255))
            else:
                # Parse hex color
                hex_color = background_color.lstrip('#')
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                canvas = Image.new('RGBA', (mug_width, mug_height), (*rgb, 255))

            # Convert to RGBA
            chart_img = chart_img.convert('RGBA')

            # Center the chart on the canvas, leaving room for title at top and footer at bottom
            # Title needs ~80px, footer needs ~120px
            title_space = 80
            footer_space = 120
            available_height = mug_height - title_space - footer_space  # 1050 - 200 = 850px available

            # Resize chart if it's too tall
            if chart_size > available_height:
                chart_size = available_height
                chart_img = chart_img.resize((chart_size, chart_size), Image.Resampling.LANCZOS)

            x_offset = (mug_width - chart_size) // 2
            y_offset = title_space  # Position below title

            canvas.paste(chart_img, (x_offset, y_offset), chart_img)

            draw = ImageDraw.Draw(canvas)

            # Add name centered at top
            if name:
                try:
                    name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
                except:
                    name_font = ImageFont.load_default()

                bbox = draw.textbbox((0, 0), name, font=name_font)
                text_width = bbox[2] - bbox[0]
                # Center the name horizontally
                text_x = (mug_width - text_width) // 2
                text_y = 25

                draw.text((text_x + 2, text_y + 2), name, fill=(150, 150, 150, 200), font=name_font)
                draw.text((text_x, text_y), name, fill=(50, 50, 100, 255), font=name_font)

            # Add Sun-Rising combination at bottom (the most important relationship!)
            if planets_data and houses_data:
                # Get Sun sign
                sun_data = planets_data.get('sun', {})
                sun_sign_raw = sun_data.get('sign', '').lower()
                # Map 3-letter abbreviations to full names
                sign_map = {
                    'ari': 'aries', 'tau': 'taurus', 'gem': 'gemini', 'can': 'cancer',
                    'leo': 'leo', 'vir': 'virgo', 'lib': 'libra', 'sco': 'scorpio',
                    'sag': 'sagittarius', 'cap': 'capricorn', 'aqu': 'aquarius', 'pis': 'pisces'
                }
                sun_sign = sign_map.get(sun_sign_raw, sun_sign_raw)

                # Get Rising sign from first house cusp (house_1 or first_house key)
                first_house = houses_data.get('house_1', houses_data.get('first_house', {}))
                rising_sign_raw = first_house.get('sign', '').lower()
                rising_sign = sign_map.get(rising_sign_raw, rising_sign_raw)

                # Get the Sun-Rising combination saying
                combo_key = (sun_sign, rising_sign)
                saying = self.SUN_RISING_COMBOS.get(combo_key, '')

                if saying and sun_sign and rising_sign:
                    try:
                        combo_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                        saying_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
                    except:
                        combo_font = ImageFont.load_default()
                        saying_font = ImageFont.load_default()

                    # Sun/Rising label centered at bottom
                    sun_symbol = self.ZODIAC_SYMBOLS.get(sun_sign, '')
                    rising_symbol = self.ZODIAC_SYMBOLS.get(rising_sign, '')
                    combo_label = f"{sun_sign.title()} {sun_symbol} Sun, {rising_sign.title()} {rising_symbol} Rising"

                    bbox = draw.textbbox((0, 0), combo_label, font=combo_font)
                    label_width = bbox[2] - bbox[0]
                    draw.text(((mug_width - label_width) // 2, mug_height - 90), combo_label,
                             fill=(60, 60, 100, 255), font=combo_font)

                    # The saying centered below it
                    bbox2 = draw.textbbox((0, 0), f'"{saying}"', font=saying_font)
                    saying_width = bbox2[2] - bbox2[0]
                    draw.text(((mug_width - saying_width) // 2, mug_height - 50), f'"{saying}"',
                             fill=(100, 100, 120, 255), font=saying_font)

            # Save the image
            output_filename = f"mug_chart_{chart_id}.png"
            output_path = self.images_dir / output_filename
            canvas.save(str(output_path), 'PNG', dpi=(300, 300))

            return output_filename

        except Exception as e:
            print(f"Error generating chart mug image: {e}")
            return None

    def generate_wordcloud_mug_image(
        self,
        wordcloud_filename: str,
        chart_id: str,
        name: str = "",
        mug_size: str = "11oz",
        background_color: str = "transparent"
    ) -> Optional[str]:
        """
        Generate a mug-ready PNG from the existing wordcloud (for back of mug)

        Args:
            wordcloud_filename: The existing wordcloud filename
            chart_id: Unique chart identifier
            name: Person's name (optional)
            mug_size: "11oz" or "15oz"
            background_color: "transparent", "white", or hex color

        Returns:
            Filename of generated PNG or None on failure
        """
        try:
            mug_full_width, mug_height = self.MUG_DIMENSIONS.get(mug_size, self.MUG_DIMENSIONS["11oz"])
            
            # Use square canvas for separate face upload
            mug_width = mug_height

            # Create mug canvas
            if background_color == "transparent":
                canvas = Image.new('RGBA', (mug_width, mug_height), (0, 0, 0, 0))
            elif background_color == "white":
                canvas = Image.new('RGBA', (mug_width, mug_height), (255, 255, 255, 255))
            else:
                hex_color = background_color.lstrip('#')
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                canvas = Image.new('RGBA', (mug_width, mug_height), (*rgb, 255))

            # Load the existing wordcloud
            wordcloud_path = self.images_dir / wordcloud_filename
            if not wordcloud_path.exists():
                print(f"Wordcloud file not found: {wordcloud_path}")
                return None

            wordcloud_img = Image.open(str(wordcloud_path)).convert('RGBA')

            # Calculate scaling to fit the mug dimensions while maintaining aspect ratio
            # Reserve space for footer text at bottom
            padding = 30
            footer_space = 90 if name else 0
            available_height = mug_height - padding - footer_space
            available_width = mug_width - (2 * padding)

            # Calculate scale factor
            wc_width, wc_height = wordcloud_img.size
            scale_w = available_width / wc_width
            scale_h = available_height / wc_height
            scale = min(scale_w, scale_h)

            # Resize wordcloud
            new_width = int(wc_width * scale)
            new_height = int(wc_height * scale)
            wordcloud_resized = wordcloud_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Center the wordcloud horizontally and vertically in available space
            x_offset = (mug_width - new_width) // 2
            y_offset = (available_height - new_height) // 2 + padding

            # Paste wordcloud onto canvas
            canvas.paste(wordcloud_resized, (x_offset, y_offset), wordcloud_resized)

            # Add name if provided
            if name:
                draw = ImageDraw.Draw(canvas)
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
                except:
                    font = ImageFont.load_default()

                title = f"{name}'s Chart Essence"
                bbox = draw.textbbox((0, 0), title, font=font)
                text_width = bbox[2] - bbox[0]
                text_x = (mug_width - text_width) // 2
                text_y = mug_height - 70

                # Draw text with slight shadow
                draw.text((text_x + 2, text_y + 2), title, fill=(100, 100, 100, 200), font=font)
                draw.text((text_x, text_y), title, fill=(50, 50, 100, 255), font=font)

            # Save the image
            output_filename = f"mug_wordcloud_{chart_id}.png"
            output_path = self.images_dir / output_filename
            canvas.save(str(output_path), 'PNG', dpi=(300, 300))

            return output_filename

        except Exception as e:
            print(f"Error generating wordcloud mug image: {e}")
            return None

    def generate_mug_set(
        self,
        svg_filename: str,
        wordcloud_filename: str,
        chart_id: str,
        name: str = "",
        mug_size: str = "11oz",
        background_color: str = "transparent"
    ) -> Dict[str, Optional[str]]:
        """
        Generate both mug images (chart and wordcloud) as a set

        Returns:
            Dictionary with 'chart_image' and 'wordcloud_image' filenames
        """
        chart_filename = self.generate_chart_mug_image(
            svg_filename=svg_filename,
            chart_id=chart_id,
            name=name,
            mug_size=mug_size,
            background_color=background_color
        )

        wordcloud_mug_filename = self.generate_wordcloud_mug_image(
            wordcloud_filename=wordcloud_filename,
            chart_id=chart_id,
            name=name,
            mug_size=mug_size,
            background_color=background_color
        )

        return {
            "chart_image": chart_filename,
            "wordcloud_image": wordcloud_mug_filename
        }

    def generate_planets_mug_image(
        self,
        planets_data: Dict[str, Any],
        chart_id: str,
        name: str = "",
        mug_size: str = "11oz",
        background_color: str = "white"
    ) -> Optional[str]:
        """
        Generate a mug-ready PNG showing planet positions with symbols

        Args:
            planets_data: Dictionary of planet data from chart generator
            chart_id: Unique chart identifier
            name: Person's name (optional)
            mug_size: "11oz" or "15oz"
            background_color: "white" or hex color

        Returns:
            Filename of generated PNG or None on failure
        """
        try:
            # Use full width for readable standalone image (not for mug)
            mug_width, mug_height = self.MUG_DIMENSIONS.get(mug_size, self.MUG_DIMENSIONS["11oz"])

            # Create canvas with proper background color handling
            if background_color in ("white", "transparent", None, ""):
                canvas = Image.new('RGBA', (mug_width, mug_height), (255, 255, 255, 255))
            elif background_color.startswith('#') and len(background_color) == 7:
                hex_color = background_color.lstrip('#')
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                canvas = Image.new('RGBA', (mug_width, mug_height), (*rgb, 255))
            else:
                canvas = Image.new('RGBA', (mug_width, mug_height), (255, 255, 255, 255))

            draw = ImageDraw.Draw(canvas)

            # Load fonts - larger for readability
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
                planet_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
                meaning_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
                symbol_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44)
            except:
                title_font = ImageFont.load_default()
                planet_font = ImageFont.load_default()
                meaning_font = ImageFont.load_default()
                symbol_font = ImageFont.load_default()

            # Sign name mapping
            sign_mapping = {
                'ari': 'Aries', 'tau': 'Taurus', 'gem': 'Gemini', 'can': 'Cancer',
                'leo': 'Leo', 'vir': 'Virgo', 'lib': 'Libra', 'sco': 'Scorpio',
                'sag': 'Sagittarius', 'cap': 'Capricorn', 'aqu': 'Aquarius', 'pis': 'Pisces'
            }

            # Planet meanings combined with sign expression
            planet_meanings = {
                'sun': 'Core identity',
                'moon': 'Emotions & needs',
                'mercury': 'Mind & communication',
                'venus': 'Love & values',
                'mars': 'Drive & action',
                'jupiter': 'Growth & luck',
                'saturn': 'Discipline & limits',
                'uranus': 'Innovation & change',
                'neptune': 'Dreams & intuition',
                'pluto': 'Power & transformation'
            }

            # Planet-in-sign specific interpretations
            planet_sign_meanings = {
                ('sun', 'aries'): 'bold leader, pioneer spirit',
                ('sun', 'taurus'): 'steady, reliable, sensual',
                ('sun', 'gemini'): 'curious, versatile, witty',
                ('sun', 'cancer'): 'nurturing, protective, emotional',
                ('sun', 'leo'): 'confident, creative, generous',
                ('sun', 'virgo'): 'analytical, helpful, perfectionist',
                ('sun', 'libra'): 'diplomatic, charming, balanced',
                ('sun', 'scorpio'): 'intense, powerful, transformative',
                ('sun', 'sagittarius'): 'adventurous, optimistic, free',
                ('sun', 'capricorn'): 'ambitious, disciplined, achieving',
                ('sun', 'aquarius'): 'original, humanitarian, independent',
                ('sun', 'pisces'): 'compassionate, intuitive, dreamy',
                ('moon', 'aries'): 'passionate emotions, quick reactions',
                ('moon', 'taurus'): 'steady feelings, needs security',
                ('moon', 'gemini'): 'changeable moods, needs variety',
                ('moon', 'cancer'): 'deep emotions, very nurturing',
                ('moon', 'leo'): 'dramatic feelings, needs attention',
                ('moon', 'virgo'): 'analytical emotions, helpful nature',
                ('moon', 'libra'): 'needs harmony, avoids conflict',
                ('moon', 'scorpio'): 'intense feelings, emotionally deep',
                ('moon', 'sagittarius'): 'optimistic mood, needs freedom',
                ('moon', 'capricorn'): 'controlled emotions, responsible',
                ('moon', 'aquarius'): 'detached feelings, needs space',
                ('moon', 'pisces'): 'empathic, absorbs others\' feelings',
                ('mercury', 'aries'): 'quick thinker, direct speaker',
                ('mercury', 'taurus'): 'deliberate mind, practical ideas',
                ('mercury', 'gemini'): 'brilliant communicator, curious',
                ('mercury', 'cancer'): 'intuitive thinking, good memory',
                ('mercury', 'leo'): 'dramatic expression, confident speech',
                ('mercury', 'virgo'): 'precise mind, analytical thinker',
                ('mercury', 'libra'): 'balanced views, diplomatic words',
                ('mercury', 'scorpio'): 'probing mind, sees hidden truths',
                ('mercury', 'sagittarius'): 'big-picture thinking, blunt',
                ('mercury', 'capricorn'): 'strategic mind, serious tone',
                ('mercury', 'aquarius'): 'innovative ideas, unique views',
                ('mercury', 'pisces'): 'imaginative mind, poetic speech',
                ('venus', 'aries'): 'passionate love, bold in romance',
                ('venus', 'taurus'): 'sensual, loyal, loves comfort',
                ('venus', 'gemini'): 'flirtatious, loves variety',
                ('venus', 'cancer'): 'nurturing love, emotionally devoted',
                ('venus', 'leo'): 'dramatic romance, generous lover',
                ('venus', 'virgo'): 'devoted, shows love through service',
                ('venus', 'libra'): 'romantic idealist, loves beauty',
                ('venus', 'scorpio'): 'intense passion, all-or-nothing',
                ('venus', 'sagittarius'): 'adventurous love, needs freedom',
                ('venus', 'capricorn'): 'serious love, loyal partner',
                ('venus', 'aquarius'): 'unconventional love, needs space',
                ('venus', 'pisces'): 'romantic dreamer, selfless love',
                ('mars', 'aries'): 'powerful drive, competitive nature',
                ('mars', 'taurus'): 'persistent effort, steady force',
                ('mars', 'gemini'): 'mental energy, versatile actions',
                ('mars', 'cancer'): 'protective drive, indirect approach',
                ('mars', 'leo'): 'confident action, dramatic energy',
                ('mars', 'virgo'): 'precise actions, works hard',
                ('mars', 'libra'): 'balanced approach, fights for fairness',
                ('mars', 'scorpio'): 'powerful will, intense drive',
                ('mars', 'sagittarius'): 'adventurous energy, bold moves',
                ('mars', 'capricorn'): 'strategic action, ambitious drive',
                ('mars', 'aquarius'): 'unconventional methods, rebel energy',
                ('mars', 'pisces'): 'inspired action, subtle approach',
                ('jupiter', 'aries'): 'bold expansion, lucky pioneer',
                ('jupiter', 'taurus'): 'material growth, steady luck',
                ('jupiter', 'gemini'): 'intellectual growth, many interests',
                ('jupiter', 'cancer'): 'emotional wisdom, family luck',
                ('jupiter', 'leo'): 'generous spirit, creative expansion',
                ('jupiter', 'virgo'): 'growth through service, practical wisdom',
                ('jupiter', 'libra'): 'social expansion, luck in partnerships',
                ('jupiter', 'scorpio'): 'deep wisdom, transformative growth',
                ('jupiter', 'sagittarius'): 'natural philosopher, very lucky',
                ('jupiter', 'capricorn'): 'disciplined growth, earned success',
                ('jupiter', 'aquarius'): 'humanitarian vision, social luck',
                ('jupiter', 'pisces'): 'spiritual wisdom, compassionate',
                ('saturn', 'aries'): 'learns patience, disciplined action',
                ('saturn', 'taurus'): 'builds security, patient builder',
                ('saturn', 'gemini'): 'structured thinking, focused mind',
                ('saturn', 'cancer'): 'emotional lessons, family duties',
                ('saturn', 'leo'): 'learns humility, earns recognition',
                ('saturn', 'virgo'): 'perfectionist, mastery through work',
                ('saturn', 'libra'): 'relationship lessons, fair judge',
                ('saturn', 'scorpio'): 'faces fears, deep transformation',
                ('saturn', 'sagittarius'): 'structured beliefs, wisdom earned',
                ('saturn', 'capricorn'): 'natural authority, ambitious',
                ('saturn', 'aquarius'): 'social responsibility, reforms',
                ('saturn', 'pisces'): 'spiritual lessons, creative discipline',
                ('uranus', 'aries'): 'revolutionary pioneer, sudden starts',
                ('uranus', 'taurus'): 'changes values, new resources',
                ('uranus', 'gemini'): 'brilliant ideas, restless mind',
                ('uranus', 'cancer'): 'family disruptions, emotional freedom',
                ('uranus', 'leo'): 'creative rebel, unique expression',
                ('uranus', 'virgo'): 'innovative methods, health changes',
                ('uranus', 'libra'): 'relationship revolution, new social norms',
                ('uranus', 'scorpio'): 'deep transformation, power shifts',
                ('uranus', 'sagittarius'): 'belief revolution, freedom seeker',
                ('uranus', 'capricorn'): 'structural change, new systems',
                ('uranus', 'aquarius'): 'true visionary, radical change',
                ('uranus', 'pisces'): 'spiritual awakening, collective shift',
                ('neptune', 'aries'): 'inspired action, spiritual warrior',
                ('neptune', 'taurus'): 'artistic values, inspired beauty',
                ('neptune', 'gemini'): 'imaginative ideas, poetic mind',
                ('neptune', 'cancer'): 'psychic sensitivity, family ideals',
                ('neptune', 'leo'): 'creative dreams, artistic expression',
                ('neptune', 'virgo'): 'healing service, practical mysticism',
                ('neptune', 'libra'): 'idealistic love, artistic beauty',
                ('neptune', 'scorpio'): 'psychic depth, hidden mysteries',
                ('neptune', 'sagittarius'): 'spiritual seeking, inspired vision',
                ('neptune', 'capricorn'): 'practical dreams, dissolving structures',
                ('neptune', 'aquarius'): 'collective dreams, humanitarian ideals',
                ('neptune', 'pisces'): 'deeply spiritual, boundless compassion',
                ('pluto', 'aries'): 'transformative power, rebirth of self',
                ('pluto', 'taurus'): 'transforms values, material rebirth',
                ('pluto', 'gemini'): 'transforms thinking, powerful ideas',
                ('pluto', 'cancer'): 'family transformation, emotional power',
                ('pluto', 'leo'): 'creative power, transforms expression',
                ('pluto', 'virgo'): 'transforms work, health regeneration',
                ('pluto', 'libra'): 'relationship power, transforms partnerships',
                ('pluto', 'scorpio'): 'ultimate transformer, profound depth',
                ('pluto', 'sagittarius'): 'transforms beliefs, truth seeker',
                ('pluto', 'capricorn'): 'structural transformation, power shifts',
                ('pluto', 'aquarius'): 'social transformation, collective power',
                ('pluto', 'pisces'): 'spiritual transformation, dissolving ego',
            }

            # Draw title centered at top
            title = f"{name}'s Planets" if name else "Planetary Positions"
            bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = bbox[2] - bbox[0]
            draw.text(((mug_width - title_width) // 2, 15), title, fill=(50, 50, 100, 255), font=title_font)

            # Layout: 2 columns, 5 rows for 10 planets - compact for 1050px square
            planets_order = ['sun', 'moon', 'mercury', 'venus', 'mars',
                           'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']

            # Two column layout with minimal margins
            margin = 30
            col_width = (mug_width - 2 * margin) // 2
            start_y = 80
            row_height = (mug_height - start_y - 20) // 5  # 5 rows

            for idx, planet in enumerate(planets_order):
                if planet not in planets_data:
                    continue

                data = planets_data[planet]
                col = idx % 2
                row = idx // 2

                x_base = margin + col * col_width
                y_base = start_y + row * row_height

                # Get planet symbol and sign
                planet_symbol = self.PLANET_SYMBOLS.get(planet, "")
                sign_raw = data.get("sign", "").lower()
                sign_name = sign_mapping.get(sign_raw, sign_raw.title())
                sign_key = sign_name.lower()
                zodiac_symbol = self.ZODIAC_SYMBOLS.get(sign_key, "")

                # Row 1: Symbol + Planet in Sign
                draw.text((x_base, y_base), planet_symbol, fill=(100, 50, 150, 255), font=symbol_font)

                planet_text = f"{planet.title()} in {sign_name} {zodiac_symbol}"
                if data.get("retrograde", False):
                    planet_text += " ℞"
                draw.text((x_base + 45, y_base), planet_text, fill=(50, 50, 80, 255), font=planet_font)

                # Row 2: Planet meaning only (skip planet-in-sign to save space)
                meaning = planet_meanings.get(planet, '')
                draw.text((x_base + 45, y_base + 40), meaning, fill=(100, 100, 100, 255), font=meaning_font)

                # Row 3: Brief planet-in-sign interpretation
                planet_sign_key = (planet, sign_key)
                interpretation = planet_sign_meanings.get(planet_sign_key, '')
                if interpretation:
                    draw.text((x_base + 45, y_base + 72), interpretation, fill=(130, 130, 130, 255), font=meaning_font)

            # Save the image
            output_filename = f"mug_planets_{chart_id}.png"
            output_path = self.images_dir / output_filename
            canvas.save(str(output_path), 'PNG', dpi=(300, 300))

            return output_filename

        except Exception as e:
            print(f"Error generating planets mug image: {e}")
            return None

    def generate_aspects_mug_image(
        self,
        aspects_data: list,
        chart_id: str,
        name: str = "",
        mug_size: str = "11oz",
        background_color: str = "white"
    ) -> Optional[str]:
        """
        Generate a mug-ready PNG showing major aspects

        Args:
            aspects_data: List of aspect data from interpreter
            chart_id: Unique chart identifier
            name: Person's name (optional)
            mug_size: "11oz" or "15oz"
            background_color: "white" or hex color

        Returns:
            Filename of generated PNG or None on failure
        """
        try:
            _, mug_height = self.MUG_DIMENSIONS.get(mug_size, self.MUG_DIMENSIONS["11oz"])
            # Use compact width (square) for individual panel placement on mug
            mug_width = mug_height

            # Create canvas with proper background color handling
            if background_color in ("white", "transparent", None, ""):
                canvas = Image.new('RGBA', (mug_width, mug_height), (255, 255, 255, 255))
            elif background_color.startswith('#') and len(background_color) == 7:
                hex_color = background_color.lstrip('#')
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                canvas = Image.new('RGBA', (mug_width, mug_height), (*rgb, 255))
            else:
                canvas = Image.new('RGBA', (mug_width, mug_height), (255, 255, 255, 255))

            draw = ImageDraw.Draw(canvas)

            # Load fonts
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
                aspect_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                meaning_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
                symbol_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44)
            except:
                title_font = ImageFont.load_default()
                aspect_font = ImageFont.load_default()
                meaning_font = ImageFont.load_default()
                symbol_font = ImageFont.load_default()

            # Draw title centered at top
            title = f"{name}'s Aspects" if name else "Major Aspects"
            bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = bbox[2] - bbox[0]
            draw.text(((mug_width - title_width) // 2, 25), title, fill=(50, 50, 100, 255), font=title_font)

            # Filter to major aspects between major planets only
            major_aspects = ['conjunction', 'opposition', 'trine', 'square', 'sextile']
            major_planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
            max_aspects = 10

            # Filter aspects: major aspect types between major planets only
            filtered_aspects = []
            for a in aspects_data:
                # Handle both data formats
                if "planets" in a:
                    parts = a.get("planets", "").split()
                    if len(parts) >= 3:
                        p1, asp, p2 = parts[0].lower(), parts[1].lower(), parts[2].lower()
                    else:
                        continue
                else:
                    p1 = a.get("planet1", "").lower()
                    p2 = a.get("planet2", "").lower()
                    asp = a.get("aspect", "").lower()

                # Only include if major aspect between major planets
                if asp in major_aspects and p1 in major_planets and p2 in major_planets:
                    # Prioritize by aspect type and orb
                    orb = a.get("orb", 10)
                    filtered_aspects.append((orb, a))

            # Sort by tightest orb (most exact aspects first)
            filtered_aspects.sort(key=lambda x: x[0])
            display_aspects = [a[1] for a in filtered_aspects[:max_aspects]]

            # Layout: 2 columns, 5 rows - compact for 1050px square
            margin = 30
            col_width = (mug_width - 2 * margin) // 2
            start_y = 80
            row_height = (mug_height - start_y - 20) // 5

            for idx, aspect in enumerate(display_aspects):
                col = idx % 2
                row = idx // 2

                x_base = margin + col * col_width
                y_base = start_y + row * row_height

                # Parse aspect info - handle both formats:
                # Format 1: {"planets": "Sun conjunction Moon", ...}
                # Format 2: {"planet1": "sun", "planet2": "moon", "aspect": "conjunction", ...}
                if "planets" in aspect:
                    planets_str = aspect.get("planets", "")
                    parts = planets_str.split()
                    if len(parts) >= 3:
                        planet1 = parts[0].lower()
                        aspect_type = parts[1].lower()
                        planet2 = parts[2].lower()
                    else:
                        continue
                elif "planet1" in aspect:
                    planet1 = aspect.get("planet1", "").lower()
                    planet2 = aspect.get("planet2", "").lower()
                    aspect_type = aspect.get("aspect", "").lower()
                else:
                    continue

                if planet1 and planet2 and aspect_type:

                    # Get symbols
                    p1_symbol = self.PLANET_SYMBOLS.get(planet1, planet1[:2].upper())
                    p2_symbol = self.PLANET_SYMBOLS.get(planet2, planet2[:2].upper())
                    aspect_symbol = self.ASPECT_SYMBOLS.get(aspect_type, aspect_type[:3])

                    # Get color for aspect type
                    aspect_color = self.ASPECT_COLORS.get(aspect_type, "#333333")
                    hex_c = aspect_color.lstrip('#')
                    rgb_color = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4)) + (255,)

                    # Get planet-pair specific meaning
                    meaning = self._get_aspect_meaning(planet1, planet2, aspect_type)

                    # Row 1: Symbols + aspect name
                    draw.text((x_base, y_base), p1_symbol, fill=(100, 50, 150, 255), font=symbol_font)
                    draw.text((x_base + 50, y_base), aspect_symbol, fill=rgb_color, font=symbol_font)
                    draw.text((x_base + 100, y_base), p2_symbol, fill=(100, 50, 150, 255), font=symbol_font)

                    # Aspect name next to symbols
                    desc = f"{planet1.title()} {aspect_type} {planet2.title()}"
                    draw.text((x_base + 155, y_base + 5), desc, fill=(60, 60, 80, 255), font=aspect_font)

                    # Row 2: Meaning
                    if meaning:
                        draw.text((x_base + 50, y_base + 48), meaning, fill=(100, 100, 100, 255), font=meaning_font)

                    # Row 3: Aspect type description
                    aspect_desc = {
                        'conjunction': 'energies merged',
                        'opposition': 'tension & awareness',
                        'trine': 'natural flow',
                        'square': 'growth through challenge',
                        'sextile': 'opportunity'
                    }.get(aspect_type, '')
                    if aspect_desc:
                        draw.text((x_base + 50, y_base + 82), aspect_desc, fill=(130, 130, 130, 255), font=meaning_font)

            # Save the image
            output_filename = f"mug_aspects_{chart_id}.png"
            output_path = self.images_dir / output_filename
            canvas.save(str(output_path), 'PNG', dpi=(300, 300))

            return output_filename

        except Exception as e:
            print(f"Error generating aspects mug image: {e}")
            return None

    def _get_planet_in_house_meaning(self, planet: str, house: int) -> str:
        """Get interpretation for a planet in a specific house"""
        meanings = {
            # Sun placements
            ('sun', 1): "Identity shines through your presence",
            ('sun', 2): "Self-worth tied to what you build",
            ('sun', 3): "Identity expressed through ideas",
            ('sun', 4): "Home and family define you",
            ('sun', 5): "Creative self-expression is vital",
            ('sun', 6): "Purpose through work and service",
            ('sun', 7): "Identity through partnerships",
            ('sun', 8): "Transformation is your path",
            ('sun', 9): "Seeking meaning through exploration",
            ('sun', 10): "Career and status are central",
            ('sun', 11): "Purpose through community",
            ('sun', 12): "Inner world is your strength",
            # Moon placements
            ('moon', 1): "Emotions on display, sensitive presence",
            ('moon', 2): "Emotional security through resources",
            ('moon', 3): "Feelings expressed through words",
            ('moon', 4): "Deep need for home and roots",
            ('moon', 5): "Heart in creative expression",
            ('moon', 6): "Nurturing through daily care",
            ('moon', 7): "Emotional fulfillment in partnership",
            ('moon', 8): "Intense emotional depths",
            ('moon', 9): "Feelings expand through learning",
            ('moon', 10): "Public life affects emotions",
            ('moon', 11): "Nurtured by friendships",
            ('moon', 12): "Rich inner emotional life",
            # Mercury placements
            ('mercury', 1): "Quick mind, articulate presence",
            ('mercury', 2): "Thinks about money and values",
            ('mercury', 3): "Natural communicator, curious",
            ('mercury', 4): "Mind on family matters",
            ('mercury', 5): "Creative thinking, playful ideas",
            ('mercury', 6): "Analytical approach to work",
            ('mercury', 7): "Communication key in relationships",
            ('mercury', 8): "Probing, investigative mind",
            ('mercury', 9): "Philosophical thinker",
            ('mercury', 10): "Career in communication",
            ('mercury', 11): "Ideas shared with groups",
            ('mercury', 12): "Intuitive, private thoughts",
            # Venus placements
            ('venus', 1): "Charming, attractive presence",
            ('venus', 2): "Values comfort and beauty",
            ('venus', 3): "Graceful communication style",
            ('venus', 4): "Love of home, beautiful spaces",
            ('venus', 5): "Romantic, creative pleasures",
            ('venus', 6): "Harmony in daily routines",
            ('venus', 7): "Partnership is essential",
            ('venus', 8): "Intense, transformative love",
            ('venus', 9): "Love of travel and learning",
            ('venus', 10): "Success through charm",
            ('venus', 11): "Friendships bring joy",
            ('venus', 12): "Secret or spiritual love",
            # Mars placements
            ('mars', 1): "Bold, assertive presence",
            ('mars', 2): "Driven to earn and acquire",
            ('mars', 3): "Direct, forceful communication",
            ('mars', 4): "Energy focused on home",
            ('mars', 5): "Passionate, competitive creativity",
            ('mars', 6): "Hard worker, active routines",
            ('mars', 7): "Assertive in partnerships",
            ('mars', 8): "Powerful transformative drive",
            ('mars', 9): "Fights for beliefs",
            ('mars', 10): "Ambitious career drive",
            ('mars', 11): "Active in group causes",
            ('mars', 12): "Hidden strength and anger",
            # Jupiter placements
            ('jupiter', 1): "Optimistic, generous presence",
            ('jupiter', 2): "Lucky with money, abundance",
            ('jupiter', 3): "Big ideas, loves learning",
            ('jupiter', 4): "Blessed home life",
            ('jupiter', 5): "Joy through creativity, lucky in love",
            ('jupiter', 6): "Growth through service",
            ('jupiter', 7): "Fortunate partnerships",
            ('jupiter', 8): "Benefits through others' resources",
            ('jupiter', 9): "Born philosopher, loves travel",
            ('jupiter', 10): "Success and recognition",
            ('jupiter', 11): "Many friends, big dreams",
            ('jupiter', 12): "Spiritual protection, inner faith",
            # Saturn placements
            ('saturn', 1): "Serious, responsible presence",
            ('saturn', 2): "Works hard for security",
            ('saturn', 3): "Careful, structured thinking",
            ('saturn', 4): "Lessons through family",
            ('saturn', 5): "Discipline in creativity",
            ('saturn', 6): "Mastery through hard work",
            ('saturn', 7): "Commitment in partnerships",
            ('saturn', 8): "Facing fears, deep lessons",
            ('saturn', 9): "Structured beliefs, late education",
            ('saturn', 10): "Career takes time, lasting success",
            ('saturn', 11): "Serious about goals",
            ('saturn', 12): "Solitude brings wisdom",
            # Uranus placements
            ('uranus', 1): "Unique, unconventional presence",
            ('uranus', 2): "Unusual approach to money",
            ('uranus', 3): "Original thinker, inventive",
            ('uranus', 4): "Unconventional home life",
            ('uranus', 5): "Creative genius, unique expression",
            ('uranus', 6): "Innovative work methods",
            ('uranus', 7): "Freedom in relationships",
            ('uranus', 8): "Sudden transformations",
            ('uranus', 9): "Revolutionary beliefs",
            ('uranus', 10): "Unusual career path",
            ('uranus', 11): "Visionary, ahead of time",
            ('uranus', 12): "Awakening through solitude",
            # Neptune placements
            ('neptune', 1): "Dreamy, artistic presence",
            ('neptune', 2): "Idealistic about money",
            ('neptune', 3): "Imaginative communication",
            ('neptune', 4): "Idealized home, family secrets",
            ('neptune', 5): "Artistic creativity, romantic dreams",
            ('neptune', 6): "Service with compassion",
            ('neptune', 7): "Idealistic in love",
            ('neptune', 8): "Psychic sensitivity, spiritual depth",
            ('neptune', 9): "Spiritual seeker, visionary",
            ('neptune', 10): "Artistic or healing career",
            ('neptune', 11): "Dreams for humanity",
            ('neptune', 12): "Deep spirituality, intuition",
            # Pluto placements
            ('pluto', 1): "Intense, powerful presence",
            ('pluto', 2): "Transforms relationship with money",
            ('pluto', 3): "Penetrating mind, powerful words",
            ('pluto', 4): "Family transformation, deep roots",
            ('pluto', 5): "Intense creative power",
            ('pluto', 6): "Transforms through work",
            ('pluto', 7): "Powerful partnerships",
            ('pluto', 8): "Master of transformation",
            ('pluto', 9): "Profound beliefs, seeks truth",
            ('pluto', 10): "Power in career, influence",
            ('pluto', 11): "Transforms groups, powerful vision",
            ('pluto', 12): "Deep unconscious power",
        }
        return meanings.get((planet.lower(), house), "")

    def generate_houses_mug_image(
        self,
        planets_data: Dict[str, Any],
        houses_data: Dict[str, Any],
        chart_id: str,
        name: str = "",
        mug_size: str = "11oz",
        background_color: str = "white"
    ) -> Optional[str]:
        """
        Generate a mug-ready PNG showing planet placements in houses with interpretations

        Args:
            planets_data: Dictionary of planet data (includes house placement)
            houses_data: Dictionary of house cusp data
            chart_id: Unique chart identifier
            name: Person's name (optional)
            mug_size: "11oz" or "15oz"
            background_color: "white" or hex color

        Returns:
            Filename of generated PNG or None on failure
        """
        try:
            mug_full_width, mug_height = self.MUG_DIMENSIONS.get(mug_size, self.MUG_DIMENSIONS["11oz"])

            # Use square canvas for separate face upload
            mug_width = mug_height

            # Create canvas with proper background color handling
            if background_color in ("white", "transparent", None, ""):
                canvas = Image.new('RGBA', (mug_width, mug_height), (255, 255, 255, 255))
            elif background_color.startswith('#') and len(background_color) == 7:
                hex_color = background_color.lstrip('#')
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                canvas = Image.new('RGBA', (mug_width, mug_height), (*rgb, 255))
            else:
                canvas = Image.new('RGBA', (mug_width, mug_height), (255, 255, 255, 255))

            draw = ImageDraw.Draw(canvas)

            # Load fonts
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
                planet_name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
                house_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
                meaning_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
                symbol_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
            except:
                title_font = ImageFont.load_default()
                planet_name_font = ImageFont.load_default()
                house_font = ImageFont.load_default()
                meaning_font = ImageFont.load_default()
                symbol_font = ImageFont.load_default()

            # House names for display
            house_names = {
                1: "1st House (Self)",
                2: "2nd House (Money)",
                3: "3rd House (Mind)",
                4: "4th House (Home)",
                5: "5th House (Joy)",
                6: "6th House (Work)",
                7: "7th House (Partners)",
                8: "8th House (Depth)",
                9: "9th House (Growth)",
                10: "10th House (Career)",
                11: "11th House (Friends)",
                12: "12th House (Spirit)"
            }

            house_name_to_num = {
                'first_house': 1, 'second_house': 2, 'third_house': 3, 'fourth_house': 4,
                'fifth_house': 5, 'sixth_house': 6, 'seventh_house': 7, 'eighth_house': 8,
                'ninth_house': 9, 'tenth_house': 10, 'eleventh_house': 11, 'twelfth_house': 12
            }

            # Collect planet placements with meanings
            placements = []
            planets_order = ['sun', 'moon', 'mercury', 'venus', 'mars',
                           'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']

            for planet_name in planets_order:
                if planet_name not in planets_data:
                    continue
                pdata = planets_data[planet_name]
                house_raw = pdata.get('house', '').lower().replace(' ', '_')
                house_num = house_name_to_num.get(house_raw)
                if house_num:
                    meaning = self._get_planet_in_house_meaning(planet_name, house_num)
                    if meaning:
                        placements.append({
                            'planet': planet_name,
                            'symbol': self.PLANET_SYMBOLS.get(planet_name, ''),
                            'house_num': house_num,
                            'house_name': house_names[house_num],
                            'meaning': meaning
                        })

            # Draw title centered at top
            title = f"{name}'s House Placements" if name else "House Placements"
            bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = bbox[2] - bbox[0]
            draw.text(((mug_width - title_width) // 2, 25), title, fill=(50, 50, 100, 255), font=title_font)

            # Layout: 2 columns, 5 rows for 10 planets - center content within square canvas
            margin = 20
            content_width = mug_width - (2 * margin)
            col_width = content_width // 2
            start_y = 100
            row_height = (mug_height - start_y - 40) // 5

            for idx, placement in enumerate(placements[:10]):
                col = idx % 2
                row = idx // 2

                x_base = margin + col * col_width + 10
                y_base = start_y + row * row_height

                # Draw planet symbol
                draw.text((x_base, y_base), placement['symbol'], fill=(100, 50, 150, 255), font=symbol_font)

                # Draw planet name in house
                planet_text = f"{placement['planet'].title()} in {placement['house_name']}"
                draw.text((x_base + 60, y_base), planet_text, fill=(60, 60, 80, 255), font=planet_name_font)

                # Draw interpretation
                draw.text((x_base + 60, y_base + 48), placement['meaning'], fill=(100, 100, 100, 255), font=meaning_font)

            # Save the image
            output_filename = f"mug_houses_{chart_id}.png"
            output_path = self.images_dir / output_filename
            canvas.save(str(output_path), 'PNG', dpi=(300, 300))

            return output_filename

        except Exception as e:
            print(f"Error generating houses mug image: {e}")
            return None

    def generate_full_mug_set(
        self,
        svg_filename: str,
        wordcloud_filename: str,
        planets_data: Dict[str, Any],
        aspects_data: list,
        chart_id: str,
        name: str = "",
        mug_size: str = "11oz",
        background_color: str = "white",
        houses_data: Dict[str, Any] = None
    ) -> Dict[str, Optional[str]]:
        """
        Generate all 5 mug images for customer to choose from

        Returns:
            Dictionary with 'chart_image', 'wordcloud_image', 'planets_image', 'aspects_image', 'houses_image' filenames
        """
        chart_filename = self.generate_chart_mug_image(
            svg_filename=svg_filename,
            chart_id=chart_id,
            name=name,
            mug_size=mug_size,
            background_color=background_color,
            planets_data=planets_data,
            houses_data=houses_data
        )

        wordcloud_filename_out = self.generate_wordcloud_mug_image(
            wordcloud_filename=wordcloud_filename,
            chart_id=chart_id,
            name=name,
            mug_size=mug_size,
            background_color=background_color
        )

        planets_filename = self.generate_planets_mug_image(
            planets_data=planets_data,
            chart_id=chart_id,
            name=name,
            mug_size=mug_size,
            background_color=background_color
        )

        aspects_filename = self.generate_aspects_mug_image(
            aspects_data=aspects_data,
            chart_id=chart_id,
            name=name,
            mug_size=mug_size,
            background_color=background_color
        )

        houses_filename = self.generate_houses_mug_image(
            planets_data=planets_data,
            houses_data=houses_data,
            chart_id=chart_id,
            name=name,
            mug_size=mug_size,
            background_color=background_color
        )

        return {
            "chart_image": chart_filename,
            "wordcloud_image": wordcloud_filename_out,
            "planets_image": planets_filename,
            "aspects_image": aspects_filename,
            "houses_image": houses_filename
        }
