from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import io

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def generate_report(self, conversation_data: dict, session_id: str) -> io.BytesIO:
        """Generate PDF report from conversation data"""
        buffer = io.BytesIO()
        
        try:
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            
            # Title
            title = Paragraph("DB-Buddy Analysis Report", self.styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Metadata
            meta = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            meta += f"Session ID: {session_id}<br/>"
            meta += f"Service Type: {conversation_data.get('type', 'General')}"
            
            story.append(Paragraph(meta, self.styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Content
            answers = conversation_data.get('answers', [])
            for i, answer in enumerate(answers, 1):
                story.append(Paragraph(f"Query {i}:", self.styles['Heading2']))
                story.append(Paragraph(answer, self.styles['Normal']))
                story.append(Spacer(1, 12))
            
            doc.build(story)
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            # Return empty buffer on error
            buffer.write(b"PDF generation failed")
            buffer.seek(0)
            return buffer