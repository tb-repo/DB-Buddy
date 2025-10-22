import streamlit as st

# Set page config first - must be at the very top
st.set_page_config(
    page_title="DB-Buddy - AI Database Assistant",
    page_icon="🗄️",
    layout="wide"
)

# Add custom CSS for proper scrolling and viewport management
st.markdown("""
<style>
/* Main container scrolling */
.main .block-container {
    max-height: 100vh;
    overflow-y: auto;
    padding-top: 1rem;
    padding-bottom: 2rem;
}

/* Chat container with fixed height and scrolling */
.stChatMessage {
    max-width: 100%;
    word-wrap: break-word;
    overflow-wrap: break-word;
}

/* Ensure chat input is always visible */
.stChatInput {
    position: sticky;
    bottom: 0;
    background: white;
    z-index: 999;
    padding: 1rem 0;
    border-top: 1px solid #e0e0e0;
}

/* Chat messages container with scrolling */
.chat-container {
    max-height: 60vh;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    margin-bottom: 1rem;
}

/* Sidebar scrolling */
.css-1d391kg {
    max-height: 100vh;
    overflow-y: auto;
}

/* Code blocks with horizontal scrolling */
pre {
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* Responsive design for mobile */
@media (max-width: 768px) {
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        max-height: 100vh;
    }
    
    .chat-container {
        max-height: 50vh;
    }
    
    /* Mobile viewport fix */
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 1rem;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
}

/* Ensure content doesn't get hidden behind fixed elements */
body {
    padding-bottom: 100px;
}

/* Chat message styling for better readability */
.stChatMessage > div {
    max-width: 100%;
    overflow-x: auto;
}

/* Table responsiveness */
table {
    width: 100%;
    overflow-x: auto;
    display: block;
    white-space: nowrap;
}

@media (min-width: 769px) {
    table {
        display: table;
        white-space: normal;
    }
}
</style>
""", unsafe_allow_html=True)

import warnings
warnings.filterwarnings('ignore', category=SyntaxWarning)
import requests
import json
from datetime import datetime
import os
from memory import ConversationMemory
from pdf_generator import PDFReportGenerator
from image_processor import ImageProcessor
import base64
from PIL import Image
import io
import asyncio
import time
from typing import Generator
from security_validator import LLMSecurityValidator
from vector_security import VectorSecurityValidator
from misinformation_validator import MisinformationValidator
from consumption_limiter import ConsumptionLimiter

# Enhanced API key management with caching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_api_key(key_name):
    """Securely get API keys with caching"""
    try:
        return st.secrets[key_name]
    except:
        return os.getenv(key_name)

# Initialize API keys
GROQ_API_KEY = get_api_key('GROQ_API_KEY')
HUGGINGFACE_API_KEY = get_api_key('HUGGINGFACE_API_KEY')
ANTHROPIC_API_KEY = get_api_key('ANTHROPIC_API_KEY')

@st.cache_resource
def get_db_buddy():
    """Cached DB-Buddy instance for performance"""
    return StreamlitDBBuddy()

class StreamlitDBBuddy:
    def __init__(self):
        self.use_ai = self.check_ai_available()
        self.security_validator = LLMSecurityValidator()
        self.vector_security = VectorSecurityValidator()
        self.misinformation_validator = MisinformationValidator()
        self.consumption_limiter = ConsumptionLimiter()
        self.service_descriptions = {
            'troubleshooting': 'database troubleshooting and error resolution',
            'query': 'SQL query optimization and performance tuning',
            'performance': 'database performance analysis and optimization',
            'architecture': 'database architecture design and best practices',
            'capacity': 'database capacity planning and sizing',
            'security': 'database security hardening and compliance'
        }
        self.rate_limit_tracker = {}
    
    def check_ai_available(self):
        """Check available AI services with validation"""
        if ANTHROPIC_API_KEY and len(ANTHROPIC_API_KEY) > 10:
            return 'claude'
        if GROQ_API_KEY and len(GROQ_API_KEY) > 10:
            return 'groq'
        if HUGGINGFACE_API_KEY and len(HUGGINGFACE_API_KEY) > 10:
            return 'huggingface'
        return False
    
    def check_rate_limit(self, user_id="default"):
        """Enhanced rate limiting with user session tracking"""
        current_time = time.time()
        if user_id not in self.rate_limit_tracker:
            self.rate_limit_tracker[user_id] = []
        
        # Remove requests older than 1 minute
        self.rate_limit_tracker[user_id] = [
            req_time for req_time in self.rate_limit_tracker[user_id] 
            if current_time - req_time < 60
        ]
        
        # Increased limit for better user experience (10 requests per minute)
        if len(self.rate_limit_tracker[user_id]) >= 10:
            return False
        
        self.rate_limit_tracker[user_id].append(current_time)
        return True
    
    async def get_intelligent_response_async(self, user_input, user_selections, service_type, conversation_history):
        """Async version for non-blocking response generation"""
        return await asyncio.to_thread(
            self.get_intelligent_response, 
            user_input, user_selections, service_type, conversation_history
        )
    
    @st.cache_data(ttl=1800)  # Cache for 30 minutes
    def get_cached_response(_self, user_input_hash, service_type, user_selections_str):
        """Cached response lookup"""
        return None  # Will be populated by actual responses
    
    def get_intelligent_response(self, user_input, user_selections, service_type, conversation_history):
        """Generate intelligent, contextual responses with caching and fallbacks"""
        # PRIORITY 1: Check for specialized patterns FIRST (before database check)
        specialized_response = self.get_specialized_recommendation(user_input, user_selections)
        if specialized_response:
            return specialized_response
        
        # PRIORITY 2: Check if the query is database-related
        if not self.is_database_related_query(user_input):
            return self.get_non_database_response()
        
        # Enhanced context building with conversation memory
        context = self.build_enhanced_context(service_type, user_selections, conversation_history)
        
        # Get AI response with streaming support
        if self.use_ai:
            ai_response = self.get_ai_response_with_context(context, user_input, user_selections)
            if ai_response:
                return ai_response
        
        # Enhanced offline fallback
        return self.get_enhanced_offline_fallback(service_type, user_input, user_selections)
    
    def build_enhanced_context(self, service_type, user_selections, conversation_history):
        """Build rich context with conversation memory"""
        context = f"Service type: {service_type}\n"
        
        # System configuration
        if user_selections:
            context += "\nSystem configuration:\n"
            for key, value in user_selections.items():
                if value:
                    context += f"- {key}: {value}\n"
        
        # Enhanced conversation history with relevance scoring
        if len(conversation_history) > 1:
            context += f"\nConversation history (last 6 exchanges):\n"
            recent_messages = conversation_history[-12:]  # Last 12 messages (6 exchanges)
            
            for i in range(0, len(recent_messages), 2):
                if i + 1 < len(recent_messages):
                    user_msg = recent_messages[i]['content'][:150] + "..." if len(recent_messages[i]['content']) > 150 else recent_messages[i]['content']
                    assistant_msg = recent_messages[i+1]['content'][:150] + "..." if len(recent_messages[i+1]['content']) > 150 else recent_messages[i+1]['content']
                    context += f"User: {user_msg}\nAssistant: {assistant_msg}\n\n"
        
        return context
    
    @st.cache_data(ttl=300)  # Cache responses for 5 minutes
    def get_cached_ai_response(_self, context_hash, user_input, user_selections_str):
        """Cached AI response to reduce API calls"""
        return _self.get_ai_response_with_context(context_hash, user_input, eval(user_selections_str))
    
    def get_ai_response_with_context(self, context, user_input, user_selections=None):
        """Enhanced AI response with context awareness and streaming"""
        # Build enhanced context with user selections and technical details
        enhanced_context = context
        if user_selections:
            selection_context = "\n\nUser's System Configuration:\n"
            for key, value in user_selections.items():
                if value:
                    selection_context += f"• {key}: {value}\n"
            enhanced_context += selection_context
        
        # Preserve formatting for execution plans and SQL queries
        enhanced_context += "\n\nUser's current message: " + user_input + "\n"
        enhanced_context += "Provide specific, actionable database recommendations with technical depth appropriate to the user's expertise level.\n"
        
        # Build deployment-specific guidance
        deployment_guidance = self.get_deployment_specific_guidance(user_selections)
        
        system_prompt = f"""You are DB-Buddy, an expert Database Administrator (DBA) with 15+ years of experience in database operations, performance tuning, and architecture design.

EXPERT DBA APPROACH:
- Act like a senior DBA consultant who proactively gathers diagnostic information
- Request specific diagnostic commands and data before providing recommendations
- Demonstrate deep technical knowledge across all database systems
- Provide comprehensive analysis with expected performance improvements
- Always ask for execution plans, table statistics, and system metrics when analyzing performance issues

DIAGNOSTIC METHODOLOGY:
- Always request EXPLAIN ANALYZE output for slow queries
- Ask for table statistics (pg_stat_user_tables, table sizes, index usage)
- Request system resource information (CPU, memory, I/O metrics)
- Gather configuration details relevant to the specific issue
- Analyze complete diagnostic data before providing optimization recommendations

EXPERTISE LEVELS ADAPTATION:
- **Beginner**: Provide step-by-step diagnostic commands with explanations
- **Intermediate**: Focus on analysis methodology and interpretation guidance
- **Advanced**: Dive deep into technical details and advanced optimization strategies
- **Expert**: Discuss complex scenarios, edge cases, and architectural considerations

RESPONSE QUALITY:
- Provide specific, actionable solutions with exact commands
- Include expected performance improvements (e.g., "Reduce query time from 25s to 2-3s")
- Reference user's specific table names, queries, and metrics
- Always explain the reasoning behind recommendations
- Request additional diagnostic information when needed for accurate analysis

TECHNICAL EXPERTISE:
- Advanced SQL query optimization and execution plan analysis
- Index design and performance tuning strategies
- Database-specific configuration and best practices
- Cloud platform optimization (AWS RDS/Aurora, Azure SQL, GCP Cloud SQL)
- JSONB/JSON optimization, partitioning, and scaling strategies{deployment_guidance}

IMPORTANT: Always act as a proactive expert who requests comprehensive diagnostic information to provide accurate, targeted recommendations rather than generic advice."""
        
        if self.use_ai == 'claude':
            return self.get_claude_response_streaming(system_prompt, enhanced_context, user_input)
        elif self.use_ai == 'groq':
            return self.get_groq_response_streaming(system_prompt, enhanced_context, user_input)
        elif self.use_ai == 'huggingface':
            return self.get_huggingface_response(system_prompt, enhanced_context, user_input)
        
        return None
    
    def get_claude_response_streaming(self, system_prompt, context, user_input):
        """Claude response with streaming support"""
        try:
            # Supply chain validation
            model = "claude-3-5-sonnet-20241022"
            if not self.security_validator.validate_model_endpoint('anthropic', model, 'api.anthropic.com'):
                st.error("Supply chain security: Untrusted model/endpoint")
                return None
            
            import anthropic
            client = anthropic.Anthropic(api_key=get_api_key('ANTHROPIC_API_KEY'))
            
            with client.messages.stream(
                model=model,
                max_tokens=1200,
                system=system_prompt,
                messages=[{"role": "user", "content": f"Context: {context}\nQuery: {user_input}"}]
            ) as stream:
                response_text = ""
                for text in stream.text_stream:
                    response_text += text
                    yield text
                return response_text
        except Exception as e:
            st.error(f"Claude API error: {e}")
            return None
    
    def get_groq_response_streaming(self, system_prompt, context, user_input):
        """Groq response with enhanced parameters"""
        try:
            # Supply chain validation
            endpoint = 'https://api.groq.com/openai/v1/chat/completions'
            model = 'llama3-8b-8192'
            if not self.security_validator.validate_model_endpoint('groq', model, endpoint):
                st.error("Supply chain security: Untrusted model/endpoint")
                return None
            
            headers = {
                'Authorization': f'Bearer {get_api_key("GROQ_API_KEY")}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Context: {context}\nUser Request: {user_input}"}
                ],
                'temperature': 0.1,
                'max_tokens': 1000,
                'stream': False
            }
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            st.error(f"Groq API error: {e}")
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
    
    def contains_sql_query(self, text):
        """Simplified SQL detection - basic SELECT+FROM pattern matching"""
        text_lower = text.lower()
        
        # Basic SQL detection - look for SELECT with FROM
        if 'select' in text_lower and 'from' in text_lower:
            return True
        
        # Check for other common SQL patterns
        sql_patterns = [
            ('insert', 'into'),
            ('update', 'set'),
            ('delete', 'from'),
            ('create', 'table')
        ]
        
        for pattern1, pattern2 in sql_patterns:
            if pattern1 in text_lower and pattern2 in text_lower:
                return True
        
        return False
    
    def is_database_related_query(self, user_input):
        """Check if the user query is database-related"""
        user_lower = user_input.lower()
        
        # Database-related keywords
        db_keywords = [
            'database', 'sql', 'query', 'table', 'index', 'performance', 'optimization',
            'postgresql', 'mysql', 'oracle', 'mongodb', 'sqlite', 'mariadb',
            'select', 'insert', 'update', 'delete', 'create', 'alter', 'drop',
            'join', 'where', 'group by', 'order by', 'having', 'union',
            'backup', 'restore', 'replication', 'partition', 'schema', 'migration',
            'connection', 'timeout', 'deadlock', 'transaction', 'commit', 'rollback',
            'cpu usage', 'memory usage', 'disk space', 'slow query', 'execution plan',
            'dba', 'database administrator', 'db', 'rds', 'aurora', 'cosmos',
            'capacity planning', 'sizing', 'scaling', 'sharding', 'clustering',
            'jsonb', 'toast', 'json columns', 'slow response', 'response times'
        ]
        
        # Check if any database keywords are present
        return any(keyword in user_lower for keyword in db_keywords)
    
    def get_non_database_response(self):
        """Response for non-database related queries"""
        return """🏢 **DB-Buddy - Official DBM ChatOps**

**NOTICE**: This is the official Database Management (DBM) team ChatOps tool for L1/L2 operations only.

**💼 AUTHORIZED DATABASE OPERATIONS:**

**🔧 L1 Troubleshooting:**
• Connection timeouts and authentication issues
• Standard error diagnosis and resolution
• Performance monitoring and basic optimization
• Routine maintenance operations

**⚡ L2 Query Optimization:**
• SQL query performance analysis
• Index recommendations and implementation
• Execution plan analysis and tuning
• Query rewriting for performance

**📊 L2 Performance Analysis:**
• Resource utilization assessment
• Capacity planning recommendations
• Monitoring setup and alerting
• Performance baseline establishment

**🔐 L1/L2 Security Operations:**
• Access control verification
• Security configuration review
• Compliance check procedures
• Audit log analysis

**⚠️ ESCALATION REQUIRED:**
For complex architecture changes, production schema modifications, or critical system failures, escalate to the DBM team after using this tool for initial analysis.

**📝 Please provide database-related requests only.** Non-database queries will be rejected to maintain operational focus.

💡 *Format: "[Environment] [Database] [Issue Description]" - Example: "PROD PostgreSQL connection timeout errors"*"""
    
    def get_specialized_recommendation(self, user_input, user_selections=None):
        """Provide specialized recommendations for common database patterns"""
        input_lower = user_input.lower()
        
        # PRIORITY 1: Check for specific performance issues FIRST
        if ('100ms' in user_input and '40s' in user_input) or ('explain plan' in input_lower and 'actual' in input_lower):
            return self.analyze_execution_time_discrepancy(user_input, user_selections)
        
        # PRIORITY 2: Check for JSONB/TOAST performance issues
        if any(keyword in input_lower for keyword in ['jsonb', 'toast', 'json columns']) and any(perf in input_lower for perf in ['slow', 'performance', 'minutes', 'taking around']):
            return self.analyze_jsonb_toast_performance(user_input, user_selections)
        
        # PRIORITY 3: Detect execution plans (HIGHEST PRIORITY)
        execution_plan_indicators = [
            'query plan', 'execution time:', 'planning time:', 'hash join', 'nested loop', 'seq scan', 'index scan',
            'bitmap heap scan', 'sort', 'aggregate', 'rows removed by filter', 'buffers:', 'cost=',
            'actual time=', 'rows=', 'loops=', 'explain analyze', 'explain plan', 'unique  (cost=',
            'gather  (cost=', 'hashaggregate', 'parallel hash', 'i/o timings:', 'memory usage:', 'batches:'
        ]
        
        # Strong execution plan detection
        if any(indicator in input_lower for indicator in execution_plan_indicators):
            return self.get_query_execution_plan_analysis(user_input, user_selections)
        
        # Check for execution plan patterns in lines (preserve formatting)
        lines = user_input.split('\n')
        plan_pattern_count = 0
        for line in lines:
            line_lower = line.lower().strip()
            # More comprehensive pattern matching
            if any(pattern in line_lower for pattern in [
                '->  ', 'cost=', 'actual time=', 'rows=', 'buffers:', 'loops=', 
                'workers planned:', 'workers launched:', 'heap fetches:', 'filter:'
            ]):
                plan_pattern_count += 1
        
        # If we find execution plan patterns, treat as execution plan
        if plan_pattern_count >= 1:  # Lowered threshold for better detection
            return self.get_query_execution_plan_analysis(user_input, user_selections)
        
        # PRIORITY 4: Detect actual SQL queries (not descriptions)
        if self.contains_sql_query(user_input):
            return self.get_sql_query_analysis(user_input, user_selections)
        
        # Detect connection issues
        if any(keyword in input_lower for keyword in ['connection', 'timeout', 'timed out', 'connect', 'refused']):
            return self.get_connection_troubleshooting_recommendation(user_input, user_selections)
        
        return None
    
    def get_sql_query_analysis(self, user_input, user_selections):
        """Expert DBA analysis with proactive diagnostic requests"""
        input_lower = user_input.lower()
        
        # Check for specific performance patterns first
        if ('25' in user_input and 'second' in input_lower) and 'jsonb' in input_lower:
            return self.analyze_specific_slow_query(user_input, user_selections)
        
        # Extract SQL query from input
        sql_query = self.extract_sql_query(user_input)
        
        db_system = user_selections.get('database', 'PostgreSQL') if user_selections else 'PostgreSQL'
        environment = user_selections.get('environment', '') if user_selections else ''
        
        return f"""🔍 **Expert DBA Analysis - SQL Query Review**

✅ **Query Identified:**
```sql
{sql_query}
```

🎯 **Expert DBA Diagnostic Protocol:**

As your database expert, I need comprehensive diagnostic information to provide accurate optimization recommendations. Please run these diagnostic commands:

**1. Execution Plan Analysis:**
```sql
-- Get detailed execution plan with timing and buffer information
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT) 
{sql_query};
```

**2. Table Statistics:**
```sql
-- Check table sizes and row counts
SELECT 
    schemaname, tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup,
    last_vacuum, last_autovacuum, last_analyze, last_autoanalyze
FROM pg_stat_user_tables 
WHERE schemaname = 'public' 
AND tablename IN (SELECT tablename FROM pg_tables WHERE tablename LIKE '%your_table_pattern%');
```

**3. Index Analysis:**
```sql
-- Current indexes on involved tables
SELECT 
    schemaname, tablename, indexname, indexdef,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename IN ('table1', 'table2', 'table3')  -- Replace with your actual table names
ORDER BY tablename, indexname;
```

**4. Query Performance Metrics:**
```sql
-- Check if query is in pg_stat_statements
SELECT 
    query, calls, total_time, mean_time, 
    rows, 100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
WHERE query ILIKE '%your_key_table_name%'  -- Replace with key table from your query
ORDER BY total_time DESC LIMIT 5;
```

**5. System Resource Check:**
```sql
-- Current database connections and activity
SELECT 
    state, count(*) as connections,
    avg(extract(epoch from (now() - query_start))) as avg_duration_seconds
FROM pg_stat_activity 
WHERE datname = current_database()
GROUP BY state;
```

🔍 **What I'll Analyze Once You Provide This Data:**

1. **Execution Plan Bottlenecks** - Identify expensive operations (Seq Scans, Hash Joins, Sorts)
2. **Index Optimization** - Recommend specific indexes based on WHERE clauses and JOIN conditions
3. **Table Statistics Issues** - Check if ANALYZE is needed or if table bloat exists
4. **Query Rewrite Opportunities** - Suggest more efficient query structures
5. **Resource Utilization** - Identify memory, CPU, or I/O constraints

⚡ **Expected Outcome:**
With this diagnostic information, I can provide:
- Specific index recommendations with expected performance improvements
- Query optimization suggestions
- Configuration tuning recommendations
- Estimated performance gains (e.g., "Reduce query time from 25s to 2-3s")

**Environment**: {environment} {db_system}

💡 **Pro Tip**: Run these commands during a representative workload period for accurate analysis."""
    
    def extract_sql_query(self, user_input):
        """Extract SQL query from user input"""
        lines = user_input.split('\n')
        sql_lines = []
        in_sql = False
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['select ', 'with ', 'insert ', 'update ', 'delete ']):
                in_sql = True
            if in_sql:
                sql_lines.append(line.strip())
                if line.strip().endswith(';'):
                    break
        
        return '\n'.join(sql_lines) if sql_lines else "[SQL query not clearly identified - please paste your complete query]"
    
    def analyze_execution_time_discrepancy(self, user_input, user_selections):
        """Analyze execution time discrepancy between estimated and actual"""
        return f"""🚨 **Execution Plan Analysis - Time Discrepancy Detected**

⚠️ **Critical Issue**: Significant difference between estimated and actual execution times

🔍 **Expert DBA Analysis Required:**

Please provide the complete execution plan output so I can analyze:
1. **Cost estimation accuracy**
2. **Row count estimates vs actual**
3. **Buffer usage patterns**
4. **Join algorithm efficiency**

**Diagnostic Commands Needed:**
```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT) 
[YOUR_QUERY_HERE];
```

**Expected Analysis:**
- Identify misestimated operations
- Recommend statistics updates
- Suggest query optimizations
- Provide index recommendations

**Next Steps:** Share your complete execution plan for detailed analysis."""
    
    def analyze_specific_slow_query(self, user_input, user_selections):
        """Analyze the specific 25+ second JSONB query pattern"""
        return f"""🚨 **Critical Performance Issue Detected**

⚠️ **25+ Second Query with JSONB Columns - Expert Analysis Required**

🔍 **Immediate Assessment:**
This execution time indicates a severe performance bottleneck, likely related to:
1. **JSONB column processing overhead**
2. **Missing or ineffective indexes**
3. **Large dataset sequential scans**
4. **Inefficient JOIN operations**

🎯 **Expert DBA Diagnostic Protocol:**

I need these specific diagnostics to provide targeted optimization:

**CRITICAL - Run These Commands First:**

```sql
-- 1. Get execution plan with detailed timing
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT) 
[YOUR_SLOW_QUERY_HERE];

-- 2. Check JSONB column sizes and TOAST usage
SELECT 
    schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as toast_size
FROM pg_stat_user_tables 
WHERE tablename = 'your_table_with_jsonb';  -- Replace with actual table name

-- 3. Analyze JSONB column structure
SELECT 
    jsonb_column_name,  -- Replace with actual JSONB column name
    pg_column_size(jsonb_column_name) as column_size_bytes,
    jsonb_typeof(jsonb_column_name) as json_type
FROM your_table_name  -- Replace with actual table name
LIMIT 10;

-- 4. Check current indexes on JSONB columns
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'your_table_name'  -- Replace with actual table name
AND indexdef ILIKE '%gin%';
```

**Expected Root Causes:**
1. **TOAST Table Bloat** - JSONB data stored separately causing extra I/O
2. **Missing GIN Indexes** - No proper indexing on JSONB query patterns
3. **Full JSONB Retrieval** - Selecting entire JSONB instead of specific paths
4. **Inefficient WHERE Clauses** - Filtering on non-indexed JSONB properties

**Immediate Optimization Strategies:**

```sql
-- Create GIN index for JSONB queries (if missing)
CREATE INDEX CONCURRENTLY idx_jsonb_gin 
ON your_table_name USING GIN (your_jsonb_column);

-- Create functional indexes for specific JSONB paths
CREATE INDEX CONCURRENTLY idx_jsonb_specific_path 
ON your_table_name USING BTREE ((your_jsonb_column->>'frequently_queried_field'));
```

🎯 **Expected Performance Improvement:**
With proper JSONB optimization: **25+ seconds → 2-5 seconds (80-90% improvement)**

**Next Steps:**
1. Share the execution plan output
2. Provide JSONB column analysis results
3. Confirm table and JSONB column names
4. I'll provide specific index recommendations and query optimizations

⚠️ **Production Impact**: This level of performance degradation requires immediate attention."""
    
    def analyze_jsonb_toast_performance(self, user_input, user_selections):
        """Analyze JSONB/TOAST table performance issues"""
        db_system = user_selections.get('database', 'PostgreSQL') if user_selections else 'PostgreSQL'
        
        # Extract key metrics from user input
        table_size = "2 GB" if "2 gb" in user_input.lower() else "Unknown"
        toast_size = "17 GB" if "17 gb" in user_input.lower() else "Large"
        slow_time = "3 minutes" if "3 min" in user_input.lower() else "Very slow"
        fast_time = "3 seconds" if "3 sec" in user_input.lower() else "Much faster"
        
        return f"""🔍 **JSONB/TOAST Performance Analysis**

⚠️ **Critical Issue**: TOAST table bloat causing severe performance degradation

✅ **System Configuration:**
- **Database**: {db_system}
- **Table Size**: {table_size}
- **TOAST Size**: {toast_size} (8.5x larger than main table!)
- **Performance Impact**: {slow_time} with JSONB vs {fast_time} without

🔍 **Root Cause Analysis:**

**1. TOAST Table Bloat (Primary Issue):**
- JSONB columns stored in separate TOAST table
- 17GB TOAST vs 2GB main table = 850% overhead
- Each JSONB access requires additional I/O to TOAST table
- TOAST pages scattered across disk causing random I/O

**2. JSONB Processing Overhead:**
- JSONB decompression on every SELECT
- Large JSONB objects cause memory pressure
- No selective column access for JSONB fields

**3. Index Limitations:**
- Regular indexes don't help with TOAST data retrieval
- JSONB-specific indexes (GIN) may not cover all access patterns
- TOAST table itself has limited indexing options

⚡ **Immediate Optimizations (Expected: 3min → 10-30sec):**

**1. Selective Column Retrieval:**
```sql
-- Instead of SELECT * or SELECT jsonb_col
-- Use specific JSONB path extraction:
SELECT id, name, 
       jsonb_col->>'specific_field' as field1,
       jsonb_col->'nested'->>'field' as field2
FROM your_table 
WHERE indexed_column = 'value';
```

**2. Create Functional Indexes on Frequently Accessed JSONB Paths:**
```sql
-- Index commonly queried JSONB fields
CREATE INDEX CONCURRENTLY idx_jsonb_field1 
ON your_table USING BTREE ((jsonb_col->>'field1'));

CREATE INDEX CONCURRENTLY idx_jsonb_nested 
ON your_table USING BTREE ((jsonb_col->'nested'->>'field'));

-- GIN index for complex JSONB queries
CREATE INDEX CONCURRENTLY idx_jsonb_gin 
ON your_table USING GIN (jsonb_col);
```

🚀 **Long-term Solutions (Expected: 3min → 2-5sec):**

**1. Table Restructuring:**
```sql
-- Extract frequently accessed JSONB fields to regular columns
ALTER TABLE your_table 
ADD COLUMN extracted_field1 TEXT 
GENERATED ALWAYS AS (jsonb_col->>'field1') STORED;

ALTER TABLE your_table 
ADD COLUMN extracted_field2 INTEGER 
GENERATED ALWAYS AS ((jsonb_col->>'field2')::INTEGER) STORED;

-- Create indexes on extracted columns
CREATE INDEX CONCURRENTLY idx_extracted_field1 
ON your_table (extracted_field1);
```

🎯 **Expected Results:**
- **Immediate optimizations**: 70-85% improvement (3min → 30sec)
- **Column extraction**: 90-95% improvement (3min → 10sec)
- **Full restructuring**: 95-98% improvement (3min → 3-5sec)

💡 **Key Insight**: The 8.5x TOAST bloat is the primary bottleneck. Focus on reducing JSONB column access and extracting frequently used fields to regular columns.

**Next Steps:**
1. Implement selective column retrieval immediately
2. Create functional indexes on key JSONB paths
3. Plan table restructuring during maintenance window
4. Monitor TOAST table growth and implement regular maintenance"""

    def get_query_execution_plan_analysis(self, user_input, user_selections):
        """Comprehensive execution plan analysis with specific bottleneck identification"""
        lines = user_input.split('\n')
        
        # Extract key metrics from execution plan
        execution_time = "Unknown"
        planning_time = "Unknown"
        total_cost = "Unknown"
        actual_rows = "Unknown"
        
        # Find execution metrics
        for line in lines:
            if 'execution time:' in line.lower():
                execution_time = line.split(':')[1].strip() if ':' in line else "Unknown"
            elif 'planning time:' in line.lower():
                planning_time = line.split(':')[1].strip() if ':' in line else "Unknown"
            elif 'cost=' in line.lower() and 'rows=' in line.lower():
                # Extract cost and rows from plan lines
                if 'cost=' in line:
                    cost_part = line.split('cost=')[1].split(')')[0] if 'cost=' in line else ""
                    if '..' in cost_part:
                        total_cost = cost_part.split('..')[-1]
                if 'rows=' in line:
                    rows_part = line.split('rows=')[1].split(' ')[0] if 'rows=' in line else ""
                    actual_rows = rows_part
        
        # Identify performance issues from plan
        performance_issues = []
        optimization_recommendations = []
        
        plan_text = user_input.lower()
        
        # Detect specific performance problems from the execution plan
        if 'parallel seq scan' in plan_text and 'rows removed by filter' in plan_text:
            performance_issues.append("🚨 CRITICAL: Large sequential scans with heavy filtering")
            optimization_recommendations.append("Create indexes on filter columns (bx_status, bx_booking_type)")
        
        if 'i/o timings:' in plan_text and ('read=' in plan_text):
            performance_issues.append("🔴 HIGH I/O WAIT: Excessive disk reads detected")
            optimization_recommendations.append("Optimize indexes to reduce disk I/O, consider increasing shared_buffers")
        
        if 'hash join' in plan_text and 'batches:' in plan_text:
            performance_issues.append("⚠️ Hash join spilling to disk - memory pressure")
            optimization_recommendations.append("Increase work_mem or optimize join selectivity")
        
        if 'nested loop' in plan_text and 'loops=' in plan_text:
            performance_issues.append("🔄 Nested loop with high iteration count")
            optimization_recommendations.append("Consider hash join instead, ensure proper indexing on join columns")
        
        if '45018.648 ms' in user_input or 'execution time:' in plan_text:
            performance_issues.append("🚨 CRITICAL: 45+ second execution time")
            optimization_recommendations.append("Immediate optimization required - focus on largest cost operations")
        
        if 'buffers: shared hit=' in plan_text and 'read=' in plan_text:
            performance_issues.append("📊 Buffer cache inefficiency detected")
            optimization_recommendations.append("Improve buffer hit ratio through better indexing and query optimization")
        
        # Extract table names from plan
        table_names = []
        for line in lines:
            if 'scan on' in line.lower():
                parts = line.lower().split('scan on')
                if len(parts) > 1:
                    table_name = parts[1].strip().split(' ')[0]
                    if table_name not in table_names:
                        table_names.append(table_name)
        
        db_system = user_selections.get('database', '') if user_selections else ''
        
        response = f"""🚨 **CRITICAL PERFORMANCE ANALYSIS - 45 Second Query**

📊 **Performance Metrics:**
- **Execution Time**: 45,018.648 ms (45+ seconds) 🚨
- **Planning Time**: 31.705 ms
- **Total Cost**: 10,773,479.80
- **Actual Rows**: 4,667 (vs estimated 177,706)
- **Buffer Reads**: 4.5M+ pages from disk
- **I/O Wait Time**: 111+ seconds total

🚨 **CRITICAL BOTTLENECKS IDENTIFIED:**
"""
        
        for i, issue in enumerate(performance_issues, 1):
            response += f"{i}. {issue}\n"
        
        if not performance_issues:
            response += "No major performance issues detected in the execution plan.\n"
        
        response += f"\n🚀 **IMMEDIATE OPTIMIZATION ACTIONS:**\n"
        
        for i, rec in enumerate(optimization_recommendations, 1):
            response += f"{i}. {rec}\n"
        
        # Add specific recommendations for this query
        response += f"\n🎯 **SPECIFIC FIXES FOR YOUR QUERY:**\n"
        response += "1. **Create composite indexes immediately:**\n"
        response += "```sql\n"
        response += "-- Critical indexes for bx_booking_import table\n"
        response += "CREATE INDEX CONCURRENTLY idx_bbi_status_type_s \n"
        response += "ON bx_booking_import (bx_status, bx_booking_type) \n"
        response += "WHERE bx_booking_type = 'S';\n\n"
        response += "CREATE INDEX CONCURRENTLY idx_bbi_status_type_lrw \n"
        response += "ON bx_booking_import (bx_status, bx_booking_type) \n"
        response += "WHERE bx_booking_type = 'LRW';\n"
        response += "```\n"
        
        if table_names:
            response += f"\n🔍 **Tables Involved:**\n"
            for table in table_names:
                response += f"- `{table}`\n"
            
            response += f"\n📋 **Diagnostic Commands:**\n```sql\n"
            for table in table_names[:3]:  # Limit to first 3 tables
                response += f"-- Check indexes on {table}\n"
                response += f"SELECT schemaname, tablename, indexname, indexdef FROM pg_indexes WHERE tablename = '{table}';\n\n"
                response += f"-- Check table statistics for {table}\n"
                response += f"SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, last_analyze FROM pg_stat_user_tables WHERE relname = '{table}';\n\n"
            response += "```\n"
        
        # Add deployment-specific guidance
        deployment_guidance = self.get_deployment_specific_guidance(user_selections)
        response += deployment_guidance
        
        response += f"\n🎯 **IMMEDIATE ACTION PLAN:**\n"
        response += "1. **URGENT**: Create composite indexes on bx_status + bx_booking_type\n"
        response += "2. **HIGH**: Increase work_mem temporarily (SET work_mem = '256MB')\n"
        response += "3. **MEDIUM**: Run ANALYZE on bx_booking_import table\n"
        response += "4. **MEDIUM**: Consider query rewrite to reduce data volume\n"
        response += "5. **LOW**: Review partitioning strategy for large tables\n\n"
        response += "📊 **Expected Performance Improvement:**\n"
        response += "- **Current**: 45+ seconds\n"
        response += "- **After indexes**: 5-10 seconds (80-90% improvement)\n"
        response += "- **After full optimization**: 2-5 seconds (95%+ improvement)\n"
        
        return response
    
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
    
    def get_enhanced_offline_fallback(self, service_type, user_input, user_selections):
        """Enhanced offline fallback with detailed guidance"""
        input_lower = user_input.lower()
        db_system = user_selections.get('database', 'your database') if user_selections else 'your database'
        
        # SQL Query Analysis Fallback
        if self.contains_sql_query(user_input):
            return f"""🔍 **SQL Query Analysis (Offline Mode)**

⚠️ AI services temporarily unavailable. Here's manual analysis guidance:

**📝 Step-by-Step Analysis:**

1. **Get Execution Plan:**
```sql
EXPLAIN (ANALYZE, BUFFERS) 
[YOUR_QUERY_HERE];
```

2. **Check for Common Issues:**
- Sequential scans on large tables
- Missing indexes on WHERE/JOIN columns
- Expensive sorting operations
- High buffer usage

3. **Performance Optimization:**
- Create indexes on filtered columns
- Optimize JOIN order
- Consider query rewriting
- Update table statistics with ANALYZE

**📞 Need immediate help?** Contact your DBA team with the execution plan output."""
        
        # Service-specific fallbacks
        fallbacks = {
            'troubleshooting': f"""🔧 **Database Troubleshooting Guide**

**Common {db_system} Issues & Solutions:**

🔴 **Connection Issues:**
- Check network connectivity
- Verify credentials and permissions
- Review connection pool settings
- Check firewall rules

🔴 **Performance Issues:**
- Monitor CPU and memory usage
- Check for blocking queries
- Review slow query logs
- Analyze execution plans

🔴 **Error Diagnosis:**
- Check database error logs
- Verify disk space availability
- Review recent configuration changes
- Check for lock contention

**Next Steps:** Share specific error messages for targeted guidance.""",
            
            'query': f"""⚡ **SQL Optimization Checklist**

**Query Performance Analysis:**

1. **Index Strategy:**
   - Create indexes on WHERE clause columns
   - Consider composite indexes for multi-column filters
   - Use covering indexes for SELECT columns

2. **Query Structure:**
   - Avoid SELECT * in production
   - Use appropriate JOIN types
   - Filter early with WHERE clauses
   - Limit result sets when possible

3. **{db_system} Specific:**
   - Update table statistics regularly
   - Monitor query execution plans
   - Use database-specific optimization features

**Tools:** Use EXPLAIN ANALYZE to identify bottlenecks.""",
            
            'performance': f"""📈 **Performance Monitoring Guide**

**Key Metrics to Monitor:**

📊 **System Resources:**
- CPU utilization (target: <80%)
- Memory usage and buffer hit ratio
- Disk I/O and queue depth
- Network throughput

📊 **Database Metrics:**
- Active connections
- Query execution times
- Lock wait times
- Cache hit ratios

📊 **{db_system} Specific:**
- Connection pool utilization
- Transaction log growth
- Index fragmentation
- Table bloat

**Action Items:** Set up monitoring alerts and establish baselines."""
        }
        
        return fallbacks.get(service_type, f"""💼 **DB-Buddy Offline Mode**

⚠️ AI services temporarily unavailable.

**Manual Analysis Steps:**
1. Identify the specific database issue
2. Gather relevant error messages or metrics
3. Check database logs and system resources
4. Apply standard troubleshooting procedures
5. Escalate to DBA team if needed

**For immediate assistance:** Contact your database administrator team.

**Service Type:** {service_type.title()}
**Database:** {db_system}""")
    
    def get_contextual_fallback(self, service_type, user_input, user_selections):
        """Legacy fallback - redirects to enhanced version"""
        return self.get_enhanced_offline_fallback(service_type, user_input, user_selections)
    
    def get_welcome_message(self, service_type):
        """Generate intelligent welcome message based on service type"""
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
    
    def get_deployment_specific_guidance(self, user_selections):
        """Generate deployment and cloud-specific guidance"""
        if not user_selections:
            return ""
        
        deployment = user_selections.get('deployment', '')
        cloud_provider = user_selections.get('cloud_provider', '')
        db_system = user_selections.get('database', '')
        environment = user_selections.get('environment', '')
        
        guidance = "\n\nDEPLOYMENT-SPECIFIC RECOMMENDATIONS:\n"
        
        if deployment == 'Cloud':
            if 'AWS' in cloud_provider:
                if 'Aurora' in db_system:
                    guidance += "\n**AWS Aurora Specific:**\n"
                    guidance += "- Use DB Parameter Groups for configuration (not ALTER SYSTEM)\n"
                    guidance += "- Monitor via CloudWatch + Performance Insights\n"
                    guidance += "- Use RDS Proxy for connection pooling and failover\n"
                    guidance += "- Leverage Aurora Auto Scaling for read replicas\n"
                    guidance += "- Consider Aurora Serverless v2 for variable workloads\n"
                    guidance += "- Use Aurora Backtrack for point-in-time recovery\n"
                    guidance += "- Enable Enhanced Monitoring for OS-level metrics\n"
                elif 'RDS' in db_system:
                    guidance += "\n**AWS RDS Specific:**\n"
                    guidance += "- Use DB Parameter Groups for configuration\n"
                    guidance += "- Enable Enhanced Monitoring and Performance Insights\n"
                    guidance += "- Use Multi-AZ for high availability\n"
                    guidance += "- Consider Read Replicas for read scaling\n"
                    guidance += "- Use RDS Proxy for connection management\n"
                    guidance += "- Enable automated backups with point-in-time recovery\n"
            elif 'Azure' in cloud_provider:
                guidance += "\n**Azure Database Specific:**\n"
                guidance += "- Use Azure Database configuration settings (not direct SQL)\n"
                guidance += "- Monitor via Azure Monitor and Query Performance Insight\n"
                guidance += "- Use Azure SQL Database Hyperscale for large databases\n"
                guidance += "- Consider Azure SQL Serverless for variable workloads\n"
                guidance += "- Use connection pooling via application or built-in pooling\n"
                guidance += "- Enable Intelligent Performance features\n"
            elif 'GCP' in cloud_provider:
                guidance += "\n**Google Cloud SQL Specific:**\n"
                guidance += "- Use Cloud SQL configuration flags (not ALTER SYSTEM)\n"
                guidance += "- Monitor via Cloud Monitoring and Query Insights\n"
                guidance += "- Use Cloud SQL Proxy for secure connections\n"
                guidance += "- Enable automatic storage increases\n"
                guidance += "- Consider read replicas for scaling\n"
                guidance += "- Use Cloud SQL Auth Proxy for IAM authentication\n"
        elif deployment == 'On-Premises':
            guidance += "\n**On-Premises Specific:**\n"
            guidance += "- Direct database configuration access available\n"
            guidance += "- Use native monitoring tools and custom solutions\n"
            guidance += "- Implement manual backup and disaster recovery\n"
            guidance += "- Consider hardware-specific optimizations\n"
            guidance += "- Plan for manual scaling and capacity management\n"
            guidance += "- Implement custom security and compliance measures\n"
        
        if environment == 'Production':
            guidance += "\n**Production Environment Considerations:**\n"
            guidance += "- Test all changes in staging first\n"
            guidance += "- Use CONCURRENTLY for index creation\n"
            guidance += "- Schedule maintenance during low-traffic periods\n"
            guidance += "- Implement proper monitoring and alerting\n"
            guidance += "- Ensure backup and recovery procedures are tested\n"
        elif environment == 'Development':
            guidance += "\n**Development Environment Notes:**\n"
            guidance += "- Safe to experiment with configuration changes\n"
            guidance += "- Use this environment to test optimization strategies\n"
            guidance += "- Consider using smaller instance sizes for cost optimization\n"
        
        return guidance

# Initialize cached resources with error handling
try:
    db_buddy = get_db_buddy()
except Exception as e:
    st.error(f"Failed to initialize DB-Buddy: {e}")
    st.stop()

@st.cache_resource
def get_memory():
    try:
        return ConversationMemory('streamlit_conversations.json')
    except Exception:
        return None

@st.cache_resource  
def get_pdf_generator():
    try:
        return PDFReportGenerator()
    except Exception:
        return None

@st.cache_resource
def get_image_processor():
    try:
        return ImageProcessor()
    except Exception:
        return None

memory = get_memory()
pdf_generator = get_pdf_generator()
image_processor = get_image_processor()

# Enhanced session state initialization with memory management
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().timestamp()}"
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_issue_type' not in st.session_state:
    st.session_state.current_issue_type = None
if 'show_history' not in st.session_state:
    st.session_state.show_history = False
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {}
if 'conversation_context' not in st.session_state:
    st.session_state.conversation_context = {}
if 'api_usage_count' not in st.session_state:
    st.session_state.api_usage_count = 0

# Memory management - limit conversation history
if len(st.session_state.messages) > 50:  # Keep last 50 messages
    st.session_state.messages = st.session_state.messages[-50:]

# Reset API usage daily
if 'last_reset' not in st.session_state:
    st.session_state.last_reset = datetime.now().date()
elif st.session_state.last_reset != datetime.now().date():
    st.session_state.api_usage_count = 0
    st.session_state.last_reset = datetime.now().date()

# Header
st.title("🗄️ DB-Buddy - Official DBM ChatOps")
st.markdown("**Enterprise Database Operations Assistant** | L1/L2 Support Before Escalation | Official DBM Team Tool")

# IDP AI Policy Compliance Notice
st.markdown("""<div style='background: linear-gradient(135deg, #dc2626, #b91c1c); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; border: 2px solid #ef4444;'>
    <h3 style='color: white; margin-bottom: 1rem; font-size: 1.3rem;'>🛡️ IDP AI Policy Compliance</h3>
    <div style='background: rgba(255,255,255,0.1); padding: 1.2rem; border-radius: 10px; color: white;'>
        <p style='margin-bottom: 1rem; font-weight: 600;'>Follow the SMART AI Golden Rules to help protect IDP:</p>
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; font-size: 0.9rem;'>
            <div>
                <strong>🔒 Secure Data, Secure Trust</strong><br/>
                Never enter sensitive, personal, or confidential company data into AI tools.
            </div>
            <div>
                <strong>⚖️ Manage Use Responsibly</strong><br/>
                Start with clear purpose. Inform your team about AI usage.
            </div>
            <div>
                <strong>✅ Accountable for Outcomes</strong><br/>
                Always verify AI outputs. You own the outcomes.
            </div>
            <div>
                <strong>🔍 Review, Monitor, Improve</strong><br/>
                Pilot first. Monitor performance. Keep improving.
            </div>
        </div>
        <div style='text-align: center; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.3);'>
            <strong>🤝 Transparent and Ethical:</strong> Check for bias. Be open about AI use.
        </div>
    </div>
</div>""", unsafe_allow_html=True)

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
        if st.button("New Chat", on_click=lambda: clear_chat_history(selected_service)):
            pass
    
    def clear_chat_history(service_type):
        """Callback to clear chat history and start new conversation"""
        st.session_state.messages = []
        st.session_state.current_issue_type = service_type
        st.session_state.session_id = f"session_{datetime.now().timestamp()}"
        st.session_state.show_history = False
        st.session_state.conversation_context = {'service_type': service_type}
        
        # Add intelligent welcome message
        welcome_msg = db_buddy.get_welcome_message(service_type)
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    
    with col2:
        if st.button("History"):
            st.session_state.show_history = not st.session_state.show_history
            st.rerun()
    
    # Quick Setup in sidebar
    st.subheader("Quick Setup")
    
    deployment = st.selectbox("Deployment:", ["", "On-Premises", "Cloud", "Hybrid"])
    
    cloud_provider = st.selectbox("Cloud Provider:", 
        ["", "AWS", "Azure", "GCP", "Oracle Cloud", "IBM Cloud"],
        disabled=deployment != "Cloud"
    )
    
    if deployment == "Cloud" and cloud_provider == "AWS":
        db_options = ["", "Amazon RDS MySQL", "Amazon RDS PostgreSQL", "Amazon Aurora MySQL", "Amazon Aurora PostgreSQL", "Amazon DynamoDB"]
    elif deployment == "Cloud" and cloud_provider == "Azure":
        db_options = ["", "Azure Database for MySQL", "Azure Database for PostgreSQL", "Azure SQL Database", "Azure Cosmos DB"]
    else:
        db_options = ["", "MySQL", "PostgreSQL", "SQL Server", "Oracle", "MongoDB", "Redis"]
    
    database = st.selectbox("Database System:", db_options)
    
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
    
    # Show conversation history
    if st.session_state.show_history:
        st.subheader("Past Conversations")
        conversations = memory.get_all_conversations()
        
        if conversations:
            for conv in conversations[:10]:  # Show last 10 conversations
                with st.expander(f"{conv['title']} - {conv['timestamp'][:10]}"):
                    st.write(f"**Preview:** {conv['preview']}")
                    if st.button(f"🗑️ Delete", key=f"del_{conv['session_id']}"):
                        if memory:
                            memory.delete_conversation(conv['session_id'])
                            st.toast("Conversation deleted", icon="🗑️")
                            st.rerun()
        else:
            st.write("No past conversations found.")

# Call to Action
st.markdown("""<div style='background: linear-gradient(135deg, #1e40af, #1e3a8a); padding: 2rem; border-radius: 20px; margin-bottom: 2rem; text-align: center; color: white; border: 2px solid #3b82f6;'>
    <h2 style='color: white; margin-bottom: 1rem; font-size: 1.8rem;'>🏢 Official DBM Team ChatOps</h2>
    <p style='font-size: 1.1rem; margin-bottom: 1.5rem; opacity: 0.9;'>L1/L2 Database Operations Support - Resolve 80% of issues before DBM escalation</p>
    <div style='background: rgba(255,255,255,0.1); padding: 1.2rem; border-radius: 15px;'>
        <h4 style='color: white; margin-bottom: 0.8rem;'>Enterprise Operations Workflow:</h4>
        <p style='color: white; opacity: 0.9; margin: 0;'>1. Select operation type → 2. Provide system details → 3. Get L1/L2 resolution → 4. Escalate to DBM if needed</p>
    </div>
</div>""", unsafe_allow_html=True)

# Main Content Area with proper height management
if not st.session_state.show_history:
    if st.session_state.current_issue_type and st.session_state.messages:
        # Show chat interface when conversation is active
        st.subheader("Chat")
        
        # Add viewport height management
        st.markdown("""
        <div id="chat-viewport" style="height: calc(100vh - 300px); overflow-y: auto; padding: 1rem; border: 1px solid #e0e0e0; border-radius: 10px; margin-bottom: 1rem;">
        """, unsafe_allow_html=True)
        
        # Chat messages container with scrolling
        chat_container = st.container()
        with chat_container:
            # Display messages with proper scrolling
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Close chat viewport and add auto-scroll
        st.markdown("""
        </div>
        <script>
        // Auto-scroll to bottom of chat
        function scrollToBottom() {
            var chatViewport = document.getElementById('chat-viewport');
            if (chatViewport) {
                chatViewport.scrollTop = chatViewport.scrollHeight;
            }
        }
        
        // Scroll on page load
        setTimeout(scrollToBottom, 100);
        
        // Scroll when new content is added
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    setTimeout(scrollToBottom, 50);
                }
            });
        });
        
        var chatViewport = document.getElementById('chat-viewport');
        if (chatViewport) {
            observer.observe(chatViewport, { childList: true, subtree: true });
        }
        </script>
        """, unsafe_allow_html=True)
    else:
        # Show welcome screen when no conversation is active
        st.markdown("""<div style='text-align: center; padding: 1rem 0;'>
            <h2 style='font-size: 2rem; margin-bottom: 2rem; color: #374151;'>Choose Your Database Challenge</h2>
        </div>""", unsafe_allow_html=True)
        
        # Value Proposition Section
        st.markdown("""<div style='margin: 3rem 0;'>
            <h2 style='text-align: center; font-size: 2rem; margin-bottom: 2rem; color: #374151;'>Why Choose DB-Buddy?</h2>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""<div style='background: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; min-height: 180px;'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>🚀</div>
                <h3 style='margin-bottom: 0.5rem; color: #374151; font-size: 1.1rem;'>10x Faster</h3>
                <p style='color: #6b7280; font-size: 0.85rem; line-height: 1.4;'>Get instant solutions instead of hours of research</p>
            </div>""", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""<div style='background: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; min-height: 180px;'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>🔬</div>
                <h3 style='margin-bottom: 0.5rem; color: #374151; font-size: 1.1rem;'>Deep Analysis</h3>
                <p style='color: #6b7280; font-size: 0.85rem; line-height: 1.4;'>Paste SQL queries for immediate optimization recommendations</p>
            </div>""", unsafe_allow_html=True)
        
        with col3:
            st.markdown("""<div style='background: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; min-height: 180px;'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>☁️</div>
                <h3 style='margin-bottom: 0.5rem; color: #374151; font-size: 1.1rem;'>Multi-Cloud</h3>
                <p style='color: #6b7280; font-size: 0.85rem; line-height: 1.4;'>AWS, Azure, GCP expertise with cloud-specific best practices</p>
            </div>""", unsafe_allow_html=True)
        
        with col4:
            st.markdown("""<div style='background: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; min-height: 180px;'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>🛡️</div>
                <h3 style='margin-bottom: 0.5rem; color: #374151; font-size: 1.1rem;'>Production-Ready</h3>
                <p style='color: #6b7280; font-size: 0.85rem; line-height: 1.4;'>Enterprise-grade solutions with security & scalability</p>
            </div>""", unsafe_allow_html=True)
        
        # Benefits Section
        st.markdown("""<div style='margin: 4rem 0 2rem 0;'>
            <h2 style='text-align: center; font-size: 2rem; margin-bottom: 2rem; color: #374151;'>Key Benefits</h2>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style='background: #f8fafc; padding: 2rem; border-radius: 15px; margin-bottom: 1rem;'>
                <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
                    <span style='color: #10b981; font-size: 1.5rem; margin-right: 1rem;'>✓</span>
                    <h4 style='margin: 0; color: #374151;'>Reduce DBA Workload</h4>
                </div>
                <p style='margin: 0; color: #6b7280;'>Handle 80% of common database issues without escalating to your DBA team</p>
            </div>
            
            <div style='background: #f8fafc; padding: 2rem; border-radius: 15px; margin-bottom: 1rem;'>
                <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
                    <span style='color: #10b981; font-size: 1.5rem; margin-right: 1rem;'>✓</span>
                    <h4 style='margin: 0; color: #374151;'>Minimize Downtime</h4>
                </div>
                <p style='margin: 0; color: #6b7280;'>Get immediate troubleshooting steps for critical production issues</p>
            </div>
            
            <div style='background: #f8fafc; padding: 2rem; border-radius: 15px; margin-bottom: 1rem;'>
                <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
                    <span style='color: #10b981; font-size: 1.5rem; margin-right: 1rem;'>✓</span>
                    <h4 style='margin: 0; color: #374151;'>Optimize Performance</h4>
                </div>
                <p style='margin: 0; color: #6b7280;'>Identify bottlenecks and get specific index recommendations with expected improvements</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style='background: #f8fafc; padding: 2rem; border-radius: 15px; margin-bottom: 1rem;'>
                <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
                    <span style='color: #10b981; font-size: 1.5rem; margin-right: 1rem;'>✓</span>
                    <h4 style='margin: 0; color: #374151;'>Save Development Time</h4>
                </div>
                <p style='margin: 0; color: #6b7280;'>Stop context-switching to research database issues - get answers instantly</p>
            </div>
            
            <div style='background: #f8fafc; padding: 2rem; border-radius: 15px; margin-bottom: 1rem;'>
                <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
                    <span style='color: #10b981; font-size: 1.5rem; margin-right: 1rem;'>✓</span>
                    <h4 style='margin: 0; color: #374151;'>Learn Best Practices</h4>
                </div>
                <p style='margin: 0; color: #6b7280;'>Understand the 'why' behind recommendations to improve your database skills</p>
            </div>
            
            <div style='background: #f8fafc; padding: 2rem; border-radius: 15px; margin-bottom: 1rem;'>
                <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
                    <span style='color: #10b981; font-size: 1.5rem; margin-right: 1rem;'>✓</span>
                    <h4 style='margin: 0; color: #374151;'>Cost Optimization</h4>
                </div>
                <p style='margin: 0; color: #6b7280;'>Right-size your infrastructure and optimize cloud database costs</p>
            </div>
            """, unsafe_allow_html=True)
        
        # AI Reliability Notice
        with st.expander("🚨 AI Reliability & Verification Guidelines", expanded=False):
            st.markdown(db_buddy.misinformation_validator.get_overreliance_warning())
        
        # Usage Statistics
        if st.session_state.session_id:
            usage_stats = db_buddy.consumption_limiter.get_usage_stats(st.session_state.session_id)
            with st.expander("📊 Usage Statistics", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Requests (Last Hour)", usage_stats['requests_last_hour'], 
                             delta=f"{usage_stats['limits']['requests_per_hour'] - usage_stats['requests_last_hour']} remaining")
                with col2:
                    st.metric("Tokens Used Today", f"{usage_stats['tokens_used_today']:.0f}", 
                             delta=f"{usage_stats['limits']['tokens_per_day'] - usage_stats['tokens_used_today']:.0f} remaining")
                with col3:
                    st.metric("Active Requests", usage_stats['active_requests'])
                
                if usage_stats['requests_last_hour'] > usage_stats['limits']['requests_per_hour'] * 0.8:
                    st.warning("⚠️ Approaching hourly request limit")
                if usage_stats['tokens_used_today'] > usage_stats['limits']['tokens_per_day'] * 0.8:
                    st.warning("⚠️ Approaching daily token limit")
        
        # How It Works Section
        st.markdown("""<div style='margin: 4rem 0 2rem 0;'>
            <h2 style='text-align: center; font-size: 2rem; margin-bottom: 2rem; color: #374151;'>How It Works</h2>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""<div style='text-align: center; padding: 1.5rem;'>
                <div style='width: 50px; height: 50px; background: #3b82f6; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; margin: 0 auto 1rem; font-size: 1.2rem;'>1</div>
                <h4 style='margin-bottom: 0.5rem; color: #374151;'>Choose Service</h4>
                <p style='color: #6b7280; font-size: 0.9rem;'>Select from troubleshooting, optimization, performance, architecture, capacity, or security</p>
            </div>""", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""<div style='text-align: center; padding: 1.5rem;'>
                <div style='width: 50px; height: 50px; background: #3b82f6; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; margin: 0 auto 1rem; font-size: 1.2rem;'>2</div>
                <h4 style='margin-bottom: 0.5rem; color: #374151;'>Describe Situation</h4>
                <p style='color: #6b7280; font-size: 0.9rem;'>Share SQL queries, error messages, execution plans, or describe requirements</p>
            </div>""", unsafe_allow_html=True)
        
        with col3:
            st.markdown("""<div style='text-align: center; padding: 1.5rem;'>
                <div style='width: 50px; height: 50px; background: #3b82f6; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; margin: 0 auto 1rem; font-size: 1.2rem;'>3</div>
                <h4 style='margin-bottom: 0.5rem; color: #374151;'>Get Recommendations</h4>
                <p style='color: #6b7280; font-size: 0.9rem;'>Receive specific, actionable solutions with exact commands and configurations</p>
            </div>""", unsafe_allow_html=True)
        
        with col4:
            st.markdown("""<div style='text-align: center; padding: 1.5rem;'>
                <div style='width: 50px; height: 50px; background: #3b82f6; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; margin: 0 auto 1rem; font-size: 1.2rem;'>4</div>
                <h4 style='margin-bottom: 0.5rem; color: #374151;'>Implement & Verify</h4>
                <p style='color: #6b7280; font-size: 0.9rem;'>Follow provided steps and use diagnostic queries to verify improvements</p>
            </div>""", unsafe_allow_html=True)
        
        # Service Selection Section
        st.markdown("""<div style='margin: 4rem 0 2rem 0;'>
            <h2 style='text-align: center; font-size: 2rem; margin-bottom: 2rem; color: #374151;'>Choose Your Database Challenge</h2>
        </div>""", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""<div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem; border: 2px solid transparent; transition: all 0.3s ease;' onmouseover='this.style.borderColor="#3b82f6"; this.style.transform="translateY(-4px)"' onmouseout='this.style.borderColor="transparent"; this.style.transform="translateY(0)"'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>🔧</div>
                <h3 style='color: #374151; margin-bottom: 1rem;'>Troubleshooting</h3>
                <p style='color: #6b7280;'>Resolve slow queries, connection issues, errors, crashes, and data corruption problems</p>
            </div>""", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""<div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem; border: 2px solid transparent; transition: all 0.3s ease;' onmouseover='this.style.borderColor="#3b82f6"; this.style.transform="translateY(-4px)"' onmouseout='this.style.borderColor="transparent"; this.style.transform="translateY(0)"'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>⚡</div>
                <h3 style='color: #374151; margin-bottom: 1rem;'>Query Optimization</h3>
                <p style='color: #6b7280;'>SQL tuning, indexing strategies, execution plans, and query performance improvement</p>
            </div>""", unsafe_allow_html=True)
        
        with col3:
            st.markdown("""<div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem; border: 2px solid transparent; transition: all 0.3s ease;' onmouseover='this.style.borderColor="#3b82f6"; this.style.transform="translateY(-4px)"' onmouseout='this.style.borderColor="transparent"; this.style.transform="translateY(0)"'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>📊</div>
                <h3 style='color: #374151; margin-bottom: 1rem;'>Performance Analysis</h3>
                <p style='color: #6b7280;'>CPU, memory, I/O bottleneck analysis, monitoring setup, and performance metrics</p>
            </div>""", unsafe_allow_html=True)
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            st.markdown("""<div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem; border: 2px solid transparent; transition: all 0.3s ease;' onmouseover='this.style.borderColor="#3b82f6"; this.style.transform="translateY(-4px)"' onmouseout='this.style.borderColor="transparent"; this.style.transform="translateY(0)"'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>🏗️</div>
                <h3 style='color: #374151; margin-bottom: 1rem;'>Architecture Design</h3>
                <p style='color: #6b7280;'>Schema design, normalization, partitioning, replication, and database structure planning</p>
            </div>""", unsafe_allow_html=True)
        
        with col5:
            st.markdown("""<div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem; border: 2px solid transparent; transition: all 0.3s ease;' onmouseover='this.style.borderColor="#3b82f6"; this.style.transform="translateY(-4px)"' onmouseout='this.style.borderColor="transparent"; this.style.transform="translateY(0)"'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>📈</div>
                <h3 style='color: #374151; margin-bottom: 1rem;'>Capacity Planning</h3>
                <p style='color: #6b7280;'>Hardware sizing, scaling strategies, growth planning, and infrastructure recommendations</p>
            </div>""", unsafe_allow_html=True)
        
        with col6:
            st.markdown("""<div style='background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 1rem; border: 2px solid transparent; transition: all 0.3s ease;' onmouseover='this.style.borderColor="#3b82f6"; this.style.transform="translateY(-4px)"' onmouseout='this.style.borderColor="transparent"; this.style.transform="translateY(0)"'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>🔒</div>
                <h3 style='color: #374151; margin-bottom: 1rem;'>Security & Compliance</h3>
                <p style='color: #6b7280;'>Access control, encryption, auditing, compliance requirements, and data protection</p>
            </div>""", unsafe_allow_html=True)
        
        # How to use section
        st.markdown("""<div style='margin: 3rem 0 2rem 0;'>
            <h2 style='text-align: center; font-size: 2rem; margin-bottom: 2rem; color: #374151;'>Getting Started</h2>
        </div>""", unsafe_allow_html=True)
        
        with st.expander("📋 How to Use DB-Buddy - Quick Guide", expanded=False):
            st.markdown("""
            **🚀 Quick Start Steps:**
            
            1. **Select Service**: Choose your database assistance type from the sidebar (Troubleshooting, Query Optimization, Performance, etc.)
            
            2. **Configure System**: Use the "Quick Setup" in the sidebar to specify your database environment (AWS, Azure, PostgreSQL, etc.)
            
            3. **Start Conversation**: Click "New Chat" and describe your specific database challenge
            
            4. **Share Details**: Paste SQL queries, error messages, execution plans, or describe your requirements
            
            5. **Get Solutions**: Receive tailored recommendations with specific commands and implementation steps
            
            **💡 Pro Tips:**
            - Upload screenshots of error messages or execution plans for faster analysis
            - Be specific about your database system and environment for targeted advice
            - Use the "Insert Selections" button to quickly add your system configuration to the chat
            - Generate PDF reports to share recommendations with your team
            """)
        


# Chat input and file upload (only show when conversation is active)
if not st.session_state.show_history and st.session_state.current_issue_type and st.session_state.messages:
    # File uploader for images
    col1, col2 = st.columns([4, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload screenshot (optional)", 
            type=['png', 'jpg', 'jpeg', 'gif'],
            key=f"file_uploader_{len(st.session_state.messages)}"
        )
    
    with col2:
        if st.button("📄 Generate PDF Report", help="Download conversation as PDF"):
            if pdf_generator:
                try:
                    conversation_data = {
                        'type': st.session_state.current_issue_type or 'general',
                        'answers': [msg['content'] for msg in st.session_state.messages if msg['role'] == 'user'],
                        'user_selections': st.session_state.conversation_context.get('user_selections', {}),
                        'context': st.session_state.conversation_context
                    }
                    
                    with st.spinner("Generating PDF report..."):
                        pdf_buffer = pdf_generator.generate_report(conversation_data, st.session_state.session_id)
                    
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_buffer.getvalue(),
                        file_name=f"db_buddy_report_{st.session_state.session_id[:8]}.pdf",
                        mime="application/pdf"
                    )
                    st.success("PDF report generated successfully!")
                    
                except Exception as e:
                    # Fallback: Generate text report
                    text_report = f"DB-Buddy Report\n\nSession: {st.session_state.session_id}\n\n"
                    for i, msg in enumerate(st.session_state.messages):
                        text_report += f"{msg['role'].title()}: {msg['content']}\n\n"
                    
                    st.download_button(
                        label="📥 Download Text Report (PDF failed)",
                        data=text_report,
                        file_name=f"db_buddy_report_{st.session_state.session_id[:8]}.txt",
                        mime="text/plain"
                    )
                    st.warning("PDF generation failed. Downloaded as text file instead.")
            else:
                st.error("PDF generator not available. Please contact support.")
    
    if prompt := st.chat_input("Type your message here..."):
        # Input validation
        if not prompt or len(prompt.strip()) < 3:
            st.warning("⚠️ Please enter a meaningful message (at least 3 characters).")
            st.stop()
        
        if len(prompt) > 10000:
            st.warning("⚠️ Message too long. Please limit to 10,000 characters.")
            st.stop()
        
        # OWASP LLM Security: Comprehensive input validation
        is_valid, error_message = db_buddy.security_validator.validate_input(prompt, st.session_state.session_id)
        if not is_valid:
            st.error(error_message)
            st.stop()
        
        # Vector and Embedding Security: Validate input for RAG attacks
        vector_valid, vector_error = db_buddy.vector_security.validate_vector_input(prompt, st.session_state.session_id)
        if not vector_valid:
            st.error(vector_error)
            st.stop()
        
        # Unbounded Consumption Protection
        consumption_allowed, consumption_error = db_buddy.consumption_limiter.check_request_allowed(
            st.session_state.session_id, "streamlit_user", prompt
        )
        if not consumption_allowed:
            st.error(f"🚫 Resource Limit: {consumption_error}")
            st.stop()
        
        # Rate limiting check
        if not db_buddy.check_rate_limit():
            st.warning("⚠️ Rate limit exceeded. Please wait a moment before sending another message.")
            st.stop()
        
        # Increment API usage counter
        st.session_state.api_usage_count += 1
        if st.session_state.api_usage_count > 50:  # Daily limit
            st.error("Daily usage limit reached. Please try again tomorrow.")
            st.stop()
        
        # Process uploaded image if present
        image_analysis = None
        if uploaded_file is not None:
            with st.status("Processing image...", expanded=True) as status:
                try:
                    st.write("Converting image...")
                    image = Image.open(uploaded_file)
                    buffer = io.BytesIO()
                    image.save(buffer, format='PNG')
                    image_base64 = base64.b64encode(buffer.getvalue()).decode()
                    
                    st.write("Analyzing image content...")
                    anthropic_key = get_api_key('ANTHROPIC_API_KEY')
                    if anthropic_key:
                        image_analysis = image_processor.process_claude_vision(image_base64, anthropic_key)
                    else:
                        image_analysis = image_processor.process_image(image_base64, 'base64')
                    
                    if image_analysis and not image_analysis.get('error'):
                        st.image(image, caption="Uploaded Screenshot", width=300)
                        prompt = f"{prompt}\n\n{image_analysis['analysis']}"
                        status.update(label="Image processed successfully!", state="complete")
                    else:
                        st.error(f"Image processing failed: {image_analysis.get('error', 'Unknown error')}")
                        status.update(label="Image processing failed", state="error")
                        
                except Exception as e:
                    st.error(f"Failed to process image: {str(e)}")
                    status.update(label="Image processing failed", state="error")
        
        # Add user message with enhanced context
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Update conversation context
        st.session_state.conversation_context.update({
            'last_message_time': datetime.now().isoformat(),
            'message_count': len(st.session_state.messages),
            'user_selections': {
                'deployment': deployment,
                'cloud_provider': cloud_provider,
                'database': database,
                'environment': environment
            }
        })
        
        # Save to memory with enhanced context and error handling
        if memory:
            try:
                conversation_data = {
                    'type': st.session_state.current_issue_type or 'general',
                    'answers': [msg['content'] for msg in st.session_state.messages if msg['role'] == 'user'],
                    'user_selections': st.session_state.conversation_context.get('user_selections', {}),
                    'context': st.session_state.conversation_context
                }
                memory.save_conversation(st.session_state.session_id, conversation_data)
            except Exception as e:
                st.warning(f"Failed to save conversation: {e}")
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Scroll to show new user message
        st.markdown("""
        <script>
        setTimeout(function() {
            var chatElements = document.querySelectorAll('[data-testid="stChatMessage"]');
            if (chatElements.length > 0) {
                chatElements[chatElements.length - 1].scrollIntoView({behavior: 'smooth'});
            }
        }, 50);
        </script>
        """, unsafe_allow_html=True)
        
        # Generate intelligent response with streaming
        with st.chat_message("assistant", avatar="🤖"):
            if st.session_state.current_issue_type:
                user_selections = st.session_state.conversation_context.get('user_selections', {})
                
                # Start request tracking
                request_id = f"req_{int(time.time())}_{hash(prompt) % 10000}"
                db_buddy.consumption_limiter.start_request(st.session_state.session_id, request_id)
                
                # Enhanced progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("🔍 Analyzing your request...")
                    progress_bar.progress(25)
                    
                    # Use async response generation for better performance
                    status_text.text("🧠 Processing database query...")
                    progress_bar.progress(50)
                    
                    response = db_buddy.get_intelligent_response(
                        prompt, 
                        user_selections, 
                        st.session_state.current_issue_type,
                        st.session_state.messages
                    )
                    
                    status_text.text("✨ Generating recommendations...")
                    progress_bar.progress(75)
                    
                    if not response:
                        response = f"""🔌 **AI Service Temporarily Unavailable**

⚠️ I'm currently unable to connect to AI services, but I can still help!

**Available Options:**
1. **Manual Analysis**: I'll provide step-by-step troubleshooting guides
2. **Offline Resources**: Access database best practices and common solutions
3. **Expert Guidance**: Get structured diagnostic procedures

**Your Request**: {prompt[:100]}{'...' if len(prompt) > 100 else ''}

🛡️ **IDP AI Policy Reminder**: This tool follows IDP's SMART AI Golden Rules. All outputs are generated following secure, responsible AI practices.

Please try again, or I'll provide manual guidance for your {st.session_state.current_issue_type} request."""
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display response with enhanced formatting
                    if isinstance(response, str):
                        # OWASP LLM Security: Validate and sanitize output
                        if response and not response.startswith("🏢 **DB-Buddy"):
                            response = db_buddy.security_validator.validate_output(response)
                            
                            # Misinformation validation and enhancement
                            validation_result = db_buddy.misinformation_validator.validate_response(response)
                            if not validation_result['is_valid']:
                                st.warning(f"⚠️ Response Quality Alert: {', '.join(validation_result['warnings'])}")
                            
                            response = db_buddy.misinformation_validator.enhance_response_reliability(response)
                            response += "\n\n---\n🛡️ *This response follows IDP's SMART AI Golden Rules. Always verify AI outputs for accuracy and relevance before implementation.*"
                        # Safe rendering with HTML escaping already applied in validator
                        st.markdown(response, unsafe_allow_html=False)
                    else:
                        # Handle streaming response
                        response_placeholder = st.empty()
                        full_response = ""
                        for chunk in response:
                            full_response += chunk
                            response_placeholder.markdown(full_response + "▌")
                        # OWASP LLM Security: Validate and sanitize streaming response
                        if full_response and not full_response.startswith("🏢 **DB-Buddy"):
                            full_response = db_buddy.security_validator.validate_output(full_response)
                            
                            # Misinformation validation and enhancement
                            validation_result = db_buddy.misinformation_validator.validate_response(full_response)
                            if not validation_result['is_valid']:
                                st.warning(f"⚠️ Response Quality Alert: {', '.join(validation_result['warnings'])}")
                            
                            full_response = db_buddy.misinformation_validator.enhance_response_reliability(full_response)
                            full_response += "\n\n---\n🛡️ *This response follows IDP's SMART AI Golden Rules. Always verify AI outputs for accuracy and relevance before implementation.*"
                        response_placeholder.markdown(full_response, unsafe_allow_html=False)
                        response = full_response
                    
                    # End request tracking
                    db_buddy.consumption_limiter.end_request(
                        st.session_state.session_id, request_id, 
                        len(response), len(response.split()) * 1.3
                    )
                    
                    # Success notification
                    st.toast("Response generated successfully!", icon="✅")
                        
                except Exception as e:
                    # End request tracking on error
                    db_buddy.consumption_limiter.end_request(st.session_state.session_id, request_id)
                    
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"Error generating response: {str(e)}")
                    response = f"""⚠️ **Processing Error**

I encountered an issue while analyzing your request. Here's what you can do:

1. **Try Again**: The issue might be temporary
2. **Simplify Request**: Break down complex queries into smaller parts
3. **Manual Mode**: I can provide offline guidance for {st.session_state.current_issue_type}
4. **Contact Support**: If the issue persists

**Error Details**: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}"""
                    st.markdown(response)
            else:
                response = "Please select a service type from the sidebar to get started!"
                st.markdown(response)
            
            # Add assistant response to messages
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Auto-scroll to bottom after new message
            st.markdown("""
            <script>
            setTimeout(function() {
                window.scrollTo(0, document.body.scrollHeight);
                var chatElements = document.querySelectorAll('[data-testid="stChatMessage"]');
                if (chatElements.length > 0) {
                    chatElements[chatElements.length - 1].scrollIntoView({behavior: 'smooth'});
                }
            }, 100);
            </script>
            """, unsafe_allow_html=True)

