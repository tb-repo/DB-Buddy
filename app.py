from flask import Flask, request, jsonify, render_template
import json
import requests
import os
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

class DBBuddy:
    def __init__(self):
        self.conversations = {}
        self.use_ai = self.check_ollama_available()
        self.question_flows = {
            'troubleshooting': [
                """👋 **Welcome to Database Troubleshooting!**

🔧 **Quick Start:**
1. Use the dropdowns above to select your deployment, database system, and environment
2. Click "Insert" to add your selections
3. Describe your specific issue or error

I'll provide targeted diagnostic queries and solutions based on your setup!"""
            ],
            'query': [
                """👋 **Welcome to Query Optimization!**

⚡ **Quick Start:**
1. Use the dropdowns above to select your deployment and database system
2. Click "Insert" to add your selections
3. Paste your SQL query and describe the performance issue

I'll analyze your query and provide optimization recommendations!"""
            ],
            'performance': [
                """👋 **Welcome to Performance Analysis!**

📊 **Quick Start:**
1. Use the dropdowns above to select your deployment and database system
2. Click "Insert" to add your selections
3. Describe your performance symptoms (slow queries, high CPU, etc.)

I'll provide diagnostic queries and tuning recommendations!"""
            ],
            'architecture': [
                """👋 **Welcome to Architecture Design!**

🏗️ **Quick Start:**
1. Use the dropdowns above to select your preferred deployment and database system
2. Click "Insert" to add your selections
3. Describe your application type and expected scale

I'll design an optimal database architecture for your needs!"""
            ],
            'capacity': [
                """👋 **Welcome to Capacity Planning!**

📈 **Quick Start:**
1. Use the dropdowns above to select your deployment and database system
2. Click "Insert" to add your selections
3. Share your current/expected data size and user load

I'll provide hardware sizing and scaling recommendations!"""
            ],
            'security': [
                """👋 **Welcome to Database Security!**

🔒 **Quick Start:**
1. Use the dropdowns above to select your deployment and database system
2. Click "Insert" to add your selections
3. Describe your security concerns and compliance needs

I'll provide security hardening and compliance guidance!"""
            ]
        }
    
    def check_ollama_available(self):
        import os
        # Check for Groq API key first (best for multi-user)
        if os.getenv('GROQ_API_KEY'):
            return 'groq'
        
        # Check for Hugging Face API key
        if os.getenv('HUGGINGFACE_API_KEY'):
            return 'huggingface'
        
        # Check for local Ollama
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.status_code == 200:
                return 'ollama'
        except:
            pass
        return False
    
    def get_ai_response(self, context, user_input, user_selections=None):
        if not self.use_ai:
            return None
        
        # Build enhanced context with user selections
        enhanced_context = context
        if user_selections:
            selection_context = "\n\nUser's System Configuration:\n"
            if user_selections.get('deployment'):
                selection_context += f"• Deployment: {user_selections['deployment']}\n"
            if user_selections.get('cloud_provider'):
                selection_context += f"• Cloud Provider: {user_selections['cloud_provider']}\n"
            if user_selections.get('database'):
                selection_context += f"• Database System: {user_selections['database']}\n"
            if user_selections.get('environment'):
                selection_context += f"• Environment: {user_selections['environment']}\n"
            if user_selections.get('issue_type'):
                selection_context += f"• Issue Type: {user_selections['issue_type']}\n"
            enhanced_context += selection_context
        
        # Build cloud-specific guidance
        cloud_guidance = ""
        if user_selections and user_selections.get('deployment') == 'Cloud':
            cloud_provider = user_selections.get('cloud_provider', '')
            db_system = user_selections.get('database', '')
            
            if 'AWS' in cloud_provider:
                if 'Aurora' in db_system:
                    cloud_guidance = "\n\nAWS AURORA SPECIFIC GUIDANCE:\n- Use DB Parameter Groups (not ALTER SYSTEM) for configuration changes\n- Monitor via CloudWatch metrics and Performance Insights\n- Use Aurora-specific features like Global Database, Backtrack, Serverless\n- Consider Aurora Auto Scaling for read replicas\n- Use RDS Proxy for connection pooling\n"
                elif 'RDS' in db_system:
                    cloud_guidance = "\n\nAWS RDS SPECIFIC GUIDANCE:\n- Use DB Parameter Groups for configuration changes\n- Monitor via CloudWatch and Enhanced Monitoring\n- Use Read Replicas for scaling reads\n- Consider Multi-AZ for high availability\n- Use RDS Proxy for connection management\n"
            elif 'Azure' in cloud_provider:
                cloud_guidance = "\n\nAZURE DATABASE SPECIFIC GUIDANCE:\n- Use Azure Database configuration settings (not direct SQL commands)\n- Monitor via Azure Monitor and Query Performance Insight\n- Use Read Replicas and Hyperscale for scaling\n- Consider Azure SQL Database Serverless\n- Use connection pooling via application or Azure SQL Database\n"
            elif 'GCP' in cloud_provider:
                cloud_guidance = "\n\nGCP CLOUD SQL SPECIFIC GUIDANCE:\n- Use Cloud SQL configuration flags (not ALTER SYSTEM)\n- Monitor via Cloud Monitoring and Query Insights\n- Use Read Replicas for read scaling\n- Consider Cloud SQL Proxy for secure connections\n- Use connection pooling at application level\n"
        
        system_prompt = f"""You are DB-Buddy, a senior database architect and performance specialist with deep expertise across all major database systems.

IMPORTANT: Always consider the user's specific system configuration when providing recommendations. Tailor your advice to their exact database system, deployment type, and environment.

CLOUD DATABASE CONSIDERATIONS:
- For managed cloud databases (RDS, Aurora, Azure SQL, Cloud SQL), configuration changes are done via cloud console/CLI, not direct SQL commands
- Parameter groups, configuration flags, and service-specific settings control database behavior
- Cloud monitoring tools provide better insights than traditional database queries
- Scaling, backup, and maintenance are handled differently in cloud environments{cloud_guidance}

Work with whatever information users provide, even if incomplete:
1. **Analyze available information** and provide immediate recommendations
2. **Provide diagnostic queries** to gather missing critical data
3. **Give specific, executable solutions** based on what you know
4. **Include monitoring queries** to verify improvements

Database-specific diagnostic commands:
- MySQL/Aurora MySQL: EXPLAIN, SHOW INDEX, SHOW TABLE STATUS, SHOW PROCESSLIST
- PostgreSQL/Aurora PostgreSQL: EXPLAIN ANALYZE, \d+ table, pg_stat_user_tables, pg_stat_activity
- SQL Server: SET STATISTICS IO ON, sys.dm_exec_query_stats, sp_helpindex
- Oracle: EXPLAIN PLAN, DBMS_XPLAN, USER_INDEXES, V$SQL
- Cloud-specific: Use cloud monitoring tools and service-specific commands

Response format:
1. **🔍 Diagnostic Queries**: To gather missing data (if needed)
2. **📊 Analysis**: Based on available information
3. **⚡ Immediate Actions**: What they can do right now
4. **📈 Verification**: How to confirm improvements
5. **🛡️ Next Steps**: Additional recommendations"""
        
        if self.use_ai == 'groq':
            return self.get_groq_response(system_prompt, enhanced_context, user_input)
        elif self.use_ai == 'huggingface':
            return self.get_huggingface_response(system_prompt, enhanced_context, user_input)
        elif self.use_ai == 'ollama':
            return self.get_ollama_response(system_prompt, enhanced_context, user_input)
        return None
    
    def get_huggingface_response(self, system_prompt, context, user_input):
        import os
        try:
            prompt = f"""{system_prompt}

Context: {context}
User situation: {user_input}

Provide your expert database recommendations:"""
            
            headers = {
                'Authorization': f'Bearer {os.getenv("HUGGINGFACE_API_KEY")}',
                'Content-Type': 'application/json'
            }
            
            # Using Microsoft DialoGPT or similar free model
            response = requests.post(
                'https://api-inference.huggingface.co/models/microsoft/DialoGPT-large',
                headers=headers,
                json={'inputs': prompt[:1000]},  # Limit input size
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').replace(prompt, '').strip()
        except:
            pass
        return None
    
    def get_groq_response(self, system_prompt, context, user_input):
        import os
        try:
            headers = {
                'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'llama3-8b-8192',  # Fast Groq model
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Database consultation request:\n\nContext: {context}\nUser details: {user_input}\n\nWork with the information provided (even if partial). If critical details are missing, provide diagnostic queries to gather that data. Give your best recommendations based on available information and be proactive in helping the user."}
                ],
                'temperature': 0.1,
                'max_tokens': 800
            }
            
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Groq API error: {e}")
            pass
        return None
    
    def get_ollama_response(self, system_prompt, context, user_input):
        try:
            prompt = f"""{system_prompt}

Context: {context}
User situation: {user_input}

Provide your expert database recommendations:"""
            
            response = requests.post('http://localhost:11434/api/generate',
                json={
                    'model': 'llama3.2:3b',
                    'prompt': prompt,
                    'stream': False,
                    'options': {'temperature': 0.3, 'num_predict': 300}
                }, timeout=45)
            
            if response.status_code == 200:
                return response.json().get('response', '').strip()
        except:
            pass
        return None
    
    def get_ai_followup_or_recommendation(self, conv):
        if not self.use_ai:
            return self.generate_recommendation(conv)
        
        try:
            context = f"""User is seeking help with {conv['type']}. 
Conversation so far:
{chr(10).join([f"Q{i+1}: {q}" for i, q in enumerate(self.question_flows[conv['type']][:conv['step']])])}
{chr(10).join([f"A{i+1}: {a}" for i, a in enumerate(conv['answers'])])}

Decide if you need more information or can provide recommendations now."""
            
            prompt = f"""You are DB-Buddy, a database expert analyzing a technical consultation.

{context}

Evaluate the user's input:

1. If they provided an SQL query, table schema, or specific technical details, respond with "READY_FOR_RECOMMENDATIONS" - you have enough to provide diagnostic queries and initial analysis.

2. If their response is too vague or missing critical information (like database system, specific query, or error details), ask ONE focused follow-up question.

Prioritize being helpful immediately. Most database issues can be analyzed with diagnostic queries.

Your response:"""
            
            if self.use_ai == 'groq':
                # Use Groq for dynamic follow-ups
                return self.get_groq_followup(context, conv)
            elif self.use_ai == 'huggingface':
                # Simplified for HuggingFace API
                return f"📋 **Analyzing your requirements...**\n\n" + self.generate_recommendation(conv)
            
            response = requests.post('http://localhost:11434/api/generate',
                json={
                    'model': 'llama3.2:3b',
                    'prompt': prompt,
                    'stream': False,
                    'options': {'temperature': 0.2, 'num_predict': 150}
                }, timeout=30)
            
            if response.status_code == 200:
                ai_response = response.json().get('response', '').strip()
                if "READY_FOR_RECOMMENDATIONS" in ai_response.upper():
                    return f"🔍 **Analyzing your requirements...**\n\n" + self.generate_recommendation(conv)
                else:
                    return f"{ai_response}\n\n📋 Progress: Gathering details for thorough analysis"
        except:
            pass
        
        # Fallback to recommendations if AI fails
        return f"🔍 **Analyzing your requirements...**\n\n" + self.generate_recommendation(conv)
    
    def get_groq_followup(self, context, conv):
        import os
        try:
            headers = {
                'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}',
                'Content-Type': 'application/json'
            }
            
            prompt = f"""You are DB-Buddy, analyzing a database consultation.

{context}

Based on the conversation, you have two options:

1. If you need MORE specific information to provide quality recommendations, ask ONE focused follow-up question that will help you give better advice.

2. If you have ENOUGH information, respond with "READY_FOR_RECOMMENDATIONS" and I'll generate the final analysis.

Choose option 1 if the user's answers are vague or you need technical details. Choose option 2 if you can provide solid recommendations."""
            
            payload = {
                'model': 'llama3-8b-8192',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.1,
                'max_tokens': 150
            }
            
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                if "READY_FOR_RECOMMENDATIONS" in ai_response.upper():
                    return f"🔍 **Analyzing your requirements...**\n\n" + self.generate_recommendation(conv)
                else:
                    return f"{ai_response}\n\n📋 Progress: Gathering details for thorough analysis"
        except:
            pass
        
        return f"🔍 **Analyzing your requirements...**\n\n" + self.generate_recommendation(conv)
    
    def start_conversation(self, session_id, issue_type):
        self.conversations[session_id] = {
            'type': issue_type,
            'step': 0,
            'answers': [],
            'user_selections': {},
            'timestamp': datetime.now()
        }
        
        greetings = {
            'troubleshooting': "👋 Hi! I'm here to help you troubleshoot database issues. Let's work together to identify and resolve your problem.\n\n",
            'query': "👋 Hello! I'll help you optimize your SQL queries for better performance. Please share your query details with me.\n\n",
            'performance': "👋 Welcome! I'll assist you in analyzing and improving your database performance. Let's dive into the details.\n\n",
            'architecture': "👋 Great choice! I'll help you design a robust database architecture. Let's discuss your requirements.\n\n",
            'capacity': "👋 Hi there! I'll help you plan the right capacity for your database needs. Let's gather some information.\n\n",
            'security': "👋 Hello! I'll guide you through database security and compliance best practices. Let's get started.\n\n"
        }
        
        greeting = greetings.get(issue_type, "👋 Hello! ")
        return greeting + self.question_flows[issue_type][0]
    
    def contains_lov_selections(self, user_input):
        """Check if user input contains LOV selections"""
        lov_keywords = ['Deployment:', 'Database System:', 'Cloud Provider:', 'Environment:', 'Issue Type:']
        return any(keyword in user_input for keyword in lov_keywords)
    
    def parse_lov_selections(self, user_input):
        """Parse LOV selections from user input"""
        selections = {}
        lines = user_input.split('\n')
        
        for line in lines:
            if 'Deployment:' in line:
                selections['deployment'] = line.split('Deployment:')[1].strip()
            elif 'Database System:' in line:
                selections['database'] = line.split('Database System:')[1].strip()
            elif 'Cloud Provider:' in line:
                selections['cloud_provider'] = line.split('Cloud Provider:')[1].strip()
            elif 'Environment:' in line:
                selections['environment'] = line.split('Environment:')[1].strip()
            elif 'Issue Type:' in line:
                selections['issue_type'] = line.split('Issue Type:')[1].strip()
        
        return selections
    
    def get_follow_up_questions(self, category, user_selections):
        """Generate context-aware follow-up questions based on user selections"""
        deployment = user_selections.get('deployment', '')
        db_system = user_selections.get('database', '')
        environment = user_selections.get('environment', '')
        cloud_provider = user_selections.get('cloud_provider', '')
        
        # Build context string
        context_parts = []
        if db_system:
            context_parts.append(db_system)
        if deployment:
            if deployment.lower() == 'cloud' and cloud_provider:
                context_parts.append(f"{cloud_provider} {deployment.lower()}")
            else:
                context_parts.append(deployment.lower())
        if environment:
            context_parts.append(f"{environment.lower()} environment")
        
        if context_parts:
            base_context = f"Perfect! I see you're working with {' in '.join(context_parts)}.\n\n"
        else:
            base_context = "Thanks for the details! \n\n"
        
        if category == 'troubleshooting':
            return base_context + """**Now tell me about your issue:**
• What error message or symptoms are you seeing?
• When does this happen? (always/sometimes/specific times)
• Any recent changes made?"""
        
        elif category == 'query':
            return base_context + """**Now share your query details:**
• Paste your SQL query here
• What's the performance issue? (slow/error/timeout)
• Current execution time (if known)"""
        
        elif category == 'performance':
            return base_context + """**Now describe your performance issues:**
• What symptoms are you seeing? (slow queries/high CPU/memory)
• When do these issues occur?
• Any current metrics you have?"""
        
        elif category == 'architecture':
            return base_context + """**Now share your requirements:**
• Application type (web app/analytics/e-commerce)
• Expected data volume (GB/TB)
• Expected concurrent users"""
        
        elif category == 'capacity':
            return base_context + """**Now share your capacity needs:**
• Current/expected data size
• Peak user count
• Workload type (OLTP/OLAP/mixed)"""
        
        elif category == 'security':
            return base_context + """**Now share your security needs:**
• Data sensitivity level (public/internal/confidential)
• Specific security concerns
• Compliance requirements (GDPR/HIPAA/SOX/PCI-DSS)"""
        
        return base_context + "Please share more details about your specific needs."
    
    def process_answer(self, session_id, answer):
        if session_id not in self.conversations:
            return "Session not found. Please start a new conversation."
        
        conv = self.conversations[session_id]
        
        # Initialize user_selections if not exists
        if 'user_selections' not in conv:
            conv['user_selections'] = {}
        
        conv['answers'].append(answer)
        conv['step'] += 1
        
        # Check if user provided LOV selections
        if self.contains_lov_selections(answer):
            selections = self.parse_lov_selections(answer)
            conv['user_selections'].update(selections)
            follow_up = self.get_follow_up_questions(conv['type'], conv['user_selections'])
            return follow_up
        
        # If we have selections and this is detailed input, generate recommendations
        if conv['user_selections'] or conv['step'] >= 2:
            return f"🔍 **Analyzing your requirements...**\n\n" + self.generate_recommendation(conv)
        
        # Default fallback
        return self.generate_recommendation(conv)
    
    def generate_recommendation(self, conv):
        issue_type = conv['type']
        answers = conv['answers']
        
        # Try AI first if available
        if self.use_ai:
            issue_contexts = {
                'troubleshooting': f'Database troubleshooting consultation',
                'query': f'SQL query optimization consultation',
                'performance': f'Database performance optimization consultation',
                'architecture': f'Database architecture design consultation',
                'capacity': f'Database capacity planning consultation',
                'security': f'Database security hardening consultation'
            }
            
            # Since user provided comprehensive details upfront, we have rich context
            context = f"{issue_contexts.get(issue_type, issue_type)}. User provided details: {answers[0] if answers else 'No details provided'}"
            user_selections = conv.get('user_selections', {})
            ai_response = self.get_ai_response(context, f"User provided {issue_type} details (may be partial). Work with available information and provide diagnostic queries to gather missing data if needed. Give actionable solutions based on what they shared.", user_selections)
            if ai_response:
                return f"## 🔧 **Database Analysis & Recommendations**\n\n{ai_response}\n\n---\n**📞 Next Step:** Execute any diagnostic queries above, then consult your DBA team for production implementation."
        
        # Fallback to rule-based recommendations
        if issue_type == 'troubleshooting':
            return self.troubleshooting_recommendation(answers)
        elif issue_type == 'query':
            return self.query_recommendation(answers)
        elif issue_type == 'performance':
            return self.performance_recommendation(answers)
        elif issue_type == 'architecture':
            return self.architecture_recommendation(answers)
        elif issue_type == 'capacity':
            return self.capacity_recommendation(answers)
        elif issue_type == 'security':
            return self.security_recommendation(answers)
    
    def troubleshooting_recommendation(self, answers):
        # Handle variable number of answers
        db_system = answers[0] if len(answers) > 0 else 'Unknown'
        issue_type = answers[1] if len(answers) > 1 else 'General issue'
        timing = answers[2] if len(answers) > 2 else 'Recently'
        symptoms = answers[3] if len(answers) > 3 else 'Performance degradation'
        
        recommendations = []
        
        if 'slow' in issue_type.lower():
            recommendations.extend(["• Check query execution plans", "• Review missing indexes", "• Analyze table statistics", "• Set up query performance monitoring"])
        if 'connection' in issue_type.lower():
            recommendations.extend(["• Check connection pool settings", "• Review network connectivity", "• Verify authentication", "• Monitor connection metrics"])
        if 'crash' in issue_type.lower():
            recommendations.extend(["• Check error logs immediately", "• Review system resources", "• Verify database integrity", "• Ensure automated backups are current"])
        if 'corruption' in issue_type.lower():
            recommendations.extend(["• Stop write operations", "• Run integrity checks", "• Restore from backup if needed", "• Review backup validation procedures"])
        
        return f"Troubleshooting recommendations for {db_system}:\n" + "\n".join(recommendations) + f"\n\nIssue started: {timing}\nSymptoms: {symptoms}\n\nBest practices: Implement automated monitoring and regular backup testing.\nNext steps: Contact DBA team if issue persists or is critical."
    
    def query_recommendation(self, answers):
        # Handle variable number of answers
        db_system = answers[0] if len(answers) > 0 else 'Unknown'
        query_type = answers[1] if len(answers) > 1 else 'SELECT'
        data_size = answers[2] if len(answers) > 2 else 'Unknown'
        performance_issue = answers[3] if len(answers) > 3 else 'General optimization'
        
        recommendations = {
            'SELECT': ["• Add indexes on WHERE/ORDER BY columns", "• Use LIMIT for large result sets", "• Avoid SELECT * in production", "• Monitor query execution time"],
            'JOIN': ["• Index all join columns", "• Use appropriate join types", "• Consider query execution order", "• Set up slow query logging"],
            'INSERT': ["• Use batch inserts for multiple rows", "• Consider bulk insert methods", "• Optimize during low-traffic periods", "• Monitor transaction log growth"],
            'UPDATE': ["• Use indexed WHERE clauses", "• Update in smaller batches", "• Consider impact on concurrent users", "• Schedule maintenance windows for large updates"],
            'DELETE': ["• Use indexed WHERE clauses", "• Delete in batches for large datasets", "• Consider archiving instead of deleting", "• Implement data retention policies"]
        }
        
        base_recs = recommendations.get(query_type.upper(), ["• Follow general optimization practices"])
        return f"Query optimization for {db_system} {query_type} operations:\n" + "\n".join(base_recs) + f"\n\nData size: {data_size}\nPerformance concern: {performance_issue}\n\nBest practices: Implement query monitoring, regular index maintenance, and automated performance alerts.\nRecommendation: Test changes in development environment first."
    
    def performance_recommendation(self, answers):
        # Handle variable number of answers
        db_system = answers[0] if len(answers) > 0 else 'Unknown'
        issue_type = answers[1] if len(answers) > 1 else 'General performance'
        db_size = answers[2] if len(answers) > 2 else 'Unknown'
        query_details = answers[3] if len(answers) > 3 else 'No specific details'
        
        recommendations = []
        
        if 'slow' in issue_type.lower():
            recommendations.extend(["• Analyze query execution plans", "• Check for missing indexes", "• Consider query optimization", "• Set up automated performance monitoring"])
        
        if 'cpu' in issue_type.lower():
            recommendations.extend(["• Review expensive queries", "• Check for table scans", "• Consider connection pooling", "• Implement CPU usage alerts"])
        
        if 'memory' in issue_type.lower():
            recommendations.extend(["• Review buffer pool settings", "• Check for memory leaks", "• Optimize sort operations", "• Monitor memory usage trends"])
        
        if 'response' in issue_type.lower() or 'time' in issue_type.lower():
            recommendations.extend(["• Set up response time monitoring", "• Implement query timeout settings", "• Review connection handling"])
        
        return f"Performance recommendations for {db_system}:\n" + "\n".join(recommendations) + f"\n\nDatabase size: {db_size}\nQuery details: {query_details}\n\nBest practices: Establish performance baselines, set up automated alerts, and schedule regular maintenance windows.\nConsider consulting DBA team for detailed analysis."
    
    def architecture_recommendation(self, answers):
        # Handle variable number of answers
        db_system = answers[0] if len(answers) > 0 else 'Unknown'
        app_type = answers[1] if len(answers) > 1 else 'General application'
        data_volume = answers[2] if len(answers) > 2 else 'Unknown'
        guidance_type = answers[3] if len(answers) > 3 else 'General guidance'
        
        recommendations = []
        
        if 'schema' in guidance_type.lower():
            recommendations.extend(["• Normalize to 3NF for OLTP systems", "• Use appropriate data types", "• Plan for future growth", "• Document schema changes and versioning"])
        if 'partition' in guidance_type.lower():
            recommendations.extend(["• Consider horizontal partitioning for large tables", "• Use date-based partitioning for time-series data", "• Plan partition maintenance", "• Automate partition management"])
        if 'replication' in guidance_type.lower():
            recommendations.extend(["• Set up read replicas for read-heavy workloads", "• Consider geographic distribution", "• Plan failover procedures", "• Test disaster recovery regularly"])
        
        # Add general architecture best practices
        recommendations.extend(["• Implement automated backup strategies", "• Plan for database version upgrades", "• Design for cost optimization"])
        
        return f"Architecture recommendations for {db_system} ({app_type}):\n" + "\n".join(recommendations) + f"\n\nData volume: {data_volume}\nGuidance needed: {guidance_type}\n\nBest practices: Implement automated backups, regular disaster recovery testing, and maintain upgrade roadmaps.\nRecommendation: Review with DBA team before implementation."
    
    def capacity_recommendation(self, answers):
        # Handle variable number of answers
        db_system = answers[0] if len(answers) > 0 else 'Unknown'
        data_volume = answers[1] if len(answers) > 1 else 'Unknown'
        users = answers[2] if len(answers) > 2 else '10'
        workload = answers[3] if len(answers) > 3 else 'Mixed'
        
        base_specs = {
            'small': {'cpu': '4-8 cores', 'memory': '16GB', 'storage': '200GB SSD'},
            'medium': {'cpu': '8-16 cores', 'memory': '32GB', 'storage': '1TB SSD'},
            'large': {'cpu': '16-32 cores', 'memory': '64GB+', 'storage': '2TB+ SSD'}
        }
        
        try:
            user_count = int(users.split()[0]) if users.split() else 10
        except:
            user_count = 10
            
        if 'TB' in data_volume or user_count > 100:
            size = 'large'
        elif 'GB' in data_volume and user_count > 50:
            size = 'medium'
        else:
            size = 'small'
        
        specs = base_specs[size]
        
        return f"Capacity planning for {db_system}:\n• CPU: {specs['cpu']}\n• Memory: {specs['memory']}\n• Storage: {specs['storage']}\n• Consider 30% growth buffer\n• Plan backup storage (3x data size)\n• Set up monitoring and alerting\n• Implement automated scaling policies\n\nWorkload: {workload}\nUsers: {users}\nData: {data_volume}\n\nBest practices: Regular capacity reviews, cost optimization monitoring, and automated backup testing.\nRecommendation: Plan for 2-3 years growth and consult DBA for production sizing."
    
    def security_recommendation(self, answers):
        # Handle variable number of answers
        db_system = answers[0] if len(answers) > 0 else 'Unknown'
        security_aspects = answers[1] if len(answers) > 1 else 'General security'
        compliance = answers[2] if len(answers) > 2 else 'No specific compliance'
        user_mgmt = answers[3] if len(answers) > 3 else 'Basic user management'
        
        recommendations = []
        
        if 'access' in security_aspects.lower():
            recommendations.extend(["• Implement role-based access control", "• Use principle of least privilege", "• Regular access reviews", "• Automated user provisioning/deprovisioning"])
        if 'encryption' in security_aspects.lower():
            recommendations.extend(["• Enable encryption at rest", "• Use TLS for data in transit", "• Manage encryption keys securely", "• Regular key rotation policies"])
        if 'audit' in security_aspects.lower():
            recommendations.extend(["• Enable database audit logging", "• Monitor privileged operations", "• Set up log retention policies", "• Automated security alerting"])
        
        # Add general security best practices
        recommendations.extend(["• Regular security assessments", "• Backup encryption and testing", "• Database version security updates"])
        
        return f"Security recommendations for {db_system}:\n" + "\n".join(recommendations) + f"\n\nCompliance: {compliance}\nUser management: {user_mgmt}\n\nBest practices: Regular security audits, automated backup testing, patch management, and incident response planning.\nRecommendation: Work with security team for compliance requirements."

db_buddy = DBBuddy()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_conversation():
    data = request.json
    session_id = data.get('session_id')
    issue_type = data.get('issue_type')
    
    if issue_type not in ['troubleshooting', 'query', 'performance', 'architecture', 'capacity', 'security']:
        return jsonify({'error': 'Invalid issue type'}), 400
    
    question = db_buddy.start_conversation(session_id, issue_type)
    ai_status = "🤖 AI-Enhanced" if db_buddy.use_ai else "📋 Rule-Based"
    return jsonify({'question': question, 'ai_status': ai_status})

@app.route('/answer', methods=['POST'])
def process_answer():
    data = request.json
    session_id = data.get('session_id')
    answer = data.get('answer')
    
    response = db_buddy.process_answer(session_id, answer)
    return jsonify({'response': response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)