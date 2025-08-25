from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import re
import io

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        # Custom styles for the report
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2563eb'),
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#374151'),
            borderWidth=1,
            borderColor=colors.HexColor('#e5e7eb'),
            borderPadding=8,
            backColor=colors.HexColor('#f8fafc')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=self.styles['Code'],
            fontSize=10,
            fontName='Courier',
            backColor=colors.HexColor('#f3f4f6'),
            borderWidth=1,
            borderColor=colors.HexColor('#d1d5db'),
            borderPadding=8,
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='UserMessage',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leftIndent=20,
            borderWidth=1,
            borderColor=colors.HexColor('#3b82f6'),
            borderPadding=8,
            backColor=colors.HexColor('#eff6ff')
        ))
        
        self.styles.add(ParagraphStyle(
            name='BotMessage',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            borderWidth=1,
            borderColor=colors.HexColor('#10b981'),
            borderPadding=8,
            backColor=colors.HexColor('#f0fdf4')
        ))
    
    def generate_report(self, conversation_data, session_id):
        """Generate PDF report from conversation data"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Build the story (content)
        story = []
        
        # Title
        story.append(Paragraph("DB-Buddy Consultation Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Report metadata
        metadata_data = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Session ID:', session_id],
            ['Service Type:', conversation_data.get('type', 'General').title()],
            ['Total Messages:', str(len(conversation_data.get('answers', [])) * 2)]  # User + Bot messages
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 30))
        
        # System Configuration
        if conversation_data.get('user_selections'):
            story.append(Paragraph("System Configuration", self.styles['SectionHeader']))
            config_data = []
            for key, value in conversation_data['user_selections'].items():
                if value:
                    config_data.append([key.replace('_', ' ').title() + ':', value])
            
            if config_data:
                config_table = Table(config_data, colWidths=[2*inch, 4*inch])
                config_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                ]))
                story.append(config_table)
                story.append(Spacer(1, 20))
        
        # Conversation
        story.append(Paragraph("Consultation Conversation", self.styles['SectionHeader']))
        
        # Process conversation messages
        answers = conversation_data.get('answers', [])
        
        for i, answer in enumerate(answers):
            # User message
            story.append(Paragraph(f"<b>User Message {i+1}:</b>", self.styles['Normal']))
            user_content = self.format_message_content(answer)
            story.append(Paragraph(user_content, self.styles['UserMessage']))
            story.append(Spacer(1, 10))
            
            # Bot response (if available)
            story.append(Paragraph(f"<b>DB-Buddy Response {i+1}:</b>", self.styles['Normal']))
            # Note: In actual implementation, you'd need to store bot responses
            # For now, we'll add a placeholder
            bot_response = "Detailed analysis and recommendations provided based on the user's query."
            story.append(Paragraph(bot_response, self.styles['BotMessage']))
            story.append(Spacer(1, 15))
        
        # Summary section
        story.append(PageBreak())
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        summary_content = f"""
        This consultation session focused on {conversation_data.get('type', 'database assistance')}. 
        The user provided {len(answers)} detailed queries/descriptions, and DB-Buddy provided 
        comprehensive analysis and recommendations for each issue.
        
        Key areas addressed:
        • Database performance optimization
        • Query analysis and tuning recommendations  
        • Best practices implementation
        • Production-ready solutions
        
        All recommendations follow industry best practices and are tailored to the user's 
        specific environment and requirements.
        """
        
        story.append(Paragraph(summary_content, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Footer
        story.append(Paragraph("Generated by DB-Buddy - AI Database Assistant", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def format_message_content(self, content):
        """Format message content for PDF display"""
        # Remove markdown formatting and clean up
        content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)  # Bold
        content = re.sub(r'\*(.*?)\*', r'<i>\1</i>', content)      # Italic
        content = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', content)  # Code
        
        # Handle code blocks
        content = re.sub(r'```sql\n(.*?)\n```', r'<br/><font name="Courier" size="9">\1</font><br/>', content, flags=re.DOTALL)
        content = re.sub(r'```\n(.*?)\n```', r'<br/><font name="Courier" size="9">\1</font><br/>', content, flags=re.DOTALL)
        
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '<br/><br/>', content)
        content = re.sub(r'\n', '<br/>', content)
        
        return content