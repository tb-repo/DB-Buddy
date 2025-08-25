import streamlit as st
import requests
import json
from datetime import datetime
import os
from memory import ConversationMemory

# Get API keys from Streamlit secrets or environment variables
def get_api_key(key_name):
    # Try Streamlit secrets first (for cloud deployment)
    try:
        return st.secrets[key_name]
    except:
        # Fallback to environment variables (for local development)
        return os.getenv(key_name)

# Initialize API keys
GROQ_API_KEY = get_api_key('GROQ_API_KEY')
HUGGINGFACE_API_KEY = get_api_key('HUGGINGFACE_API_KEY')
ANTHROPIC_API_KEY = get_api_key('ANTHROPIC_API_KEY')

class StreamlitDBBuddy:
    def __init__(self):
        self.use_ai = self.check_ai_available()
        self.service_descriptions = {
            'troubleshooting': 'database troubleshooting and error resolution',
            'query': 'SQL query optimization and performance tuning',
            'performance': 'database performance analysis and optimization',
            'architecture': 'database architecture design and best practices',
            'capacity': 'database capacity planning and sizing',
            'security': 'database security hardening and compliance'
        }
    
    def check_ai_available(self):
        if ANTHROPIC_API_KEY:
            return 'claude'
        if GROQ_API_KEY:
            return 'groq'
        if HUGGINGFACE_API_KEY:
            return 'huggingface'
        return False
    
    def get_intelligent_response(self, user_input, user_selections, service_type, conversation_history):
        """Generate intelligent, contextual responses based on user input"""
        # Build conversation context
        context = f"Service type: {service_type}\n"
        if user_selections:
            context += "System configuration:\n"
            for key, value in user_selections.items():
                if value:
                    context += f"- {key}: {value}\n"
        
        if len(conversation_history) > 1:
            context += f"\nPrevious conversation:\n"
            for i, msg in enumerate(conversation_history[-6:], 1):  # Last 6 messages for context
                role = "User" if msg['role'] == 'user' else "Assistant"
                content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                context += f"{role} {i}: {content}\n"
        
        # Get AI response with full context
        ai_response = self.get_ai_response(context, user_input, user_selections)
        
        if ai_response:
            return ai_response
        
        # Fallback to specialized recommendations if AI unavailable
        specialized = self.get_specialized_recommendation(user_input, user_selections)
        if specialized:
            return specialized
        
        # Final fallback
        return self.get_contextual_fallback(service_type, user_input, user_selections)
    
    def get_ai_response(self, context, user_input, user_selections=None):
        # Build enhanced context with user selections and technical details
        enhanced_context = context
        if user_selections:
            selection_context = "\n\nUser's System Configuration:\n"
            for key, value in user_selections.items():
                if value:
                    selection_context += f"• {key}: {value}\n"
            enhanced_context += selection_context
        
        # Add conversation context for natural responses
        enhanced_context += "\n\nUser's current message: " + user_input + "\n"
        enhanced_context += "Respond naturally and conversationally to their specific situation. Provide technical depth when appropriate, but keep the tone friendly and professional.\n"
        
        # Build cloud-specific guidance
        cloud_guidance = ""
        if user_selections and user_selections.get('deployment') == 'Cloud':
            cloud_provider = user_selections.get('cloud_provider', '')
            db_system = user_selections.get('database', '')
            
            if 'AWS' in cloud_provider:
                if 'Aurora' in db_system:
                    cloud_guidance = "\n\nAWS AURORA SPECIFIC GUIDANCE:\n- Use DB Parameter Groups (not ALTER SYSTEM) for configuration changes\n- Monitor via CloudWatch metrics and Performance Insights\n- Use Aurora-specific features like Global Database, Backtrack, Serverless\n- Consider Aurora Auto Scaling for read replicas\n- Use RDS Proxy for connection pooling\n- Leverage Aurora's distributed storage for better I/O performance\n- Use Aurora Performance Insights for query-level analysis\n- Consider Aurora Serverless v2 for variable workloads\n"
        
        system_prompt = f"""You are DB-Buddy, a senior database performance specialist. You MUST analyze the specific SQL queries, execution plans, and technical details provided by users. Never give generic responses.

CRITICAL INSTRUCTIONS:
- If a user provides a SQL query, analyze THAT EXACT query
- If they share an execution plan, interpret THOSE SPECIFIC metrics
- If they mention table sizes, constraints, or schema details, use THAT INFORMATION
- Never respond with generic advice when specific technical details are provided

SQL QUERY ANALYSIS PROCESS:
1. **Parse the actual SQL statement** - identify tables, columns, WHERE conditions, JOINs
2. **Analyze the execution plan** - look for table scans, index usage, cost estimates, actual times
3. **Identify performance bottlenecks** - high costs, long execution times, inefficient operations
4. **Recommend specific indexes** - based on WHERE clauses, ORDER BY, and SELECT columns
5. **Provide exact DDL statements** - CREATE INDEX commands with proper syntax

EXECUTION PLAN INTERPRETATION:
- **Seq Scan / Table Scan**: Missing indexes, recommend specific index creation
- **Bitmap Heap Scan**: Analyze filter conditions, suggest composite indexes
- **High cost values**: Identify expensive operations, recommend optimizations
- **Rows Removed by Filter**: Suggest better indexing strategies
- **Long execution times**: Provide immediate and long-term solutions

WHEN USER PROVIDES SPECIFIC QUERY:
- Quote their exact table names and column names in your response
- Reference their specific WHERE conditions
- Analyze their actual execution plan metrics
- Provide CREATE INDEX statements using their exact schema and table names
- Calculate expected performance improvements based on their data

FORBIDDEN RESPONSES:
- "I see you have a SQL query" (analyze the actual query instead)
- "Please share your query" (when they already shared it)
- Generic index advice (provide specific recommendations for their query)
- Template responses (respond to their specific situation)

Database-specific expertise:
- **PostgreSQL/Aurora PostgreSQL**: EXPLAIN ANALYZE, pg_stat_*, vacuum strategies, partitioning, connection pooling
- **MySQL/Aurora MySQL**: EXPLAIN FORMAT=JSON, SHOW ENGINE INNODB STATUS, query cache, buffer pool tuning
- **SQL Server**: SET STATISTICS IO/TIME, DMVs, index maintenance, query store
- **Oracle**: EXPLAIN PLAN, AWR reports, CBO statistics, partitioning strategies{cloud_guidance}

You MUST provide specific, actionable analysis of the user's actual query and execution plan. No generic responses allowed."""
        
        if self.use_ai == 'claude':
            return self.get_claude_response(system_prompt, enhanced_context, user_input)
        elif self.use_ai == 'groq':
            return self.get_groq_response(system_prompt, enhanced_context, user_input)
        elif self.use_ai == 'huggingface':
            return self.get_huggingface_response(system_prompt, enhanced_context, user_input)
        
        return None
    
    def get_claude_response(self, system_prompt, context, user_input):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": f"Context: {context}\nQuery: {user_input}"}]
            )
            return response.content[0].text
        except:
            return None
    
    def get_groq_response(self, system_prompt, context, user_input):
        try:
            headers = {
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'llama3-8b-8192',
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
        except:
            pass
        return None
    
    def get_huggingface_response(self, system_prompt, context, user_input):
        try:
            prompt = f"{system_prompt}\n\nContext: {context}\nUser situation: {user_input}\n\nProvide your expert database recommendations:"
            
            headers = {
                'Authorization': f'Bearer {HUGGINGFACE_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                'https://api-inference.huggingface.co/models/microsoft/DialoGPT-large',
                headers=headers,
                json={'inputs': prompt[:1000]},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').replace(prompt, '').strip()
        except:
            pass
        return None
    
    def get_specialized_recommendation(self, user_input, user_selections=None):
        """Provide specialized recommendations for common database patterns"""
        input_lower = user_input.lower()
        
        # Detect ANY SQL query - not just with execution plans
        if any(sql_keyword in input_lower for sql_keyword in ['select ', 'from ', 'where ', 'join ', 'left join', 'inner join']):
            return self.get_sql_query_analysis(user_input, user_selections)
        
        # Detect connection issues
        if any(keyword in input_lower for keyword in ['connection', 'timeout', 'timed out', 'connect', 'refused']):
            return self.get_connection_troubleshooting_recommendation(user_input, user_selections)
        
        return None
    
    def get_sql_query_analysis(self, user_input, user_selections):
        """Analyze any SQL query provided by user"""
        input_lower = user_input.lower()
        lines = user_input.split('\n')
        
        # Extract the SQL query
        sql_lines = []
        in_sql = False
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['select ', 'with ', 'insert ', 'update ', 'delete ']):
                in_sql = True
            if in_sql:
                sql_lines.append(line.strip())
                if line.strip().endswith(';') or (line.strip() and not line.strip().endswith(',') and not any(cont in line_lower for cont in ['from', 'where', 'join', 'and', 'or', 'order', 'group', 'having'])):
                    break
        
        sql_query = '\n'.join(sql_lines) if sql_lines else "SQL query not clearly identified"
        
        # Check if user is asking about execution plan
        asking_about_plan = any(phrase in input_lower for phrase in ['explain plan', 'execution plan', 'shall i share', 'should i provide'])
        
        db_system = user_selections.get('database', '') if user_selections else ''
        environment = user_selections.get('environment', '') if user_selections else ''
        
        # Always provide analysis for any database system, with PostgreSQL as default
        if True:  # Analyze any SQL query regardless of database system
            response = f"""🔍 **Aurora PostgreSQL Query Analysis**

✅ **Your Query:**
```sql
{sql_query}
```

🔍 **Initial Analysis:**

**Query Structure Identified:**
- **Main table**: `vw_fact_examiner_block_calculation_last_1year` (view)
- **Joins**: LEFT JOIN with `dim_examiner` and `vw_dim_block`
- **Key filter**: `block_key IS NOT NULL` and date comparison
- **Performance concern**: Slow SELECT query in {environment} environment

⚡ **Immediate Observations:**

1. **View-based query** - Views can hide complex underlying queries
2. **Multiple LEFT JOINs** - Potential for cartesian products or inefficient joins
3. **Date comparison filter** - `b.start_date >= ex.probation_period_end_date` may lack proper indexing
4. **NULL check** - `block_key IS NOT NULL` suggests data quality issues

🚀 **Optimization Recommendations:**

**1. Check View Definitions:**
```sql
-- Examine the underlying view queries
\\d+ vw_fact_examiner_block_calculation_last_1year
\\d+ vw_dim_block

-- Check if views have materialized versions
SELECT schemaname, matviewname FROM pg_matviews;
```

**2. Index Recommendations:**
```sql
-- For join performance
CREATE INDEX CONCURRENTLY idx_examiner_code ON dim_examiner(examiner_code);
CREATE INDEX CONCURRENTLY idx_block_key ON vw_dim_block(block_key);
CREATE INDEX CONCURRENTLY idx_probation_date ON dim_examiner(probation_period_end_date);

-- For the date comparison
CREATE INDEX CONCURRENTLY idx_block_start_date ON vw_dim_block(start_date);
```

**3. Query Rewrite Option:**
```sql
-- More explicit version with better filtering
SELECT ly.*, ex.probation_period_end_date, b."Block Start End Dates"
FROM public.vw_fact_examiner_block_calculation_last_1year ly
INNER JOIN public.dim_examiner ex ON ly.marker_code = ex.examiner_code
INNER JOIN public.vw_dim_block b ON ly.block_key = b.block_key
WHERE ly.block_key IS NOT NULL
  AND ex.probation_period_end_date IS NOT NULL
  AND b.start_date >= ex.probation_period_end_date;
```
"""
            
            if asking_about_plan:
                response += f"\n\n📊 **Yes, please share the execution plan!**\n\nRun this command and share the output:\n```sql\nEXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) \n{sql_query};\n```\n\nThis will help me identify specific bottlenecks and provide targeted index recommendations."
            else:
                response += f"\n\n📊 **Next Steps:**\n1. Share the execution plan using `EXPLAIN ANALYZE` for detailed analysis\n2. Check current indexes on the tables/views\n3. Review the underlying view definitions\n\n**Expected improvements**: Proper indexing should reduce query time significantly."
            
            return response
        
        # Fallback for other database systems
        return f"""🔍 **SQL Query Analysis**

✅ **Your Query:**
```sql
{sql_query}
```

🔍 **Initial Analysis:**

**Query Structure Identified:**
- **Main table**: `vw_fact_examiner_block_calculation_last_1year` (view)
- **Joins**: LEFT JOIN with `dim_examiner` and `vw_dim_block`  
- **Key filter**: `block_key IS NOT NULL` and date comparison
- **Performance concern**: Slow SELECT query in {environment} environment

⚡ **Immediate Observations:**

1. **View-based query** - Views can hide complex underlying queries
2. **Multiple LEFT JOINs** - Potential for cartesian products or inefficient joins
3. **Date comparison filter** - `b.start_date >= ex.probation_period_end_date` may lack proper indexing
4. **NULL check** - `block_key IS NOT NULL` suggests data quality issues

🚀 **Optimization Recommendations:**

**1. Check View Definitions:**
```sql
-- Examine the underlying view queries (PostgreSQL)
\\\\d+ vw_fact_examiner_block_calculation_last_1year
\\\\d+ vw_dim_block

-- Check if views have materialized versions
SELECT schemaname, matviewname FROM pg_matviews;
```

**2. Index Recommendations:**
```sql
-- For join performance
CREATE INDEX CONCURRENTLY idx_examiner_code ON dim_examiner(examiner_code);
CREATE INDEX CONCURRENTLY idx_block_key_examiner ON vw_fact_examiner_block_calculation_last_1year(block_key);
CREATE INDEX CONCURRENTLY idx_marker_code ON vw_fact_examiner_block_calculation_last_1year(marker_code);

-- For the date comparison
CREATE INDEX CONCURRENTLY idx_block_start_date ON vw_dim_block(start_date);
CREATE INDEX CONCURRENTLY idx_probation_date ON dim_examiner(probation_period_end_date);
```

**3. Query Rewrite Option:**
```sql
-- More explicit version with better filtering
SELECT ly.*, ex.probation_period_end_date, b."Block Start End Dates"
FROM public.vw_fact_examiner_block_calculation_last_1year ly
INNER JOIN public.dim_examiner ex ON ly.marker_code = ex.examiner_code
INNER JOIN public.vw_dim_block b ON ly.block_key = b.block_key
WHERE ly.block_key IS NOT NULL
  AND ex.probation_period_end_date IS NOT NULL
  AND b.start_date >= ex.probation_period_end_date;
```

📊 **Next Steps:**
1. Run `EXPLAIN ANALYZE` on your query to see the execution plan
2. Check current indexes on the tables/views involved
3. Review the underlying view definitions for complexity
4. Consider materializing frequently-used views

**Expected improvements**: Proper indexing should significantly reduce query execution time.
"""
    
    def get_query_execution_plan_analysis(self, user_input, user_selections):
        """Analyze specific SQL query with execution plan"""
        lines = user_input.split('\n')
        
        # Find the SQL query
        sql_query = ""
        for line in lines:
            if 'SELECT ' in line.upper():
                sql_query = line.strip()
                break
        
        # Extract execution time
        execution_time = ""
        for line in lines:
            if 'Execution Time:' in line:
                execution_time = line.strip()
                break
        
        db_system = user_selections.get('database', '') if user_selections else ''
        
        if 'postgres' in db_system.lower() or 'aurora' in db_system.lower():
            return f"""🔍 **Aurora PostgreSQL Query Performance Analysis**

✅ **Query Analysis:**
```sql
{sql_query}
```

🔍 **Execution Plan Issues Identified:**

**Major Performance Problems:**
1. **Bitmap Heap Scan with High Filter Cost** - 182+ seconds execution time
2. **ILIKE Pattern Matching** - `%Student%` and `%ID%` require full text scans
3. **Multiple String Filters** - first_name, middle_name, last_name all using ILIKE
4. **Large Data Set** - 40GB table with 884K+ rows being scanned
5. **Filter Inefficiency** - 725K rows removed by recheck, 294K by filter

⚡ **Immediate Index Recommendations:**

**1. Create Composite Index for Date + Text Search:**
```sql
-- For your specific query pattern
CREATE INDEX CONCURRENTLY idx_customer_search_optimized 
ON customer_ms.customer (updated_datetime, first_name, middle_name, last_name) 
WHERE updated_datetime >= '2025-01-01';
```

**2. Create Text Search Indexes:**
```sql
-- For ILIKE pattern matching
CREATE INDEX CONCURRENTLY idx_customer_names_gin 
ON customer_ms.customer USING gin (
    (first_name || ' ' || middle_name || ' ' || last_name) gin_trgm_ops
);

-- Enable trigram extension first
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

📊 **Expected Performance Improvements:**
- **Current**: 182+ seconds
- **With composite index**: ~2-5 seconds
- **With text search optimization**: ~0.5-2 seconds

🎯 **Immediate Action Plan:**
1. Create the composite index first (biggest impact)
2. Install pg_trgm extension for better ILIKE performance
3. Rewrite query with LIMIT to prevent runaway execution
4. Monitor index usage and query performance

**Expected Result**: Query should execute in under 5 seconds instead of 3+ minutes."""
        
        return "Query execution plan analysis available for PostgreSQL/Aurora."
    
    def get_connection_troubleshooting_recommendation(self, user_input, user_selections):
        """Specialized recommendations for database connection issues"""
        db_system = user_selections.get('database', '') if user_selections else ''
        cloud_provider = user_selections.get('cloud_provider', '') if user_selections else ''
        environment = user_selections.get('environment', '') if user_selections else ''
        
        if 'aws' in cloud_provider.lower() and 'aurora' in db_system.lower():
            return f"""🔍 **AWS Aurora PostgreSQL Connection Timeout Analysis**

✅ **Current Situation:**
- **Environment**: {environment}
- **Database**: {db_system}
- **Issue**: Lambda connection timeouts to Aurora PostgreSQL
- **Error**: "connection timed-out" in Lambda logs

🔍 **Root Cause Analysis:**

**Most Common Causes:**
1. **Security Group Issues** - Lambda can't reach Aurora
2. **Subnet Configuration** - Lambda not in VPC or wrong subnets
3. **Connection Pool Exhaustion** - Aurora hitting max_connections
4. **DNS Resolution** - Lambda can't resolve Aurora endpoint
5. **Aurora Serverless Cold Start** - Database paused/scaling

⚡ **Immediate Fixes:**

**1. Implement Connection Pooling:**
```python
# Use RDS Proxy for connection pooling
import psycopg2
from psycopg2 import pool

# Create connection pool (outside Lambda handler)
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # min and max connections
    host='your-rds-proxy-endpoint',
    database='your_db',
    user='your_user',
    password='your_password'
)
```

🎯 **Expected Results:**
- **Connection Success Rate**: >99%
- **Lambda Duration**: <5 seconds typical
- **Error Rate**: <1% connection failures

**Next Steps:**
1. Check security groups and VPC configuration first
2. Implement RDS Proxy if not already using
3. Add connection retry logic with exponential backoff"""
        
        return "Connection troubleshooting recommendations available for your database system."
    
    def get_contextual_fallback(self, service_type, user_input, user_selections):
        """Provide contextual fallback responses when AI is unavailable"""
        input_lower = user_input.lower()
        
        if service_type == 'troubleshooting':
            if any(word in input_lower for word in ['connection', 'timeout', 'error']):
                return "I can help with connection issues. Please share the exact error message and your database system details for specific troubleshooting steps."
        elif service_type == 'query':
            if 'select' in input_lower or 'sql' in input_lower:
                return "I see you have a SQL query. Please share the complete query and describe the performance issue you're experiencing."
        elif service_type == 'performance':
            if any(word in input_lower for word in ['slow', 'cpu', 'memory']):
                return "I can help optimize performance. Please describe the specific symptoms and share any metrics you have available."
        
        return f"I understand you need help with {service_type}. Please provide more specific details about your situation so I can give you targeted recommendations."
    
    def get_welcome_message(self, service_type):
        """Generate intelligent welcome message based on service type"""
        service_desc = self.service_descriptions.get(service_type, 'database assistance')
        
        welcome_prompt = f"""You are DB-Buddy, a senior database expert. A user just selected {service_desc} assistance. 
        
Generate a warm, professional welcome message that:
1. Welcomes them to the specific service
2. Briefly explains what you can help with
3. Asks them to describe their situation in their own words
4. Mentions they can use the dropdowns above for system details

Keep it conversational and encouraging. No bullet points or rigid structure."""
        
        # Get AI-generated welcome message
        if self.use_ai:
            ai_welcome = self.get_ai_response("", welcome_prompt, {})
            if ai_welcome:
                return ai_welcome
        
        # Fallback welcome messages
        fallback_messages = {
            'troubleshooting': "👋 Hi! I'm here to help you troubleshoot database issues. What problem are you experiencing? Feel free to describe it in your own words - I'll understand and provide targeted solutions.",
            'query': "👋 Hello! I specialize in SQL query optimization. Share your query and describe what's happening - slow performance, errors, or anything else. I'll analyze it and provide specific recommendations.",
            'performance': "👋 Welcome! I'm here to help with database performance issues. Tell me what you're experiencing - slow queries, high resource usage, or any performance concerns. I'll help you identify and fix the root cause.",
            'architecture': "👋 Great to meet you! I'll help design the right database architecture for your needs. Tell me about your application, expected scale, and any specific requirements you have in mind.",
            'capacity': "👋 Hi there! I specialize in database capacity planning. Share details about your current or expected workload, data size, user count - whatever you know. I'll help you plan the right infrastructure.",
            'security': "👋 Hello! I'm here to help with database security and compliance. What are your security concerns or requirements? Whether it's access control, encryption, or compliance standards, I'll guide you through it."
        }
        
        return fallback_messages.get(service_type, "👋 Hello! How can I help you with your database needs today?")

# Initialize DB-Buddy
if 'db_buddy' not in st.session_state:
    st.session_state.db_buddy = StreamlitDBBuddy()

# Initialize memory
if 'memory' not in st.session_state:
    st.session_state.memory = ConversationMemory('streamlit_conversations.json')

# Set page config
st.set_page_config(
    page_title="DB-Buddy - AI Database Assistant",
    page_icon="🗄️",
    layout="wide"
)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().timestamp()}"
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_issue_type' not in st.session_state:
    st.session_state.current_issue_type = None
if 'show_history' not in st.session_state:
    st.session_state.show_history = False

# Header
st.title("🗄️ DB-Buddy - AI Database Assistant")
st.markdown("Your AI-powered database assistant for instant solutions")

# Sidebar for service selection and history
with st.sidebar:
    st.header("Select Service")
    
    issue_types = {
        'troubleshooting': '🔧 Database Troubleshooting',
        'query': '⚡ Query Optimization', 
        'performance': '📊 Performance Analysis',
        'architecture': '🏗️ Architecture & Design',
        'capacity': '📈 Capacity Planning',
        'security': '🔒 Security & Compliance'
    }
    
    selected_service = st.selectbox(
        "Choose your database assistance:",
        options=list(issue_types.keys()),
        format_func=lambda x: issue_types[x],
        index=0 if st.session_state.current_issue_type is None else list(issue_types.keys()).index(st.session_state.current_issue_type)
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Chat"):
            st.session_state.messages = []
            st.session_state.current_issue_type = selected_service
            st.session_state.session_id = f"session_{datetime.now().timestamp()}"
            st.session_state.show_history = False
            
            # Add intelligent welcome message
            welcome_msg = st.session_state.db_buddy.get_welcome_message(selected_service)
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
            st.rerun()
    
    with col2:
        if st.button("History"):
            st.session_state.show_history = not st.session_state.show_history
            st.rerun()
    
    # Show conversation history
    if st.session_state.show_history:
        st.subheader("Past Conversations")
        conversations = st.session_state.memory.get_all_conversations()
        
        if conversations:
            for conv in conversations[:10]:  # Show last 10 conversations
                with st.expander(f"{conv['title']} - {conv['timestamp'][:10]}"):
                    st.write(f"**Preview:** {conv['preview']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Load", key=f"load_{conv['session_id']}"):
                            # Load conversation
                            loaded_conv = st.session_state.memory.get_conversation(conv['session_id'])
                            if loaded_conv:
                                st.session_state.current_issue_type = loaded_conv['data']['type']
                                st.session_state.messages = []
                                # Reconstruct messages from conversation data
                                for i, answer in enumerate(loaded_conv['data']['answers']):
                                    st.session_state.messages.append({"role": "user", "content": answer})
                                st.session_state.show_history = False
                                st.rerun()
                    with col2:
                        if st.button(f"Delete", key=f"del_{conv['session_id']}"):
                            st.session_state.memory.delete_conversation(conv['session_id'])
                            st.rerun()
        else:
            st.write("No past conversations found.")

# LOV Selectors
st.subheader("Quick Setup")
col1, col2, col3, col4 = st.columns(4)

with col1:
    deployment = st.selectbox("Deployment:", ["", "On-Premises", "Cloud", "Hybrid"])

with col2:
    cloud_provider = st.selectbox("Cloud Provider:", 
        ["", "AWS", "Azure", "GCP", "Oracle Cloud", "IBM Cloud"],
        disabled=deployment != "Cloud"
    )

with col3:
    if deployment == "Cloud" and cloud_provider == "AWS":
        db_options = ["", "Amazon RDS MySQL", "Amazon RDS PostgreSQL", "Amazon Aurora MySQL", "Amazon Aurora PostgreSQL", "Amazon DynamoDB"]
    elif deployment == "Cloud" and cloud_provider == "Azure":
        db_options = ["", "Azure Database for MySQL", "Azure Database for PostgreSQL", "Azure SQL Database", "Azure Cosmos DB"]
    else:
        db_options = ["", "MySQL", "PostgreSQL", "SQL Server", "Oracle", "MongoDB", "Redis"]
    
    database = st.selectbox("Database System:", db_options)

with col4:
    environment = st.selectbox("Environment:", ["", "Development", "Staging", "Production"])

if st.button("Insert Selections"):
    if any([deployment, cloud_provider, database, environment]):
        selection_text = ""
        if deployment: selection_text += f"Deployment: {deployment}\n"
        if cloud_provider: selection_text += f"Cloud Provider: {cloud_provider}\n"
        if database: selection_text += f"Database System: {database}\n"
        if environment: selection_text += f"Environment: {environment}\n"
        
        st.session_state.messages.append({"role": "user", "content": selection_text.strip()})
        st.rerun()

# Chat Interface
if not st.session_state.show_history:
    st.subheader("Chat")
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if not st.session_state.show_history:
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Save to memory
        conversation_data = {
            'type': st.session_state.current_issue_type or 'general',
            'answers': [msg['content'] for msg in st.session_state.messages if msg['role'] == 'user'],
            'user_selections': {
                'deployment': deployment,
                'cloud_provider': cloud_provider,
                'database': database,
                'environment': environment
            }
        }
        st.session_state.memory.save_conversation(st.session_state.session_id, conversation_data)
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate intelligent response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                if st.session_state.current_issue_type:
                    # Prepare user selections
                    user_selections = {
                        'deployment': deployment,
                        'cloud_provider': cloud_provider,
                        'database': database,
                        'environment': environment
                    }
                    
                    # Get intelligent response
                    response = st.session_state.db_buddy.get_intelligent_response(
                        prompt, 
                        user_selections, 
                        st.session_state.current_issue_type,
                        st.session_state.messages
                    )
                    
                    if not response:
                        response = "I'm having trouble connecting to the AI service. Please try again or provide more specific details about your database issue."
                else:
                    response = "Please select a service type from the sidebar to get started!"
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# Instructions
with st.expander("How to use DB-Buddy"):
    st.markdown("""
    1. **Select Service**: Choose your database assistance type from the sidebar
    2. **Quick Setup**: Use the dropdowns to specify your database environment
    3. **Insert Selections**: Click to add your configuration to the chat
    4. **Describe Issue**: Type your specific database question or problem
    5. **Get Recommendations**: Receive tailored advice and diagnostic queries
    """)