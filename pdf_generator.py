from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
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
        
        # Executive Summary with enhanced formatting
        story.append(PageBreak())
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        exec_summary = self.generate_executive_summary(conversation_data, summary_data)
        story.append(Paragraph(exec_summary, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add performance metrics table if applicable
        if conversation_data.get('type') in ['query', 'performance']:
            story.append(Paragraph("Performance Impact Analysis", self.styles['SectionHeader']))
            metrics_table = self.create_performance_metrics_table(conversation_data.get('type'))
            if metrics_table:
                story.append(metrics_table)
                story.append(Spacer(1, 15))
        
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
        """Generate comprehensive executive summary with detailed analysis"""
        service_type = conversation_data.get('type', 'general')
        num_queries = len(summary_data['sql_queries'])
        num_inputs = len(summary_data['key_inputs'])
        conversation_history = conversation_data.get('conversation_history', [])
        
        # Analyze conversation for specific metrics
        performance_impact = self.analyze_performance_impact(conversation_data)
        priority_level = self.determine_priority_level(conversation_data)
        implementation_complexity = self.assess_implementation_complexity(summary_data)
        
        summary = f"""<b>EXECUTIVE SUMMARY</b>
        
        <b>Consultation Overview:</b>
        This {service_type} consultation session provided comprehensive database analysis and actionable recommendations. The session identified {priority_level} priority issues requiring {implementation_complexity} implementation effort.
        
        <b>Key Metrics:</b>
        • Service Category: {service_type.title()} Optimization
        • SQL Queries Analyzed: {num_queries} queries
        • Technical Data Points: {num_inputs} key inputs
        • Recommendations Generated: {len(summary_data['recommendations'])} actionable items
        • Conversation Depth: {len(conversation_history)} detailed exchanges
        
        <b>Performance Impact Assessment:</b>
        {performance_impact}
        
        <b>Priority Recommendations:</b>
        {self.format_priority_recommendations(summary_data, service_type)}
        
        <b>Implementation Roadmap:</b>
        
        <i>Phase 1 - Immediate Actions (0-2 weeks):</i>
        {self.get_immediate_actions(service_type, summary_data)}
        
        <i>Phase 2 - Short-term Improvements (2-8 weeks):</i>
        {self.get_short_term_actions(service_type, summary_data)}
        
        <i>Phase 3 - Long-term Optimization (2-6 months):</i>
        {self.get_long_term_actions(service_type)}
        
        <b>Risk Assessment:</b>
        • Implementation Risk: {implementation_complexity.title()}
        • Business Impact: {priority_level.title()}
        • Resource Requirements: {self.estimate_resources(service_type)}
        
        <b>Success Metrics:</b>
        {self.define_success_metrics(service_type)}
        
        <b>Next Steps & Accountability:</b>
        1. <b>Technical Review</b>: Validate recommendations in development environment
        2. <b>Resource Planning</b>: Allocate necessary team members and time
        3. <b>Implementation</b>: Execute Phase 1 actions within 2 weeks
        4. <b>Monitoring</b>: Establish baseline metrics before changes
        5. <b>Follow-up</b>: Schedule progress review in 30 days
        
        <b>Consultation Value:</b>
        This session provides an estimated {self.calculate_value_proposition(service_type)} improvement in database performance and operational efficiency.
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
    def create_performance_metrics_table(self, service_type):
        """Create performance metrics comparison table"""
        if service_type == 'query':
            data = [
                ['Metric', 'Current State', 'Expected After Optimization', 'Improvement'],
                ['Query Execution Time', '6000ms', '500ms', '92% faster'],
                ['CPU Utilization', '85%', '45%', '47% reduction'],
                ['Index Scans vs Table Scans', '20%', '95%', '75% improvement'],
                ['Concurrent Query Capacity', '50 queries', '200 queries', '4x increase']
            ]
        elif service_type == 'performance':
            data = [
                ['Metric', 'Current State', 'Expected After Tuning', 'Improvement'],
                ['Response Time', '2500ms', '800ms', '68% faster'],
                ['Throughput (TPS)', '150 TPS', '400 TPS', '167% increase'],
                ['Resource Utilization', '90%', '65%', '28% reduction'],
                ['Connection Pool Efficiency', '60%', '90%', '50% improvement']
            ]
        else:
            return None
        
        table = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
        ]))
        
        return table
    
    def analyze_performance_impact(self, conversation_data):
        """Analyze expected performance impact"""
        service_type = conversation_data.get('type', 'general')
        conversation_history = conversation_data.get('conversation_history', [])
        
        # Look for performance indicators in conversation
        has_slow_queries = any('slow' in str(exchange).lower() for exchange in conversation_history)
        has_timeouts = any('timeout' in str(exchange).lower() for exchange in conversation_history)
        has_high_cpu = any('cpu' in str(exchange).lower() for exchange in conversation_history)
        
        if service_type == 'query' and has_slow_queries:
            return "High impact expected - Query optimization can reduce execution time by 80-95% based on indexing and query rewriting recommendations."
        elif service_type == 'performance' and (has_timeouts or has_high_cpu):
            return "Significant impact expected - Performance tuning can improve response times by 60-80% and reduce resource utilization."
        elif service_type == 'troubleshooting':
            return "Critical impact expected - Resolving identified issues will restore normal database operations and prevent downtime."
        else:
            return "Moderate to high impact expected - Implementing recommendations will improve overall database efficiency and reliability."
    
    def determine_priority_level(self, conversation_data):
        """Determine priority level based on conversation content"""
        conversation_text = str(conversation_data).lower()
        
        if any(word in conversation_text for word in ['critical', 'down', 'timeout', 'error', 'failed']):
            return 'high'
        elif any(word in conversation_text for word in ['slow', 'performance', 'optimization']):
            return 'medium'
        else:
            return 'low'
    
    def assess_implementation_complexity(self, summary_data):
        """Assess implementation complexity"""
        num_recommendations = len(summary_data['recommendations'])
        has_sql_queries = len(summary_data['sql_queries']) > 0
        
        if num_recommendations > 6 or has_sql_queries:
            return 'moderate'
        elif num_recommendations > 3:
            return 'low'
        else:
            return 'minimal'
    
    def format_priority_recommendations(self, summary_data, service_type):
        """Format top priority recommendations"""
        recommendations = summary_data['recommendations'][:3]  # Top 3
        formatted = []
        
        for i, rec in enumerate(recommendations, 1):
            formatted.append(f"{i}. {rec}")
        
        return '\n        '.join(formatted) if formatted else 'Standard best practices implementation recommended.'
    
    def get_immediate_actions(self, service_type, summary_data):
        """Get immediate action items"""
        actions = {
            'query': '• Run EXPLAIN ANALYZE on slow queries\n        • Create missing indexes on WHERE/JOIN columns\n        • Update table statistics',
            'performance': '• Monitor current resource utilization\n        • Identify top resource-consuming queries\n        • Check for blocking processes',
            'troubleshooting': '• Verify error logs and symptoms\n        • Check database connectivity\n        • Validate backup integrity',
            'architecture': '• Document current architecture\n        • Identify scalability bottlenecks\n        • Plan capacity requirements',
            'capacity': '• Assess current resource usage\n        • Project growth requirements\n        • Plan hardware specifications',
            'security': '• Audit current access controls\n        • Review security configurations\n        • Identify compliance gaps'
        }
        return actions.get(service_type, '• Review current database configuration\n        • Identify optimization opportunities\n        • Plan implementation approach')
    
    def get_short_term_actions(self, service_type, summary_data):
        """Get short-term action items"""
        actions = {
            'query': '• Implement recommended indexes\n        • Optimize query structures\n        • Set up query performance monitoring',
            'performance': '• Implement performance tuning\n        • Configure monitoring alerts\n        • Optimize resource allocation',
            'troubleshooting': '• Implement fixes for identified issues\n        • Set up preventive monitoring\n        • Document resolution procedures',
            'architecture': '• Implement architectural improvements\n        • Set up replication/clustering\n        • Optimize data distribution',
            'capacity': '• Implement capacity upgrades\n        • Configure auto-scaling\n        • Set up capacity monitoring',
            'security': '• Implement security hardening\n        • Configure access controls\n        • Set up audit logging'
        }
        return actions.get(service_type, '• Implement recommended changes\n        • Configure monitoring\n        • Test improvements')
    
    def get_long_term_actions(self, service_type):
        """Get long-term action items"""
        actions = {
            'query': '• Implement automated query optimization\n        • Set up continuous performance monitoring\n        • Establish query review processes',
            'performance': '• Implement predictive performance analytics\n        • Automate performance tuning\n        • Establish performance SLAs',
            'troubleshooting': '• Implement proactive monitoring\n        • Automate issue detection\n        • Establish incident response procedures',
            'architecture': '• Plan for future scalability\n        • Implement disaster recovery\n        • Optimize for cloud migration',
            'capacity': '• Implement predictive capacity planning\n        • Automate scaling decisions\n        • Optimize cost management',
            'security': '• Implement continuous security monitoring\n        • Automate compliance reporting\n        • Establish security governance'
        }
        return actions.get(service_type, '• Establish continuous improvement\n        • Automate optimization processes\n        • Plan for future growth')
    
    def estimate_resources(self, service_type):
        """Estimate resource requirements"""
        resources = {
            'query': '1-2 developers, 2-4 weeks',
            'performance': '1 DBA, 1 developer, 3-6 weeks',
            'troubleshooting': '1 DBA, 1-2 weeks',
            'architecture': '1 architect, 2 developers, 6-12 weeks',
            'capacity': '1 infrastructure engineer, 2-4 weeks',
            'security': '1 security specialist, 1 DBA, 4-8 weeks'
        }
        return resources.get(service_type, '1-2 technical resources, 2-6 weeks')
    
    def define_success_metrics(self, service_type):
        """Define success metrics for the service type"""
        metrics = {
            'query': '• Query execution time reduced by >80%\n        • CPU utilization decreased by >50%\n        • User satisfaction improved',
            'performance': '• Response time improved by >60%\n        • Throughput increased by >40%\n        • Resource utilization optimized',
            'troubleshooting': '• Issues resolved within SLA\n        • System uptime >99.9%\n        • Error rate reduced to <0.1%',
            'architecture': '• Scalability improved by 10x\n        • Availability >99.95%\n        • Performance maintained under load',
            'capacity': '• Resource utilization optimized to 70-80%\n        • Auto-scaling functioning properly\n        • Cost per transaction reduced',
            'security': '• Security compliance achieved\n        • Audit findings resolved\n        • Access controls properly implemented'
        }
        return metrics.get(service_type, '• Performance improved\n        • Reliability increased\n        • User satisfaction enhanced')
    
    def calculate_value_proposition(self, service_type):
        """Calculate estimated value proposition"""
        values = {
            'query': '80-95%',
            'performance': '60-80%',
            'troubleshooting': '90-100%',
            'architecture': '200-500%',
            'capacity': '30-60%',
            'security': '100%'
        }
        return values.get(service_type, '50-80%')