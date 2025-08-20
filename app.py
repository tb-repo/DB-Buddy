from flask import Flask, request, jsonify, render_template
import json
import requests
import os
from datetime import datetime
from memory import ConversationMemory

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

class DBBuddy:
    def __init__(self):
        self.conversations = {}
        self.memory = ConversationMemory()
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
    
    def get_specialized_recommendation(self, user_input, user_selections=None):
        """Provide specialized recommendations for common database patterns"""
        input_lower = user_input.lower()
        
        # Detect connection issues
        if any(keyword in input_lower for keyword in ['connection', 'timeout', 'timed out', 'connect', 'refused']):
            return self.get_connection_troubleshooting_recommendation(user_input, user_selections)
        
        # Detect outbox pattern performance issues
        if any(keyword in input_lower for keyword in ['outbox', 'event sourcing', 'message queue', 'pending records']):
            if any(perf_keyword in input_lower for perf_keyword in ['slow', 'performance', 'latency', 'timeout']):
                return self.get_outbox_performance_recommendation(user_input, user_selections)
        
        # Detect large table scan issues
        if any(keyword in input_lower for keyword in ['million rows', 'large table', 'full scan', 'seq scan']):
            return self.get_large_table_recommendation(user_input, user_selections)
        
        # Detect index optimization needs
        if any(keyword in input_lower for keyword in ['index', 'covering index', 'composite index']):
            return self.get_index_optimization_recommendation(user_input, user_selections)
        
        return None
    
    def get_connection_troubleshooting_recommendation(self, user_input, user_selections):
        """Specialized recommendations for database connection issues"""
        db_system = user_selections.get('database', '') if user_selections else ''
        deployment = user_selections.get('deployment', '') if user_selections else ''
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

⚡ **Immediate Diagnostic Steps:**

**1. Check Security Groups:**
```bash
# Verify Aurora security group allows Lambda subnet access
# Aurora SG should allow inbound 5432 from Lambda SG/subnets
```

**2. Verify Lambda VPC Configuration:**
```bash
# Lambda must be in same VPC as Aurora
# Lambda subnets need route to Aurora subnets
# Check Lambda execution role has VPC permissions
```

**3. Check Aurora Connection Limits:**
```sql
-- Connect to Aurora and check current connections
SELECT count(*) as current_connections FROM pg_stat_activity;
SHOW max_connections;

-- Check for connection leaks
SELECT state, count(*) 
FROM pg_stat_activity 
WHERE datname = 'your_database' 
GROUP BY state;
```

**4. Test Network Connectivity:**
```python
# Add to Lambda function for testing
import socket
def test_connection():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('your-aurora-endpoint', 5432))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Connection test failed: {{e}}")
        return False
```

🚀 **Immediate Fixes:**

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

def lambda_handler(event, context):
    conn = connection_pool.getconn()
    try:
        # Your database operations
        pass
    finally:
        connection_pool.putconn(conn)
```

**2. Configure Lambda Timeout & Retry:**
```python
# Increase Lambda timeout to 30+ seconds
# Add exponential backoff retry logic
import time
import random

def connect_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host='your-endpoint',
                database='your_db',
                user='your_user',
                password='your_password',
                connect_timeout=10
            )
            return conn
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                raise e
```

**3. Use RDS Proxy (Recommended):**
```bash
# Create RDS Proxy for Aurora cluster
# Benefits: Connection pooling, failover, security
# Lambda connects to proxy instead of direct Aurora
```

📊 **Monitoring & Verification:**

**CloudWatch Metrics to Monitor:**
- `DatabaseConnections` - Current connection count
- `ConnectionAttempts` - Failed connection attempts  
- `Lambda Duration` - Function execution time
- `Lambda Errors` - Connection failures

**Aurora Performance Insights:**
- Check for connection spikes
- Monitor wait events
- Review top SQL statements

**Verification Queries:**
```sql
-- Monitor connection patterns
SELECT 
    client_addr,
    state,
    count(*) as connections,
    max(now() - state_change) as max_idle_time
FROM pg_stat_activity 
WHERE datname = 'your_database'
GROUP BY client_addr, state;

-- Check for long-running transactions
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
```

🎯 **Expected Results:**
- **Connection Success Rate**: >99%
- **Lambda Duration**: <5 seconds typical
- **Aurora Connections**: Stable, not hitting limits
- **Error Rate**: <1% connection failures

🛡️ **Production Best Practices:**
1. **Always use RDS Proxy** for Lambda-to-Aurora connections
2. **Set appropriate timeouts** (Lambda: 30s, DB: 10s)
3. **Implement circuit breaker** pattern for resilience
4. **Monitor connection metrics** proactively
5. **Use IAM database authentication** when possible

**Next Steps:**
1. Check security groups and VPC configuration first
2. Implement RDS Proxy if not already using
3. Add connection retry logic with exponential backoff
4. Set up CloudWatch alarms for connection failures"""
        
        return "Connection troubleshooting recommendations available for your database system."
    
    def get_outbox_performance_recommendation(self, user_input, user_selections):
        """Specialized recommendations for outbox pattern performance issues"""
        db_system = user_selections.get('database', 'PostgreSQL') if user_selections else 'PostgreSQL'
        
        if 'postgres' in db_system.lower() or 'aurora' in db_system.lower():
            return f"""🔍 **Outbox Pattern Performance Analysis**

This is a classic **hot outbox table + large backlog** scenario. Your query is scanning through massive pending records, causing high latency.

✅ **Current Situation:**
- Partitioned outbox table with 1.4M+ pending records
- Query scanning from oldest events (ORDER BY event_time ASC)
- High buffer hits and rows per call
- 4+ second average latency

🔍 **Root Cause Analysis:**
1. **Large Backlog**: 1.4M pending records means every query digs deep into old data
2. **Sequential Processing**: ORDER BY event_time ASC forces scanning from oldest records
3. **Heap Fetches**: Index doesn't cover all columns, requiring table lookups
4. **No Pagination**: Processing entire backlog instead of chunks

⚡ **Immediate Fixes:**

**1. Create Covering Index:**
```sql
CREATE INDEX CONCURRENTLY idx_outbox_covering
  ON oip_engine_ms.pub_to_topic_false (event_time ASC)
  INCLUDE (id, correlation_id, event_type, message_version, message_body,
           topic_message_id, published_at, created_at, updated_at);
```

**2. Implement Pagination Strategy:**
```sql
-- Instead of scanning entire backlog
SELECT * FROM outbox 
WHERE published_to_topic = false 
  AND event_time <= now() - interval '5 seconds'
  AND event_time > :last_processed_event_time
ORDER BY event_time ASC
LIMIT 1000;
```

🚀 **Optimization Strategy:**

**3. Batch Processing Pattern:**
- Maintain a bookmark (last_processed_event_time)
- Process in chunks of 1000-5000 records
- Update bookmark after successful processing

**4. Consider Parallel Processing:**
- Partition by event_time ranges for parallel Lambda execution
- Use multiple workers on different time windows

**5. Archive Old Records:**
```sql
-- Move old pending events to archive partition
CREATE TABLE outbox_archive PARTITION OF outbox 
FOR VALUES IN (false) 
PARTITION BY RANGE (event_time);
```

📊 **Monitoring & Verification:**

**Check Index Usage:**
```sql
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename LIKE '%outbox%';
```

**Monitor Query Performance:**
```sql
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM pub_to_topic_false 
WHERE event_time <= now() - interval '5 seconds'
  AND event_time > '2024-01-01'::timestamp
ORDER BY event_time ASC LIMIT 1000;
```

🎯 **Expected Results:**
- **Latency**: Should drop from 4s to <100ms
- **Buffer Hits**: Significant reduction due to covering index
- **Scalability**: Linear performance regardless of backlog size
- **Concurrency**: Lambda concurrency of 10 will be much more effective

**🛡️ Architecture Recommendation:**
Consider implementing a **cursor-based pagination** system where each Lambda maintains its processing position, eliminating the need to scan from the beginning each time."""
        
        return "Outbox pattern optimization recommendations available for PostgreSQL/Aurora."
    
    def get_large_table_recommendation(self, user_input, user_selections):
        """Recommendations for large table performance issues"""
        return """📊 **Large Table Performance Optimization**

✅ **Analysis Approach:**
1. **Partitioning Strategy**: Implement range/list partitioning
2. **Index Optimization**: Covering indexes and partial indexes
3. **Query Rewriting**: Avoid full table scans
4. **Archival Strategy**: Move old data to separate partitions

⚡ **Immediate Actions:**
- Add LIMIT clauses to prevent runaway queries
- Create partial indexes on frequently filtered columns
- Implement pagination for large result sets
- Use EXPLAIN ANALYZE to identify bottlenecks

🚀 **Long-term Strategy:**
- Implement table partitioning by date/range
- Consider columnar storage for analytics
- Set up automated archival processes
- Optimize maintenance operations (VACUUM, REINDEX)"""
    
    def get_index_optimization_recommendation(self, user_input, user_selections):
        """Recommendations for index optimization"""
        return """📈 **Index Optimization Strategy**

🔍 **Index Analysis:**
1. **Covering Indexes**: Include all SELECT columns to avoid heap lookups
2. **Composite Indexes**: Match WHERE clause column order
3. **Partial Indexes**: Add WHERE conditions for filtered queries
4. **Index Maintenance**: Regular REINDEX and statistics updates

⚡ **Best Practices:**
- Create indexes CONCURRENTLY in production
- Monitor index usage with pg_stat_user_indexes
- Remove unused indexes to reduce maintenance overhead
- Consider expression indexes for computed columns

🎯 **Performance Impact:**
- Covering indexes can eliminate 50-90% of I/O
- Proper composite indexes enable index-only scans
- Partial indexes reduce index size and maintenance cost"""
    
    def get_ai_response(self, context, user_input, user_selections=None):
        # First check for specialized recommendations
        specialized = self.get_specialized_recommendation(user_input, user_selections)
        if specialized:
            return specialized
            
        if not self.use_ai:
            return None
        
        # Build enhanced context with user selections and technical details
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
        
        # Add technical analysis context
        enhanced_context += "\n\nProvide detailed technical analysis including:\n"
        enhanced_context += "- Specific SQL commands and configuration changes\n"
        enhanced_context += "- Execution plan analysis and optimization strategies\n"
        enhanced_context += "- Performance impact estimates and monitoring queries\n"
        enhanced_context += "- Step-by-step implementation guidance\n"
        
        # Build cloud-specific guidance with detailed technical recommendations
        cloud_guidance = ""
        if user_selections and user_selections.get('deployment') == 'Cloud':
            cloud_provider = user_selections.get('cloud_provider', '')
            db_system = user_selections.get('database', '')
            
            if 'AWS' in cloud_provider:
                if 'Aurora' in db_system:
                    cloud_guidance = "\n\nAWS AURORA SPECIFIC GUIDANCE:\n- Use DB Parameter Groups (not ALTER SYSTEM) for configuration changes\n- Monitor via CloudWatch metrics and Performance Insights\n- Use Aurora-specific features like Global Database, Backtrack, Serverless\n- Consider Aurora Auto Scaling for read replicas\n- Use RDS Proxy for connection pooling\n- Leverage Aurora's distributed storage for better I/O performance\n- Use Aurora Performance Insights for query-level analysis\n- Consider Aurora Serverless v2 for variable workloads\n"
                elif 'RDS' in db_system:
                    cloud_guidance = "\n\nAWS RDS SPECIFIC GUIDANCE:\n- Use DB Parameter Groups for configuration changes\n- Monitor via CloudWatch and Enhanced Monitoring\n- Use Read Replicas for scaling reads\n- Consider Multi-AZ for high availability\n- Use RDS Proxy for connection management\n- Implement automated backups and point-in-time recovery\n- Use RDS Performance Insights for detailed query analysis\n"
            elif 'Azure' in cloud_provider:
                cloud_guidance = "\n\nAZURE DATABASE SPECIFIC GUIDANCE:\n- Use Azure Database configuration settings (not direct SQL commands)\n- Monitor via Azure Monitor and Query Performance Insight\n- Use Read Replicas and Hyperscale for scaling\n- Consider Azure SQL Database Serverless\n- Use connection pooling via application or Azure SQL Database\n- Leverage Intelligent Performance features for automatic tuning\n- Use Query Store for historical performance analysis\n"
            elif 'GCP' in cloud_provider:
                cloud_guidance = "\n\nGCP CLOUD SQL SPECIFIC GUIDANCE:\n- Use Cloud SQL configuration flags (not ALTER SYSTEM)\n- Monitor via Cloud Monitoring and Query Insights\n- Use Read Replicas for read scaling\n- Consider Cloud SQL Proxy for secure connections\n- Use connection pooling at application level\n- Leverage automatic storage increases and performance scaling\n- Use Query Insights for performance monitoring and optimization\n"
        
        system_prompt = f"""You are DB-Buddy, a senior database architect and performance specialist with 15+ years of experience optimizing enterprise databases. You provide detailed, actionable analysis like a senior DBA consultant.

IMPORTANT: Always consider the user's specific system configuration when providing recommendations. Tailor your advice to their exact database system, deployment type, and environment.

CLOUD DATABASE CONSIDERATIONS:
- For managed cloud databases (RDS, Aurora, Azure SQL, Cloud SQL), configuration changes are done via cloud console/CLI, not direct SQL commands
- Parameter groups, configuration flags, and service-specific settings control database behavior
- Cloud monitoring tools provide better insights than traditional database queries
- Scaling, backup, and maintenance are handled differently in cloud environments{cloud_guidance}

YOUR ANALYSIS APPROACH:
1. **Identify the Root Cause**: Don't just suggest generic fixes - analyze the specific problem
2. **Explain the "Why"**: Help users understand what's happening under the hood
3. **Provide Multiple Solutions**: Offer immediate fixes, medium-term optimizations, and long-term strategies
4. **Include Specific Code**: Give exact SQL, configuration changes, and monitoring queries
5. **Quantify Impact**: Estimate performance improvements where possible

When analyzing slow queries:
- Examine execution plans in detail
- Identify index usage patterns
- Calculate row estimates vs actual rows
- Analyze buffer hits and I/O patterns
- Consider partitioning strategies
- Evaluate query rewrite opportunities

For performance issues:
- Analyze wait events and bottlenecks
- Review resource utilization (CPU, memory, I/O)
- Examine connection patterns and concurrency
- Consider caching strategies
- Evaluate hardware/instance sizing

Database-specific expertise:
- **PostgreSQL/Aurora PostgreSQL**: EXPLAIN ANALYZE, pg_stat_*, vacuum strategies, partitioning, connection pooling
- **MySQL/Aurora MySQL**: EXPLAIN FORMAT=JSON, SHOW ENGINE INNODB STATUS, query cache, buffer pool tuning
- **SQL Server**: SET STATISTICS IO/TIME, DMVs, index maintenance, query store
- **Oracle**: EXPLAIN PLAN, AWR reports, CBO statistics, partitioning strategies

Response format:
✅ **Current Situation** - Summarize what's happening
🔍 **Root Cause Analysis** - Why this is slow/problematic  
⚡ **Immediate Fixes** - What to do right now
🚀 **Optimization Strategy** - Medium-term improvements
📊 **Monitoring & Verification** - How to measure success
🎯 **Recommendations** - Best practices and next steps

Always provide specific, executable solutions with exact syntax for their database system."""
        
        if self.use_ai == 'groq':
            return self.get_groq_response(system_prompt, enhanced_context, user_input)
        elif self.use_ai == 'huggingface':
            return self.get_huggingface_response(system_prompt, enhanced_context, user_input)
        elif self.use_ai == 'ollama':
            return self.get_ollama_response(system_prompt, enhanced_context, user_input)
        
        # Fallback to rule-based recommendations if AI is not available
        return self.get_fallback_recommendation(user_input, user_selections)
    
    def get_fallback_recommendation(self, user_input, user_selections):
        """Provide rule-based recommendations when AI is not available"""
        input_lower = user_input.lower()
        
        if any(keyword in input_lower for keyword in ['slow', 'performance', 'latency']):
            return """📊 **Performance Troubleshooting Checklist**

⚡ **Immediate Actions:**
1. Check for missing indexes on WHERE/JOIN columns
2. Analyze query execution plans
3. Review recent schema changes
4. Monitor resource utilization (CPU, memory, I/O)

🔍 **Diagnostic Queries:**
- PostgreSQL: `EXPLAIN ANALYZE your_query`
- MySQL: `EXPLAIN FORMAT=JSON your_query`
- SQL Server: `SET STATISTICS IO ON; your_query`

🎯 **Common Solutions:**
- Add appropriate indexes
- Rewrite queries to avoid table scans
- Update table statistics
- Consider query result caching
- Implement connection pooling"""
        
        if any(keyword in input_lower for keyword in ['index', 'slow query']):
            return """📈 **Index Optimization Guide**

⚡ **Index Strategy:**
1. Create indexes on WHERE clause columns
2. Use composite indexes for multiple conditions
3. Consider covering indexes for SELECT columns
4. Remove unused indexes

🔍 **Analysis Commands:**
- Check index usage statistics
- Identify missing indexes from query plans
- Monitor index maintenance overhead

🎯 **Best Practices:**
- Create indexes during low-traffic periods
- Test index impact on both reads and writes
- Regular index maintenance and statistics updates"""
        
        return """🔧 **General Database Optimization**

⚡ **Quick Wins:**
1. Update database statistics
2. Check for blocking queries
3. Review connection pool settings
4. Monitor disk space and I/O

📊 **Performance Monitoring:**
- Set up query performance tracking
- Monitor resource utilization trends
- Establish performance baselines
- Implement alerting for anomalies

🎯 **Next Steps:**
- Provide specific query or error details for targeted recommendations
- Share execution plans for detailed analysis
- Consider workload-specific optimizations"""
    
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
        
        # Save to memory after each interaction
        self.memory.save_conversation(session_id, conv)
        
        # Check if user provided LOV selections
        if self.contains_lov_selections(answer):
            selections = self.parse_lov_selections(answer)
            conv['user_selections'].update(selections)
            
            # Always check if this is substantial technical input with LOV selections
            # This includes SQL queries, specific errors, or detailed technical descriptions
            if self.has_substantial_information(answer, conv['user_selections']):
                return f"🔍 **Analyzing your requirements...**\n\n" + self.generate_recommendation(conv)
            else:
                follow_up = self.get_follow_up_questions(conv['type'], conv['user_selections'])
                return follow_up
        
        # If we have detailed technical input for any category, generate recommendations
        if self.has_substantial_information(answer, conv['user_selections']) or conv['step'] >= 2:
            return f"🔍 **Analyzing your requirements...**\n\n" + self.generate_recommendation(conv)
        
        # Default fallback
        return self.generate_recommendation(conv)
    
    def has_substantial_information(self, message, user_selections):
        """Check if user provided enough information for analysis across all service categories"""
        message_lower = message.lower()
        
        # SQL queries (Query Optimization)
        has_sql_query = any(sql_keyword in message_lower for sql_keyword in [
            'select ', 'insert ', 'update ', 'delete ', 'create ', 'alter ', 'drop ',
            'from ', 'where ', 'join ', 'group by', 'order by', 'having '
        ])
        
        # Troubleshooting indicators
        troubleshooting_indicators = [
            'error', 'timeout', 'timed out', 'connection', 'refused', 'failed',
            'cannot connect', 'unable to', 'exception', 'crash', 'down', 'offline'
        ]
        
        # Performance indicators
        performance_indicators = [
            'slow', 'performance', 'cpu', 'memory', 'disk', 'i/o', 'latency',
            'throughput', 'response time', 'high usage', 'bottleneck', 'wait'
        ]
        
        # Architecture indicators
        architecture_indicators = [
            'schema', 'design', 'table structure', 'normalization', 'partition',
            'replication', 'scaling', 'architecture', 'migration', 'data model'
        ]
        
        # Capacity indicators
        capacity_indicators = [
            'sizing', 'hardware', 'storage', 'users', 'concurrent', 'load',
            'capacity', 'growth', 'scale', 'gb', 'tb', 'instances', 'cores'
        ]
        
        # Security indicators
        security_indicators = [
            'security', 'access', 'permissions', 'authentication', 'authorization',
            'encryption', 'audit', 'compliance', 'gdpr', 'hipaa', 'pci', 'sox'
        ]
        
        # Check category-specific content
        has_troubleshooting_content = any(indicator in message_lower for indicator in troubleshooting_indicators)
        has_performance_content = any(indicator in message_lower for indicator in performance_indicators)
        has_architecture_content = any(indicator in message_lower for indicator in architecture_indicators)
        has_capacity_content = any(indicator in message_lower for indicator in capacity_indicators)
        has_security_content = any(indicator in message_lower for indicator in security_indicators)
        
        # General technical content
        has_technical_content = (has_troubleshooting_content or has_performance_content or 
                               has_architecture_content or has_capacity_content or has_security_content)
        
        # System configuration
        has_system_config = user_selections and any([
            user_selections.get('deployment'),
            user_selections.get('database'),
            user_selections.get('environment'),
            user_selections.get('issue_type')
        ])
        
        # Specific measurements or details
        has_measurements = any(measure in message_lower for measure in [
            'gb', 'tb', 'mb', 'seconds', 'minutes', 'hours', 'users', '%',
            'connections', 'queries per second', 'qps', 'tps', 'rows'
        ])
        
        # Detailed description
        has_detailed_description = len(message.strip()) > 40
        
        # Consider substantial if:
        # 1. SQL query present (Query Optimization)
        # 2. Technical content + system config (all categories)
        # 3. Measurements/metrics provided (Capacity/Performance)
        # 4. Detailed description + system config (all categories)
        return (has_sql_query or 
                (has_technical_content and has_system_config) or 
                (has_measurements and has_system_config) or 
                (has_detailed_description and has_system_config and has_technical_content))
    
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

@app.route('/conversations', methods=['GET'])
def get_conversations():
    conversations = db_buddy.memory.get_all_conversations()
    return jsonify({'conversations': conversations})

@app.route('/conversation/<session_id>', methods=['GET'])
def get_conversation(session_id):
    conversation = db_buddy.memory.get_conversation(session_id)
    if conversation:
        return jsonify({'conversation': conversation})
    return jsonify({'error': 'Conversation not found'}), 404

@app.route('/conversation/<session_id>', methods=['DELETE'])
def delete_conversation(session_id):
    db_buddy.memory.delete_conversation(session_id)
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)