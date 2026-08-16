from typing import Dict, Any
import os
import uuid
from datetime import datetime

class PDFGenerator:
    """Safe wrapper for PDFGenerator that handles missing dependencies"""
    
    def __init__(self):
        # Check if reportlab is available
        self.reportlab_available = False
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            
            self.reportlab_available = True
            self.setup_reportlab_imports()
            self.setup_custom_styles()
        except ImportError:
            print("Warning: reportlab not available. PDF generation will return mock response.")
    
    def setup_reportlab_imports(self):
        """Import reportlab modules"""
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        
        self.letter = letter
        self.SimpleDocTemplate = SimpleDocTemplate
        self.Paragraph = Paragraph
        self.Spacer = Spacer
        self.PageBreak = PageBreak
        self.Table = Table
        self.TableStyle = TableStyle
        self.Image = Image
        self.getSampleStyleSheet = getSampleStyleSheet
        self.ParagraphStyle = ParagraphStyle
        self.inch = inch
        self.colors = colors
        self.TA_CENTER = TA_CENTER
        self.TA_LEFT = TA_LEFT
        self.TA_JUSTIFY = TA_JUSTIFY
        
        self.styles = self.getSampleStyleSheet()
    
    def setup_custom_styles(self):
        """Setup custom styles for the PDF"""
        if not self.reportlab_available:
            return
            
        # Title style
        self.title_style = self.ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=self.TA_CENTER,
            textColor=self.colors.HexColor('#4f46e5')
        )
        
        # Subtitle style
        self.subtitle_style = self.ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            alignment=self.TA_CENTER,
            textColor=self.colors.HexColor('#7c3aed')
        )
        
        # Section header style
        self.section_style = self.ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=self.colors.HexColor('#374151'),
            borderWidth=1,
            borderColor=self.colors.HexColor('#e5e7eb'),
            borderPadding=8,
            backColor=self.colors.HexColor('#f8fafc')
        )
        
        # Body text style
        self.body_style = self.ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=self.TA_JUSTIFY,
            textColor=self.colors.HexColor('#374151')
        )
        
        # Interpretation style
        self.interpretation_style = self.ParagraphStyle(
            'Interpretation',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            leftIndent=20,
            textColor=self.colors.HexColor('#6b7280'),
            alignment=self.TA_JUSTIFY
        )

    def generate_pdf_report(self, chart_data, filename=None):
        """Generate a comprehensive PDF report from chart data"""
        
        if not self.reportlab_available:
            # Return mock response when reportlab is not available
            if filename is None:
                timestamp = str(int(datetime.now().timestamp() * 1000000))
                filename = f"astro_report_{timestamp}.pdf"
            
            print(f"Warning: Cannot generate PDF '{filename}' - reportlab not available")
            return filename
        
        if filename is None:
            timestamp = str(int(datetime.now().timestamp() * 1000000))
            filename = f"astro_report_{timestamp}.pdf"
        
        filepath = os.path.join("static", "pdf", filename)
        
        # Ensure the pdf directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            # Create the PDF document
            doc = self.SimpleDocTemplate(
                filepath,
                pagesize=self.letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build the story (content)
            story = []
            
            # Title page
            story.extend(self._create_title_page(chart_data))
            story.append(self.PageBreak())
            
            # Chart and Rising sign on one page
            story.extend(self._create_chart_section(chart_data))
            story.extend(self._create_rising_section(chart_data))
            story.append(self.PageBreak())
            
            # Planetary interpretations
            story.extend(self._create_interpretations_section(chart_data))
            story.append(self.PageBreak())
            
            # Aspects section
            story.extend(self._create_aspects_section(chart_data))
            story.append(self.PageBreak())
            
            # Elements section
            story.extend(self._create_elements_section(chart_data))
            
            # Build the PDF
            doc.build(story)
            
            return filename
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return filename

    def _create_title_page(self, chart_data):
        """Create the title page"""
        story = []
        
        # Main title
        story.append(self.Paragraph("🌟 Astrological Chart Report", self.title_style))
        story.append(self.Spacer(1, 0.5*self.inch))
        
        # Person's name
        name = chart_data.get('birth_data', {}).get('name', 'Unknown')
        story.append(self.Paragraph(f"For: {name}", self.subtitle_style))
        story.append(self.Spacer(1, 0.3*self.inch))
        
        # Birth details
        birth_data = chart_data.get('birth_data', {})
        date = birth_data.get('date', 'Unknown')
        time = birth_data.get('time', 'Unknown')
        location = birth_data.get('location', 'Unknown')
        
        story.append(self.Paragraph(f"Born: {date} at {time}", self.body_style))
        story.append(self.Paragraph(f"Location: {location}", self.body_style))
        story.append(self.Spacer(1, 0.5*self.inch))
        
        # Generation info
        generated_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        story.append(self.Paragraph(f"Report generated on {generated_date}", self.body_style))
        
        return story

    def _create_rising_section(self, chart_data):
        """Create rising sign section"""
        story = []
        
        story.append(self.Paragraph("🌅 Your Rising Sign", self.section_style))
        
        rising_interpretation = chart_data.get('rising_interpretation', 'No rising sign interpretation available.')
        story.append(self.Paragraph(rising_interpretation, self.body_style))
        story.append(self.Spacer(1, 0.2*self.inch))
        
        return story

    def _create_interpretations_section(self, chart_data):
        """Create planetary interpretations section"""
        story = []
        
        story.append(self.Paragraph("📖 Planetary Interpretations", self.section_style))
        
        observations = chart_data.get('observations', [])
        
        for observation in observations:
            if ': ' in observation:
                title, content = observation.split(': ', 1)
                story.append(self.Paragraph(f"<b>{title}</b>", self.body_style))
                story.append(self.Paragraph(content, self.interpretation_style))
            else:
                story.append(self.Paragraph(observation, self.body_style))
            
            story.append(self.Spacer(1, 0.1*self.inch))
        
        return story

    def _create_aspects_section(self, chart_data):
        """Create aspects section"""
        story = []
        
        story.append(self.Paragraph("🔗 Planetary Aspects", self.section_style))
        
        aspects = chart_data.get('aspects', [])
        
        if not aspects:
            story.append(self.Paragraph("No aspects found in this chart.", self.body_style))
            return story
        
        for aspect in aspects:
            planets = aspect.get('planets', 'Unknown')
            strength = aspect.get('strength', 'Unknown')
            orb = aspect.get('orb', 'Unknown')
            interpretation = aspect.get('interpretation', 'No interpretation available.')
            
            # Create aspect header with strength color coding
            strength_colors = {
                'Very Strong': self.colors.HexColor('#dc2626'),
                'Strong': self.colors.HexColor('#ea580c'),
                'Moderate': self.colors.HexColor('#ca8a04'),
                'Weak': self.colors.HexColor('#6b7280')
            }
            
            strength_color = strength_colors.get(strength, self.colors.HexColor('#6b7280'))
            
            story.append(self.Paragraph(f"<b>{planets}</b> - <font color='{strength_color.hexval()}'>{strength}</font> (Orb: {orb}°)", self.body_style))
            story.append(self.Paragraph(interpretation, self.interpretation_style))
            story.append(self.Spacer(1, 0.15*self.inch))
        
        return story

    def _create_elements_section(self, chart_data):
        """Create elements analysis section"""
        story = []
        
        story.append(self.Paragraph("🌍 Elemental Analysis", self.section_style))
        
        element_analysis = chart_data.get('element_analysis', {})
        
        # Element balance
        element_balance = element_analysis.get('element_balance', 'Unknown')
        story.append(self.Paragraph(f"<b>Elemental Balance:</b> {element_balance}", self.body_style))
        
        # Element summary
        element_summary = element_analysis.get('element_summary', 'No elemental summary available.')
        story.append(self.Paragraph(element_summary, self.body_style))
        story.append(self.Spacer(1, 0.2*self.inch))
        
        return story

    def _create_chart_section(self, chart_data):
        """Create the natal chart section"""
        story = []
        
        story.append(self.Paragraph("📊 Natal Chart", self.section_style))
        
        chart_url = chart_data.get('chart_url', '')
        if chart_url:
            story.append(self.Paragraph(
                f"Chart image available at: {chart_url}",
                self.body_style
            ))
            story.append(self.Paragraph(
                "Your personalized natal chart shows the positions of the planets at the time of your birth.",
                self.body_style
            ))
        else:
            story.append(self.Paragraph("Chart image not available.", self.body_style))
        
        return story