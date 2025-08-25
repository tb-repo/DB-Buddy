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
        answers = conversation_data.get('answers', [])
        metadata_data = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Session ID:', session_id[:8] + '...'],
            ['Service Type:', conversation_data.get('type', 'General').title()],
            ['Total Interactions:', str(len(answers))]
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
        
        # High-Level Summary Section
        story.append(Paragraph("Consultation Summary", self.styles['SectionHeader']))
        summary_data = self.extract_consultation_summary(conversation_data)
        
        if summary_data['sql_queries']:
            story.append(Paragraph("<b>SQL Queries Analyzed:</b>", self.styles['Normal']))
            for i, query in enumerate(summary_data['sql_queries'][:3], 1):  # Limit to 3 queries
                story.append(Paragraph(f"Query {i}:", self.styles['Normal']))
                story.append(Paragraph(query, self.styles['CodeBlock']))
                story.append(Spacer(1, 8))
        
        if summary_data['key_inputs']:
            story.append(Paragraph("<b>Key Information Provided:</b>", self.styles['Normal']))
            for input_item in summary_data['key_inputs']:
                story.append(Paragraph(f"• {input_item}", self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        if summary_data['recommendations']:
            story.append(Paragraph("<b>Key Recommendations:</b>", self.styles['Normal']))
            for rec in summary_data['recommendations']:
                story.append(Paragraph(f"• {rec}", self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Detailed Conversation
        story.append(Paragraph("Detailed Consultation Conversation", self.styles['SectionHeader']))
        
        # Process conversation messages with better formatting
        for i, answer in enumerate(answers):
            # User message header
            story.append(Paragraph(f"<b>User Input {i+1}:</b>", self.styles['Normal']))
            story.append(Spacer(1, 6))
            
            # User content with proper formatting
            user_content = self.format_message_content(answer)
            story.append(Paragraph(user_content, self.styles['Normal']))
            story.append(Spacer(1, 15))
            
            # DB-Buddy response placeholder
            story.append(Paragraph(f"<b>DB-Buddy Analysis {i+1}:</b>", self.styles['Normal']))
            story.append(Spacer(1, 6))
            
            # Generate response summary based on content
            response_summary = self.generate_response_summary(answer, conversation_data.get('type', 'general'))
            story.append(Paragraph(response_summary, self.styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(PageBreak())
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        exec_summary = self.generate_executive_summary(conversation_data, summary_data)
        story.append(Paragraph(exec_summary, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Footer
        story.append(Paragraph("Generated by DB-Buddy - AI Database Assistant", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def extract_consultation_summary(self, conversation_data):
        """Extract key information from conversation for summary"""
        answers = conversation_data.get('answers', [])
        service_type = conversation_data.get('type', 'general')
        
        summary = {
            'sql_queries': [],
            'key_inputs': [],
            'recommendations': []
        }
        
        for answer in answers:
            # Extract SQL queries
            sql_patterns = [
                r'```sql\n(.*?)\n```',
                r'SELECT.*?(?=\n\n|$)',
                r'INSERT.*?(?=\n\n|$)',
                r'UPDATE.*?(?=\n\n|$)',
                r'DELETE.*?(?=\n\n|$)'
            ]
            
            for pattern in sql_patterns:
                matches = re.findall(pattern, answer, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    clean_query = match.strip()[:200] + ('...' if len(match.strip()) > 200 else '')
                    if clean_query and clean_query not in summary['sql_queries']:
                        summary['sql_queries'].append(clean_query)
            
            # Extract key technical information
            if 'execution time' in answer.lower():
                summary['key_inputs'].append('Query execution time metrics provided')
            if 'table' in answer.lower() and ('size' in answer.lower() or 'rows' in answer.lower()):
                summary['key_inputs'].append('Table size and row count information')
            if 'index' in answer.lower():
                summary['key_inputs'].append('Index configuration details')
            if 'error' in answer.lower() or 'timeout' in answer.lower():
                summary['key_inputs'].append('Error messages and symptoms')
            if any(db in answer.lower() for db in ['postgresql', 'mysql', 'aurora', 'rds']):
                summary['key_inputs'].append('Database system specifications')
        
        # Generate recommendations based on service type
        if service_type == 'query':
            summary['recommendations'] = [
                'Implement proper indexing strategy',
                'Optimize query execution plans',
                'Monitor query performance metrics',
                'Consider query rewriting for better performance'
            ]
        elif service_type == 'performance':
            summary['recommendations'] = [
                'Establish performance monitoring baselines',
                'Implement automated alerting for anomalies',
                'Regular maintenance and optimization schedules',
                'Capacity planning for future growth'
            ]
        elif service_type == 'troubleshooting':
            summary['recommendations'] = [
                'Implement comprehensive error logging',
                'Establish incident response procedures',
                'Regular backup and recovery testing',
                'Proactive monitoring and alerting'
            ]
        else:
            summary['recommendations'] = [
                'Follow database best practices',
                'Implement regular monitoring',
                'Plan for scalability and growth',
                'Maintain proper documentation'
            ]
        
        return summary
    
    def generate_response_summary(self, user_input, service_type):
        """Generate a summary of what DB-Buddy would analyze"""
        input_lower = user_input.lower()
        
        if 'select' in input_lower or 'sql' in input_lower:
            return "Analyzed SQL query structure, identified potential performance bottlenecks, recommended specific indexes, and provided optimization strategies."
        elif 'error' in input_lower or 'timeout' in input_lower:
            return "Diagnosed error symptoms, identified root causes, provided troubleshooting steps, and recommended preventive measures."
        elif 'slow' in input_lower or 'performance' in input_lower:
            return "Evaluated performance metrics, identified optimization opportunities, recommended tuning strategies, and provided monitoring guidelines."
        elif service_type == 'architecture':
            return "Reviewed architecture requirements, recommended design patterns, provided scalability considerations, and suggested best practices."
        elif service_type == 'capacity':
            return "Analyzed capacity requirements, recommended hardware specifications, provided growth projections, and suggested monitoring strategies."
        elif service_type == 'security':
            return "Evaluated security requirements, recommended hardening measures, provided compliance guidelines, and suggested audit procedures."
        else:
            return "Provided comprehensive analysis, identified key issues, recommended solutions, and outlined implementation steps."
    
    def generate_executive_summary(self, conversation_data, summary_data):
        """Generate executive summary based on conversation analysis"""
        service_type = conversation_data.get('type', 'general')
        num_queries = len(summary_data['sql_queries'])
        num_inputs = len(summary_data['key_inputs'])
        
        summary = f"""This DB-Buddy consultation session focused on {service_type} assistance. 
        
        <b>Session Overview:</b>
        • Service Type: {service_type.title()}
        • SQL Queries Analyzed: {num_queries}
        • Key Technical Inputs: {num_inputs}
        • Recommendations Provided: {len(summary_data['recommendations'])}
        
        <b>Key Outcomes:</b>
        The consultation provided targeted analysis and actionable recommendations tailored to the user's specific database environment and requirements. All suggestions follow industry best practices and are designed for production implementation.
        
        <b>Next Steps:</b>
        • Review and validate recommendations in development environment
        • Implement suggested optimizations during maintenance windows
        • Establish monitoring for recommended metrics
        • Consult with DBA team for production deployment
        
        <b>Follow-up:</b>
        Consider scheduling regular performance reviews and implementing automated monitoring to prevent similar issues in the future.
        """
        
        return summary
    
    def format_message_content(self, content):
        """Format message content for PDF display with better text handling"""
        # Limit content length to prevent overflow
        if len(content) > 1000:
            content = content[:1000] + "... [content truncated for report]"
        
        # Remove problematic markdown that causes formatting issues
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Remove bold markdown
        content = re.sub(r'\*(.*?)\*', r'\1', content)      # Remove italic markdown
        content = re.sub(r'`(.*?)`', r'\1', content)        # Remove inline code markdown
        
        # Handle code blocks by extracting them separately
        content = re.sub(r'```sql\n(.*?)\n```', r'[SQL Query: \1]', content, flags=re.DOTALL)
        content = re.sub(r'```\n(.*?)\n```', r'[Code Block: \1]', content, flags=re.DOTALL)
        
        # Clean up line breaks for better PDF formatting
        content = re.sub(r'\n\s*\n', ' ', content)  # Replace double line breaks with space
        content = re.sub(r'\n', ' ', content)       # Replace single line breaks with space
        content = re.sub(r'\s+', ' ', content)      # Normalize multiple spaces
        
        return content.strip()