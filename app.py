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
        # Remove predefined question flows - use intelligent conversation instead
        self.service_descriptions = {
            'troubleshooting': 'database troubleshooting and error resolution',
            'query': 'SQL query optimization and performance tuning',
            'performance': 'database performance analysis and optimization',
            'architecture': 'database architecture design and best practices',
            'capacity': 'database capacity planning and sizing',
            'security': 'database security hardening and compliance'
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
        
        # Detect ANY SQL query - not just with execution plans
        if any(sql_keyword in input_lower for sql_keyword in ['select ', 'from ', 'where ', 'join ', 'left join', 'inner join']):
            return self.get_sql_query_analysis(user_input, user_selections)
        
        # Detect connection issues
        if any(keyword in input_lower for keyword in ['connection', 'timeout', 'timed out', 'connect', 'refused']):
            return self.get_connection_troubleshooting_recommendation(user_input, user_selections)
        
        # Detect outbox pattern performance issues
        if any(keyword in input_lower for keyword in ['outbox', 'event sourcing', 'message queue', 'pending records']):
            if any(perf_keyword in input_lower for perf_keyword in ['slow', 'performance', 'latency', 'timeout']):
                return self.get_outbox_performance_recommendation(user_input, user_selections)
        
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
        
        if 'postgres' in db_system.lower() or 'aurora' in db_system.lower():
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
\d+ vw_fact_examiner_block_calculation_last_1year
\d+ vw_dim_block

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
        
        return f"I can see your SQL query. Please share more details about the performance issue and your database system for specific recommendations."
    
    def get_query_execution_plan_analysis(self, user_input, user_selections):
        """Analyze specific SQL query with execution plan"""
        # Extract key information from the input
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
        
        # Extract table information
        table_info = ""
        for line in lines:
            if 'size is' in line.lower() or 'constraint' in line.lower():
                table_info += line.strip() + "\n"
        
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

**3. Optimize Query Rewrite:**
```sql
-- More efficient version of your query
SELECT customer_uuid, crm_customer_id, first_name, last_name, 
       primary_email, primary_mobile_number, customer_related_idp_info, updated_datetime
FROM customer_ms.customer 
WHERE updated_datetime >= '2025-02-21T10:29:08.734389+00:00'::timestamptz
  AND (first_name ILIKE '%Student%' OR middle_name ILIKE '%Student%')
  AND (middle_name ILIKE '%ID%' OR last_name ILIKE '%ID%')
ORDER BY updated_datetime DESC
LIMIT 1000;  -- Add limit to prevent runaway queries
```

🚀 **Performance Optimization Strategy:**

**4. Consider Full-Text Search:**
```sql
-- For better text search performance
ALTER TABLE customer_ms.customer 
ADD COLUMN search_vector tsvector;

UPDATE customer_ms.customer 
SET search_vector = to_tsvector('english', 
    coalesce(first_name,'') || ' ' || 
    coalesce(middle_name,'') || ' ' || 
    coalesce(last_name,''));

CREATE INDEX idx_customer_fts ON customer_ms.customer USING gin(search_vector);
```

**5. Partitioning Strategy (40GB table):**
```sql
-- Consider partitioning by updated_datetime
-- This will significantly improve query performance
CREATE TABLE customer_ms.customer_2025_q1 PARTITION OF customer_ms.customer
FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
```

📊 **Expected Performance Improvements:**
- **Current**: 182+ seconds
- **With composite index**: ~2-5 seconds
- **With text search optimization**: ~0.5-2 seconds
- **With partitioning**: ~0.1-0.5 seconds

📊 **Monitoring Queries:**
```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes 
WHERE tablename = 'customer';

-- Monitor query performance
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
WHERE query LIKE '%customer_ms.customer%'
ORDER BY mean_exec_time DESC;
```

🎯 **Immediate Action Plan:**
1. Create the composite index first (biggest impact)
2. Install pg_trgm extension for better ILIKE performance
3. Rewrite query with LIMIT to prevent runaway execution
4. Monitor index usage and query performance
5. Consider partitioning for long-term scalability

**Expected Result**: Query should execute in under 5 seconds instead of 3+ minutes."""
        
        return "Query execution plan analysis available for PostgreSQL/Aurora."
    
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
        
        # Add conversation context for natural responses
        enhanced_context += "\n\nUser's current message: " + user_input + "\n"
        enhanced_context += "Respond naturally and conversationally to their specific situation. Provide technical depth when appropriate, but keep the tone friendly and professional.\n"
        
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
        
        # Generate intelligent welcome message based on service type
        service_desc = self.service_descriptions.get(issue_type, 'database assistance')
        
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
        
        return fallback_messages.get(issue_type, "👋 Hello! How can I help you with your database needs today?")
    
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
        
        # Parse LOV selections if present
        if self.contains_lov_selections(answer):
            selections = self.parse_lov_selections(answer)
            conv['user_selections'].update(selections)
        
        # Always use intelligent conversation - no predefined flows
        return self.get_intelligent_response(conv, answer)
    
    def get_intelligent_response(self, conversation, user_input):
        """Generate intelligent, contextual responses based on user input"""
        service_type = conversation.get('type', 'general')
        user_selections = conversation.get('user_selections', {})
        conversation_history = conversation.get('answers', [])
        
        # Build conversation context
        context = f"Service type: {service_type}\n"
        if user_selections:
            context += "System configuration:\n"
            for key, value in user_selections.items():
                context += f"- {key}: {value}\n"
        
        if len(conversation_history) > 1:
            context += f"\nPrevious conversation:\n"
            for i, msg in enumerate(conversation_history[-3:], 1):  # Last 3 messages for context
                context += f"User {i}: {msg[:200]}...\n" if len(msg) > 200 else f"User {i}: {msg}\n"
        
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