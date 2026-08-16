from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os
import io
from datetime import datetime
import cairosvg
from PIL import Image as PILImage
import random


# ── Sign data for career/compatibility ─────────────────────────
SIGN_FULL = {
    'ari':'Aries','tau':'Taurus','gem':'Gemini','can':'Cancer','leo':'Leo','vir':'Virgo',
    'lib':'Libra','sco':'Scorpio','sag':'Sagittarius','cap':'Capricorn','aqu':'Aquarius','pis':'Pisces',
}
SIGN_ELEMENT = {
    'Aries':'fire','Taurus':'earth','Gemini':'air','Cancer':'water','Leo':'fire','Virgo':'earth',
    'Libra':'air','Scorpio':'water','Sagittarius':'fire','Capricorn':'earth','Aquarius':'air','Pisces':'water',
}
SIGN_MODALITY = {
    'Aries':'Cardinal','Taurus':'Fixed','Gemini':'Mutable','Cancer':'Cardinal','Leo':'Fixed','Virgo':'Mutable',
    'Libra':'Cardinal','Scorpio':'Fixed','Sagittarius':'Mutable','Capricorn':'Cardinal','Aquarius':'Fixed','Pisces':'Mutable',
}
COMPATIBLE_ELEMENTS = {'fire':['fire','air'],'earth':['earth','water'],'air':['air','fire'],'water':['water','earth']}
CAREER_BY_SIGN = {
    'Aries':['Entrepreneur','Military/Defense','Athletics/Coaching','Emergency Services','Sales Leader'],
    'Taurus':['Finance/Banking','Real Estate','Culinary Arts','Music/Arts','Agriculture'],
    'Gemini':['Journalism','Marketing','Teaching','Writing/Publishing','Tech/Social Media'],
    'Cancer':['Healthcare/Nursing','Social Work','Hospitality','Interior Design','Child Development'],
    'Leo':['Entertainment/Acting','Executive Leadership','Event Planning','Fashion','Politics'],
    'Virgo':['Data Science','Healthcare/Medicine','Accounting','Research','Quality Assurance'],
    'Libra':['Law/Mediation','Diplomacy','Design/Architecture','Human Resources','Public Relations'],
    'Scorpio':['Psychology/Therapy','Criminal Justice','Surgery','Research Science','Intelligence/Security'],
    'Sagittarius':['Education/Professor','Travel Industry','Philosophy/Theology','International Business','Publishing'],
    'Capricorn':['Corporate Leadership','Engineering','Government/Policy','Architecture','Project Management'],
    'Aquarius':['Technology/Innovation','Science/Research','Nonprofit/Activism','Aerospace','Programming'],
    'Pisces':['Arts/Music','Therapy/Counseling','Film/Photography','Spiritual Work','Marine Biology'],
}

def _full(s):
    return SIGN_FULL.get((s or '').lower(), s)


class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        self.title_style = ParagraphStyle('CustomTitle', parent=self.styles['Heading1'],
            fontSize=24, spaceAfter=30, alignment=TA_CENTER, textColor=colors.HexColor('#4f46e5'))
        self.subtitle_style = ParagraphStyle('CustomSubtitle', parent=self.styles['Heading2'],
            fontSize=18, spaceAfter=20, alignment=TA_CENTER, textColor=colors.HexColor('#7c3aed'))
        self.section_style = ParagraphStyle('SectionHeader', parent=self.styles['Heading2'],
            fontSize=16, spaceAfter=12, spaceBefore=20, textColor=colors.HexColor('#374151'),
            borderWidth=1, borderColor=colors.HexColor('#e5e7eb'), borderPadding=8, backColor=colors.HexColor('#f8fafc'))
        self.body_style = ParagraphStyle('CustomBody', parent=self.styles['Normal'],
            fontSize=11, spaceAfter=12, alignment=TA_JUSTIFY, textColor=colors.HexColor('#374151'))
        self.interpretation_style = ParagraphStyle('Interpretation', parent=self.styles['Normal'],
            fontSize=10, spaceAfter=8, leftIndent=20, textColor=colors.HexColor('#6b7280'), alignment=TA_JUSTIFY)
        self.label_style = ParagraphStyle('Label', parent=self.styles['Normal'],
            fontSize=9, spaceAfter=4, textColor=colors.HexColor('#9ca3af'))
        self.value_style = ParagraphStyle('Value', parent=self.styles['Normal'],
            fontSize=13, spaceAfter=8, textColor=colors.HexColor('#4f46e5'), fontName='Helvetica-Bold')
        self.career_style = ParagraphStyle('Career', parent=self.styles['Normal'],
            fontSize=11, spaceAfter=6, textColor=colors.HexColor('#d97706'), fontName='Helvetica-Bold')
        self.compat_style = ParagraphStyle('Compat', parent=self.styles['Normal'],
            fontSize=11, spaceAfter=6, textColor=colors.HexColor('#db2777'), fontName='Helvetica-Bold')

    def generate_pdf_report(self, chart_data, filename=None):
        if filename is None:
            timestamp = str(int(datetime.now().timestamp() * 1000000))
            filename = f"astro_report_{timestamp}.pdf"

        filepath = os.path.join("static", "pdf", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        doc = SimpleDocTemplate(filepath, pagesize=letter,
            rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

        story = []

        # Page 1: Title
        story.extend(self._create_title_page(chart_data))
        story.append(PageBreak())

        # Page 2: Chart image
        story.extend(self._create_chart_section(chart_data))
        story.append(PageBreak())

        # Page 3: Wordcloud + Element/Modality info
        story.extend(self._create_wordcloud_section(chart_data))
        story.extend(self._create_info_cards(chart_data))
        story.append(PageBreak())

        # Page 4: Rising interpretation
        story.extend(self._create_rising_section(chart_data))
        story.append(PageBreak())

        # Page 5: Observations
        story.extend(self._create_observations_section(chart_data))
        story.append(PageBreak())

        # Page 6: Aspects
        story.extend(self._create_aspects_section(chart_data))
        story.append(PageBreak())

        # Page 7: Career
        story.extend(self._create_career_section(chart_data))
        story.append(PageBreak())

        # Page 8: Compatibility
        story.extend(self._create_compatibility_section(chart_data))
        story.append(PageBreak())

        # Page 9: Elemental analysis
        story.extend(self._create_elements_section(chart_data))

        doc.build(story)
        return filename

    # ── SVG conversion ─────────────────────────────────────────
    def _convert_svg_to_png(self, svg_path):
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()

            color_replacements = {
                'var(--kerykeion-chart-color-paper-0)': '#000000',
                'var(--kerykeion-chart-color-paper-1)': '#ffffff',
                'var(--kerykeion-chart-color-conjunction)': '#5757e2',
                'var(--kerykeion-chart-color-sextile)': '#d59e28',
                'var(--kerykeion-chart-color-square)': '#dc0000',
                'var(--kerykeion-chart-color-trine)': '#36d100',
                'var(--kerykeion-chart-color-opposition)': '#510060',
            }
            # Add zodiac bg/icon colors
            zodiac_colors = ['#ff7200','#6b3d00','#69acf1','#2b4972']
            for i in range(12):
                c = zodiac_colors[i % 4]
                color_replacements[f'var(--kerykeion-chart-color-zodiac-bg-{i})'] = c
                color_replacements[f'var(--kerykeion-chart-color-zodiac-icon-{i})'] = c
            # Planet colors
            planet_colors = {'sun':'#984b00','moon':'#150052','mercury':'#520800','venus':'#400052',
                'mars':'#540000','jupiter':'#47133d','saturn':'#124500','uranus':'#6f0766',
                'neptune':'#06537f','pluto':'#713f04','mean-node':'#4c1541','chiron':'#666f06'}
            for p, c in planet_colors.items():
                color_replacements[f'var(--kerykeion-chart-color-{p})'] = c
            # House colors
            for h, c in [('first','#ff7e00'),('tenth','#ff0000'),('seventh','#0000ff'),('fourth','#000000')]:
                color_replacements[f'var(--kerykeion-chart-color-{h}-house)'] = c
            color_replacements['var(--kerykeion-chart-color-house-number)'] = '#f00'
            for i in range(3):
                color_replacements[f'var(--kerykeion-chart-color-zodiac-radix-ring-{i})'] = '#ff0000'
            color_replacements['var(--kerykeion-chart-color-houses-radix-line)'] = '#ff0000'
            color_replacements['var(--kerykeion-chart-color-lunar-phase-0)'] = '#000000'
            color_replacements['var(--kerykeion-chart-color-lunar-phase-1)'] = '#ffffff'
            color_replacements['var(--kerykeion-chart-color-quintile)'] = '#1f99b3'

            for css_var, color_value in color_replacements.items():
                svg_content = svg_content.replace(css_var, color_value)

            png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), output_width=1300, output_height=1300)
            return png_data
        except Exception as e:
            print(f"Error converting SVG to PNG: {e}")
            return None

    def _embed_image(self, png_data, width, height):
        """Helper to embed PNG data as a ReportLab Image"""
        try:
            img_buffer = io.BytesIO(png_data)
            PILImage.open(io.BytesIO(png_data)).verify()
            img = Image(img_buffer, width=width, height=height)
            img.hAlign = 'CENTER'
            return img
        except Exception as e:
            print(f"Error embedding image: {e}")
            return None

    # ── Page sections ──────────────────────────────────────────
    def _create_title_page(self, chart_data):
        story = []
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph("Astrological Chart Report", self.title_style))
        story.append(Spacer(1, 0.5*inch))

        name = chart_data.get('birth_data', {}).get('name', 'Unknown')
        story.append(Paragraph(f"For: {name}", self.subtitle_style))
        story.append(Spacer(1, 0.5*inch))

        birth_data = chart_data.get('birth_data', {})
        story.append(Paragraph(f"Born: {birth_data.get('date', '?')} at {birth_data.get('time', '?')}", self.body_style))
        story.append(Paragraph(f"Location: {birth_data.get('location', '?')}", self.body_style))
        story.append(Spacer(1, 0.5*inch))

        # Quick summary
        planets = chart_data.get('planets', {})
        sun = _full(planets.get('sun', {}).get('sign'))
        moon = _full(planets.get('moon', {}).get('sign'))
        rising = _full(chart_data.get('houses', {}).get('house_1', {}).get('sign'))
        story.append(Paragraph(f"Sun: {sun}  |  Moon: {moon}  |  Rising: {rising}", self.subtitle_style))

        story.append(Spacer(1, 1*inch))
        story.append(Paragraph(f"Report generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", self.label_style))
        return story

    def _create_chart_section(self, chart_data):
        story = []
        story.append(Paragraph("Natal Chart", self.section_style))

        chart_url = chart_data.get('chart_url', '')
        if chart_url:
            svg_filename = chart_url.replace('/static/images/', '')
            svg_path = os.path.join('static', 'images', svg_filename)
            if os.path.exists(svg_path):
                png_data = self._convert_svg_to_png(svg_path)
                if png_data:
                    img = self._embed_image(png_data, 6.5*inch, 6.5*inch)
                    if img:
                        story.append(Spacer(1, 0.2*inch))
                        story.append(img)
                        return story

        story.append(Paragraph("Chart image not available.", self.body_style))
        return story

    def _create_wordcloud_section(self, chart_data):
        story = []
        wc = chart_data.get('wordcloud', {})
        file_url = wc.get('file_url', '')
        if not file_url:
            return story

        story.append(Paragraph("Chart Essence", self.section_style))

        png_path = file_url.replace('/static/', 'static/')
        if os.path.exists(png_path):
            try:
                img = Image(png_path, width=6*inch, height=3*inch)
                img.hAlign = 'CENTER'
                story.append(Spacer(1, 0.2*inch))
                story.append(img)
                story.append(Spacer(1, 0.3*inch))
            except Exception as e:
                print(f"Error embedding wordcloud: {e}")

        return story

    def _create_info_cards(self, chart_data):
        story = []
        ea = chart_data.get('element_analysis', {})
        dominant_el = ea.get('dominant_element', '?')
        balance = ea.get('element_balance', '')

        # Compute modality
        planets = chart_data.get('planets', {})
        modality_counts = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}
        for p in planets.values():
            sign = _full(p.get('sign', ''))
            m = SIGN_MODALITY.get(sign)
            if m:
                modality_counts[m] += 1
        dominant_mod = max(modality_counts, key=modality_counts.get)

        data = [
            ['Primary Element', 'Modality Focus', 'Elemental Balance'],
            [dominant_el.upper(), dominant_mod, balance],
        ]
        table = Table(data, colWidths=[2.2*inch, 2.2*inch, 2.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        return story

    def _create_rising_section(self, chart_data):
        story = []
        story.append(Paragraph("Rising Interpretation", self.section_style))
        rising = chart_data.get('rising_interpretation', '')
        if rising and 'being processed' not in rising:
            story.append(Paragraph(rising, self.body_style))
        else:
            summary = chart_data.get('element_analysis', {}).get('element_summary', '')
            if summary:
                story.append(Paragraph("Elemental Analysis", self.section_style))
                story.append(Paragraph(summary, self.body_style))
            else:
                story.append(Paragraph("Rising interpretation not available.", self.body_style))
        return story

    def _create_observations_section(self, chart_data):
        story = []
        observations = chart_data.get('observations', [])
        if not observations:
            return story

        story.append(Paragraph("Natal Observations", self.section_style))
        story.append(Spacer(1, 0.1*inch))

        for obs in observations:
            if ': ' in obs:
                title, content = obs.split(': ', 1)
                story.append(Paragraph(f"<b>{title}</b>", self.body_style))
                story.append(Paragraph(content, self.interpretation_style))
            else:
                story.append(Paragraph(obs, self.body_style))
            story.append(Spacer(1, 0.1*inch))

        return story

    def _create_aspects_section(self, chart_data):
        story = []
        aspects = chart_data.get('aspects', [])
        if not aspects:
            return story

        story.append(Paragraph("Planetary Aspects", self.section_style))
        story.append(Paragraph(
            "Aspects are angular relationships between planets. "
            "Conjunctions (0°) merge energies. Trines (120°) and sextiles (60°) create harmony. "
            "Oppositions (180°) and squares (90°) create tension that drives growth.",
            self.interpretation_style
        ))
        story.append(Spacer(1, 0.15*inch))

        strength_colors = {
            'Strong': '#ea580c', 'Very Strong': '#dc2626',
            'Moderate': '#ca8a04', 'Weak': '#6b7280'
        }

        for asp in aspects:
            planets_str = asp.get('planets', '?')
            strength = asp.get('strength', '?')
            orb = asp.get('orb', 0)
            interp = asp.get('interpretation', '')
            sc = strength_colors.get(strength, '#6b7280')

            story.append(Paragraph(
                f"<b>{planets_str}</b> — <font color='{sc}'>{strength}</font> (orb {orb:.1f}°)",
                self.body_style
            ))
            if interp:
                story.append(Paragraph(interp, self.interpretation_style))
            story.append(Spacer(1, 0.1*inch))

        return story

    def _create_career_section(self, chart_data):
        story = []
        planets = chart_data.get('planets', {})
        houses = chart_data.get('houses', {})
        if not planets:
            return story

        story.append(Paragraph("Ideal Career Path", self.section_style))

        mc_sign = _full(houses.get('house_10', {}).get('sign') or planets.get('saturn', {}).get('sign'))
        sun_sign = _full(planets.get('sun', {}).get('sign'))
        mars_sign = _full(planets.get('mars', {}).get('sign'))
        saturn_house = (planets.get('saturn', {}).get('house', '') or '').replace('_', ' ')

        mc_el = SIGN_ELEMENT.get(mc_sign, '')
        sun_el = SIGN_ELEMENT.get(sun_sign, '')

        el_desc = {'fire': 'leadership, initiative, and bold action', 'earth': 'structure, reliability, and tangible results',
                    'air': 'communication, ideas, and social connection', 'water': 'intuition, creativity, and emotional intelligence'}
        drive_desc = {'fire': 'impact and recognition', 'earth': 'security and mastery',
                      'air': 'knowledge and influence', 'water': 'meaning and healing'}

        explanation = (
            f"Your Midheaven in {mc_sign} points to careers requiring {el_desc.get(mc_el, 'diverse skills')}. "
            f"Your Sun in {sun_sign} reinforces a drive for {drive_desc.get(sun_el, 'purpose')}. "
            f"Saturn in the {saturn_house} suggests long-term success in structured professional environments."
        )
        story.append(Paragraph(explanation, self.body_style))
        story.append(Spacer(1, 0.2*inch))

        story.append(Paragraph("<b>Recommended Careers:</b>", self.body_style))
        careers = []
        seen = set()
        for c in (CAREER_BY_SIGN.get(mc_sign, []) + CAREER_BY_SIGN.get(sun_sign, [])[:2] + CAREER_BY_SIGN.get(mars_sign, [])[:1]):
            if c not in seen:
                seen.add(c)
                careers.append(c)
        for c in careers[:6]:
            story.append(Paragraph(f"• {c}", self.career_style))

        return story

    def _create_compatibility_section(self, chart_data):
        story = []
        planets = chart_data.get('planets', {})
        houses = chart_data.get('houses', {})
        if not planets:
            return story

        story.append(Paragraph("Ideal Mate Compatibility", self.section_style))

        sun = _full(planets.get('sun', {}).get('sign'))
        moon = _full(planets.get('moon', {}).get('sign'))
        venus = _full(planets.get('venus', {}).get('sign'))
        mars = _full(planets.get('mars', {}).get('sign'))
        rising = _full(houses.get('house_1', {}).get('sign'))

        # Show placements
        data = [
            ['Sun', 'Moon', 'Venus', 'Mars', 'Rising'],
            [sun, moon, venus, mars, rising],
        ]
        table = Table(data, colWidths=[1.3*inch]*5)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#db2777')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, 1), 13),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))

        # Venus analysis (general — gender not passed to PDF)
        venus_el = SIGN_ELEMENT.get(venus, '')
        venus_desc = {'fire': 'passion, adventure, and bold gestures', 'earth': 'stability, loyalty, and physical affection',
                      'air': 'communication, intellectual connection, and social bonds', 'water': 'emotional depth, intuition, and nurturing'}
        story.append(Paragraph(
            f"<b>Venus in {venus}:</b> You express love through {venus_desc.get(venus_el, 'unique ways')}.",
            self.body_style
        ))

        moon_el = SIGN_ELEMENT.get(moon, '')
        moon_desc = {'fire': 'excitement, freedom, and a partner who matches your energy',
                     'earth': 'security, consistency, and tangible expressions of care',
                     'air': 'mental stimulation, space, and a partner who communicates openly',
                     'water': 'emotional safety, deep intimacy, and a partner who understands unspoken feelings'}
        story.append(Paragraph(
            f"<b>Moon in {moon}:</b> You need {moon_desc.get(moon_el, 'deep connection')}.",
            self.body_style
        ))
        story.append(Spacer(1, 0.2*inch))

        # Best partner signs
        venus_compat = COMPATIBLE_ELEMENTS.get(venus_el, [])
        moon_compat = COMPATIBLE_ELEMENTS.get(moon_el, [])
        sun_el = SIGN_ELEMENT.get(sun, '')
        all_signs = list(SIGN_ELEMENT.keys())

        scores = []
        for s in all_signs:
            el = SIGN_ELEMENT[s]
            score = 0
            if el in venus_compat: score += 3
            if el in moon_compat: score += 2
            if el in COMPATIBLE_ELEMENTS.get(sun_el, []): score += 1
            if s == sun: score -= 1
            scores.append((s, score))
        scores.sort(key=lambda x: -x[1])

        top = [s for s, sc in scores if sc >= 5] or [s for s, _ in scores[:3]]
        good = [s for s, sc in scores if sc == 4][:4]

        story.append(Paragraph("<b>Best Partner Sun Signs:</b>", self.body_style))
        for s in top:
            story.append(Paragraph(f"• {s}", self.compat_style))
        if good:
            story.append(Paragraph("<b>Also Compatible:</b>", self.body_style))
            story.append(Paragraph(', '.join(good), self.interpretation_style))

        return story

    def _create_elements_section(self, chart_data):
        story = []
        ea = chart_data.get('element_analysis', {})

        story.append(Paragraph("Elemental Analysis", self.section_style))

        balance = ea.get('element_balance', '')
        if balance:
            story.append(Paragraph(f"<b>Elemental Balance:</b> {balance}", self.body_style))

        summary = ea.get('element_summary', '')
        if summary:
            story.append(Paragraph(summary, self.body_style))
        story.append(Spacer(1, 0.2*inch))

        detailed = ea.get('detailed_analysis', {})
        if detailed:
            story.append(Paragraph("<b>Element Distribution:</b>", self.body_style))
            icons = {'fire': 'Fire', 'earth': 'Earth', 'air': 'Air', 'water': 'Water'}
            table_data = [['Element', 'Planets', 'Count', '%']]
            for element, data in detailed.items():
                table_data.append([
                    icons.get(element, element.title()),
                    ', '.join(data.get('planets', [])),
                    str(data.get('count', 0)),
                    f"{data.get('percentage', 0)}%",
                ])

            table = Table(table_data, colWidths=[1.3*inch, 3*inch, 0.8*inch, 0.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(table)

        return story
