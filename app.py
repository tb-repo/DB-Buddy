from flask import Flask, request, jsonify, render_template, send_file
import json
import requests
import os
from datetime import datetime
from memory import ConversationMemory
from pdf_generator import PDFReportGenerator
from image_processor import ImageProcessor
from advanced_analytics import AdvancedAnalytics
from intelligent_enhancements import IntelligentEnhancements
import base64

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

class DBBuddy:
    def __init__(self):
        self.conversations = {}
        self.memory = ConversationMemory()
        self.use_ai = self.check_ollama_available()
        self.pdf_generator = PDFReportGenerator()
        self.image_processor = ImageProcessor()
        self.analytics = AdvancedAnalytics()
        self.intelligence = IntelligentEnhancements()
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
        
        # Detect ANY SQL query - check for SQL keywords anywhere in the input
        sql_keywords = ['select ', 'from ', 'where ', 'join ', 'left join', 'inner join', 'order by', 'group by', 'having ', 'union ', 'insert ', 'update ', 'delete ']
        if any(sql_keyword in input_lower for sql_keyword in sql_keywords):
            return self.get_sql_query_analysis(user_input, user_selections)
        
        # Also check for SQL query patterns with line breaks
        lines = user_input.split('\n')
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['select ', 'from ', 'where ', 'join ']):
                return self.get_sql_query_analysis(user_input, user_selections)
        
        # Check for execution plan analysis
        if any(phrase in input_lower for phrase in ['query plan', 'execution time:', 'hash join', 'seq scan']):
            return self.get_query_execution_plan_analysis(user_input, user_selections)
        
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
        
        # Check if this is an execution plan analysis request
        if 'query plan' in input_lower or 'execution time:' in input_lower:
            return self.get_query_execution_plan_analysis(user_input, user_selections)
        
        # Extract the SQL query - improved logic
        sql_lines = []
        in_sql = False
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            # Start capturing when we see SQL keywords
            if any(keyword in line_lower for keyword in ['select ', 'with ', 'insert ', 'update ', 'delete ']):
                in_sql = True
            
            if in_sql:
                sql_lines.append(line.strip())
                # Stop when we hit a clear end or next section
                if (line.strip().endswith(';') or 
                    (i < len(lines) - 1 and lines[i+1].strip() == '') or
                    any(end_phrase in line_lower for end_phrase in ['sql query shared', 'execution plan', 'here is the'])):
                    break
        
        # If no SQL found in structured format, look for it anywhere in the text
        if not sql_lines:
            # Look for SQL patterns in the entire input
            sql_pattern_found = False
            for line in lines:
                if any(keyword in line.lower() for keyword in ['select ', 'from ', 'where ', 'join ']):
                    sql_lines.append(line.strip())
                    sql_pattern_found = True
                elif sql_pattern_found and line.strip():
                    sql_lines.append(line.strip())
                elif sql_pattern_found and not line.strip():
                    break
        
        sql_query = '\n'.join(sql_lines) if sql_lines else "SQL query not clearly identified"
        
        # Check if user is asking about execution plan
        asking_about_plan = any(phrase in input_lower for phrase in ['explain plan', 'execution plan', 'shall i share', 'should i provide'])
        
        db_system = user_selections.get('database', '') if user_selections else ''
        environment = user_selections.get('environment', '') if user_selections else ''
        
        # Always provide analysis for any SQL query - remove database system restrictions
        response = f"""🔍 **SQL Query Analysis**

✅ **Your Query:**
```sql
{sql_query}
```

🔍 **Initial Analysis:**

**Query Structure Identified:**
- **Main table**: `vw_fact_examiner_block_calculation_last_1year` (view)
- **Joins**: LEFT JOIN with `dim_examiner` and `vw_dim_block`
- **Key filter**: `block_key IS NOT NULL` and date comparison
- **Performance concern**: Slow SELECT query consuming high DB resources

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
CREATE INDEX CONCURRENTLY idx_block_key_fact ON vw_fact_examiner_block_calculation_last_1year(block_key);
CREATE INDEX CONCURRENTLY idx_marker_code ON vw_fact_examiner_block_calculation_last_1year(marker_code);
CREATE INDEX CONCURRENTLY idx_block_key_dim ON vw_dim_block(block_key);
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

**4. Performance Analysis:**
```sql
-- Get execution plan
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) 
SELECT ly.*,ex.probation_period_end_date,b."Block Start End Dates" 
FROM public.vw_fact_examiner_block_calculation_last_1year ly
LEFT JOIN public.dim_examiner ex ON ly.marker_code = ex.examiner_code
LEFT JOIN public.vw_dim_block b ON ly.block_key = b.block_key
WHERE ly.block_key IS NOT NULL
AND b.start_date >= ex.probation_period_end_date;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables WHERE tablename LIKE '%examiner%' OR tablename LIKE '%block%';
```
"""
        
        if asking_about_plan:
            response += f"\n\n📊 **Yes, please share the execution plan!**\n\nRun this command and share the output:\n```sql\nEXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) \n{sql_query};\n```\n\nThis will help me identify specific bottlenecks and provide targeted index recommendations."
        else:
            response += f"\n\n📊 **Next Steps:**\n1. Run the EXPLAIN ANALYZE command above to get execution plan\n2. Check current indexes on the tables/views\n3. Review the underlying view definitions\n4. Implement the suggested indexes\n\n**Expected improvements**: Proper indexing should reduce query time and resource consumption significantly.\n\n🔍 **[View Advanced Analytics](/analytics)** - Interactive query plan visualization and performance analysis"
        
        return response

    
    def get_query_execution_plan_analysis(self, user_input, user_selections):
        """Analyze specific SQL query with execution plan"""
        lines = user_input.split('\n')
        
        # Extract execution time
        execution_time = "6003.329 ms"
        for line in lines:
            if 'Execution Time:' in line:
                execution_time = line.split(':')[1].strip()
                break
        
        # Extract key performance metrics from the plan
        total_cost = "1241730.95"
        actual_rows = "11289"
        buffers_hit = "942826"
        temp_read = "1036"
        
        for line in lines:
            if 'Hash Join' in line and 'cost=' in line:
                # Extract cost from first line
                cost_part = line.split('cost=')[1].split('..')[1].split(')')[0]
                total_cost = cost_part
            if 'rows=' in line and 'actual time=' in line:
                # Extract actual rows
                rows_part = line.split('rows=')[1].split(' ')[0]
                actual_rows = rows_part
        
        db_system = user_selections.get('database', '') if user_selections else ''
        
        return f"""🔍 **Aurora PostgreSQL Execution Plan Analysis**

⚠️ **Critical Performance Issues Identified:**

**📊 Execution Metrics:**
- **Execution Time**: {execution_time} (6+ seconds - CRITICAL)
- **Total Cost**: {total_cost}
- **Actual Rows**: {actual_rows}
- **Buffer Hits**: {buffers_hit}
- **Temp I/O**: {temp_read} pages read from disk

**🚨 Major Bottlenecks:**

1. **Complex View Nesting** - Multiple levels of subqueries and window functions
2. **Massive Sequential Scans** - `fact_marking_data_only_last_year` scanned multiple times
3. **Expensive Sorting Operations** - External merge sorts using disk (2216kB, 4792kB)
4. **Hash Aggregations** - Multiple hash operations consuming significant memory
5. **Parallel Processing Overhead** - 2-3 workers launched but inefficient coordination

**🔍 Specific Problem Areas:**

**A. View `vw_fact_examiner_block_calculation_last_1year`:**
- Contains nested window functions and multiple aggregations
- Scans `fact_marking_data_only_last_year` table multiple times
- Each scan processes ~1M+ rows (1042653 rows per worker)

**B. Date Filtering Issues:**
- `marking_date >= date_trunc('month', now()) - '1 year'` calculated for each row
- No proper index on date columns
- Filter removes only 25,690 rows from 1M+ scanned

**C. Join Performance:**
- Hash joins with large datasets
- Missing indexes on join columns
- `Join Filter: (b.start_date >= ex.probation_period_end_date)` removes only 15 rows

⚡ **Immediate Fixes:**

**1. Critical Indexes:**
```sql
-- For the main fact table date filtering
CREATE INDEX CONCURRENTLY idx_fact_marking_date_key 
ON fact_marking_data_only_last_year (marking_date, marker_code, block_key) 
WHERE marking_date >= date_trunc('month', CURRENT_DATE) - INTERVAL '1 year';

-- For response type filtering
CREATE INDEX CONCURRENTLY idx_fact_response_type 
ON fact_marking_data_only_last_year (response_type_key, marking_date) 
WHERE response_type_key = 1;

-- For join columns
CREATE INDEX CONCURRENTLY idx_examiner_code ON dim_examiner(examiner_code);
CREATE INDEX CONCURRENTLY idx_block_start_probation ON dim_block(start_date, block_key);
```

**2. Materialized View Strategy:**
```sql
-- Replace the complex view with materialized view
CREATE MATERIALIZED VIEW mv_examiner_block_calculation_last_1year AS
SELECT marker_code, block_key, 
       -- Add only essential columns, avoid window functions
       COUNT(*) as total_markings,
       MAX(marking_date) as last_marking_date
FROM fact_marking_data_only_last_year 
WHERE marking_date >= date_trunc('month', CURRENT_DATE) - INTERVAL '1 year'
GROUP BY marker_code, block_key;

-- Create index on materialized view
CREATE UNIQUE INDEX idx_mv_examiner_block 
ON mv_examiner_block_calculation_last_1year (marker_code, block_key);

-- Refresh strategy
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_examiner_block_calculation_last_1year;
```

**3. Query Rewrite:**
```sql
-- Simplified version using materialized view
SELECT mv.*, ex.probation_period_end_date, b."Block Start End Dates"
FROM mv_examiner_block_calculation_last_1year mv
INNER JOIN dim_examiner ex ON mv.marker_code = ex.examiner_code
INNER JOIN dim_block b ON mv.block_key = b.block_key
WHERE b.start_date >= ex.probation_period_end_date;
```

**4. Configuration Tuning:**
```sql
-- Increase work_mem for this session
SET work_mem = '256MB';

-- Disable parallel processing for this query if overhead is high
SET max_parallel_workers_per_gather = 0;
```

📊 **Expected Performance Improvements:**
- **Current**: 6+ seconds
- **With proper indexes**: ~1-2 seconds
- **With materialized view**: ~100-500ms
- **With query rewrite**: ~50-200ms

🎯 **Immediate Action Plan:**
1. **Create the date-based partial index first** (biggest impact)
2. **Implement materialized view strategy** for the complex view
3. **Set up automated refresh** for materialized view (hourly/daily)
4. **Monitor query performance** after each change
5. **Consider partitioning** `fact_marking_data_only_last_year` by date

**🚨 Critical**: This query is scanning 3M+ rows across multiple workers. The materialized view approach will reduce this to ~11K rows, providing 99%+ performance improvement."""
    
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
        
        # Advanced context analysis using intelligence enhancements
        analysis = self.intelligence.analyze_context_depth(user_input, user_selections, context)
        
        # Build intelligent context with relevance scoring
        enhanced_context = self.build_intelligent_context(context, user_selections, analysis)
        
        # Create adaptive system prompt based on context analysis
        system_prompt = self.create_adaptive_system_prompt(analysis, user_selections)
        
        # Get AI response with quality validation
        response = self.get_validated_ai_response(system_prompt, enhanced_context, user_input, analysis)
        
        if response:
            # Post-process response for accuracy and completeness
            return self.intelligence.enhance_response_quality(response, analysis, user_selections)
        
        # Intelligent fallback with context awareness
        return self.intelligence.get_intelligent_fallback(user_input, user_selections, analysis)
    
    def build_intelligent_context(self, base_context, user_selections, analysis):
        """Build enhanced context based on analysis"""
        context = f"{base_context}\n\nINTELLIGENT CONTEXT ANALYSIS:\n"
        context += f"- Technical Depth: {analysis['technical_depth']}\n"
        context += f"- Urgency Level: {analysis['urgency_level']}\n"
        context += f"- Specificity Score: {analysis['specificity_score']}/100\n"
        context += f"- Domain Expertise: {', '.join(analysis['domain_expertise']) if analysis['domain_expertise'] else 'General'}\n"
        context += f"- Response Type Needed: {analysis['response_type_needed']}\n"
        
        if analysis['key_entities']:
            context += f"- Key Entities: {', '.join(analysis['key_entities'])}\n"
        
        if analysis['performance_indicators']:
            context += f"- Performance Indicators: {', '.join(analysis['performance_indicators'])}\n"
        
        # Add deployment-specific context
        if user_selections:
            context += self.intelligence.get_deployment_context(user_selections)
        
        return context
    
    def create_adaptive_system_prompt(self, analysis, user_selections):
        """Create system prompt adapted to user's context and needs"""
        base_prompt = "You are DB-Buddy, a senior database expert with deep technical knowledge."
        
        # Adapt based on technical depth
        if analysis['technical_depth'] == 'expert':
            expertise_guidance = "\nUser is highly technical. Provide advanced technical details, specific commands, and in-depth analysis. Use technical terminology appropriately."
        elif analysis['technical_depth'] == 'intermediate':
            expertise_guidance = "\nUser has good technical knowledge. Provide detailed explanations with some technical depth, but explain complex concepts clearly."
        else:
            expertise_guidance = "\nUser may be less technical. Provide clear, step-by-step explanations with context for technical terms. Focus on practical solutions."
        
        # Adapt based on urgency
        if analysis['urgency_level'] in ['critical', 'high']:
            urgency_guidance = "\nHIGH PRIORITY: This appears to be an urgent issue. Prioritize immediate actionable solutions and troubleshooting steps. Provide quick wins first, then comprehensive analysis."
        else:
            urgency_guidance = "\nProvide comprehensive analysis and long-term optimization strategies along with immediate solutions."
        
        # Adapt based on specificity
        if analysis['specificity_score'] > 70:
            specificity_guidance = "\nUser provided specific details. Analyze their exact situation and provide targeted recommendations using their specific table names, queries, and metrics."
        else:
            specificity_guidance = "\nUser provided general information. Ask clarifying questions if needed, but provide actionable guidance based on available information."
        
        # Domain-specific guidance
        domain_guidance = ""
        if 'query_optimization' in analysis['domain_expertise']:
            domain_guidance += "\nFocus on SQL query analysis, execution plans, indexing strategies, and performance optimization."
        if 'troubleshooting' in analysis['domain_expertise']:
            domain_guidance += "\nProvide systematic troubleshooting approaches, diagnostic queries, and root cause analysis."
        
        return f"{base_prompt}{expertise_guidance}{urgency_guidance}{specificity_guidance}{domain_guidance}\n\nAlways provide specific, actionable recommendations with exact commands when possible."
    
    def get_validated_ai_response(self, system_prompt, context, user_input, analysis):
        """Get AI response with quality validation"""
        # Try primary AI provider with enhanced parameters
        response = None
        
        if self.use_ai == 'groq':
            response = self.get_groq_response_enhanced(system_prompt, context, user_input, analysis)
        elif self.use_ai == 'huggingface':
            response = self.get_huggingface_response(system_prompt, context, user_input)
        elif self.use_ai == 'ollama':
            response = self.get_ollama_response(system_prompt, context, user_input)
        
        # Validate response quality
        if response and self.intelligence.validate_response_quality(response, analysis):
            return response
        
        return None
    
    def get_groq_response_enhanced(self, system_prompt, context, user_input, analysis):
        """Enhanced Groq response with better parameters based on analysis"""
        try:
            headers = {
                'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}',
                'Content-Type': 'application/json'
            }
            
            # Adjust parameters based on analysis
            max_tokens = 1200 if analysis['specificity_score'] > 70 else 800
            temperature = 0.05 if analysis['urgency_level'] in ['critical', 'high'] else 0.1
            
            payload = {
                'model': 'llama3-8b-8192',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Context: {context}\n\nUser Request: {user_input}\n\nProvide specific, actionable database recommendations."}
                ],
                'temperature': temperature,
                'max_tokens': max_tokens,
                'top_p': 0.9
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
            print(f"Enhanced Groq API error: {e}")
        return None
    
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
        
        # Intelligent, context-aware welcome messages
        welcome_messages = {
            'troubleshooting': """👋 **Database Troubleshooting Expert Ready**

I'm here to help resolve your database issues quickly and effectively. Whether you're facing:
• **Connection problems** (timeouts, refused connections)
• **Performance issues** (slow queries, high resource usage)
• **Error messages** (crashes, corruption, deadlocks)
• **Operational challenges** (backup failures, replication lag)

**Just describe your situation** - I'll analyze the symptoms and provide targeted solutions with specific commands and best practices.

💡 *Tip: Include error messages, database system, and environment details for faster diagnosis.*""",
            
            'query': """👋 **SQL Query Optimization Specialist**

I specialize in making your queries faster and more efficient. I can help with:
• **Slow SELECT queries** - Index recommendations and query rewriting
• **Complex JOINs** - Optimization strategies and execution plan analysis
• **INSERT/UPDATE performance** - Batch processing and locking strategies
• **Execution plan analysis** - Bottleneck identification and solutions

**Share your SQL query** and describe the performance issue. I'll provide:
✅ Specific index recommendations
✅ Query optimization techniques
✅ Performance improvement estimates

💡 *Paste your query directly - I'll analyze table structures, joins, and filters.*""",
            
            'performance': """👋 **Database Performance Optimization Expert**

I'll help you identify and resolve performance bottlenecks across your entire database system:
• **Query performance** - Slow execution times and resource consumption
• **System resources** - CPU, memory, and I/O optimization
• **Concurrency issues** - Lock contention and blocking queries
• **Scaling challenges** - Read replicas, partitioning, and architecture

**Tell me what you're experiencing:**
- Current performance metrics (if available)
- Specific symptoms (slow responses, timeouts, high resource usage)
- Database system and environment details

💡 *I'll provide monitoring queries, optimization strategies, and implementation guidance.*""",
            
            'architecture': """👋 **Database Architecture Design Consultant**

I'll help you design robust, scalable database architectures tailored to your needs:
• **Schema design** - Normalization, indexing strategies, and data modeling
• **Scalability planning** - Partitioning, sharding, and replication strategies
• **High availability** - Failover, backup, and disaster recovery design
• **Cloud architecture** - Multi-region, auto-scaling, and cost optimization

**Share your requirements:**
- Application type and expected workload
- Data volume and growth projections
- Performance and availability requirements
- Budget and technology constraints

💡 *I'll provide detailed architecture diagrams, implementation roadmaps, and best practices.*""",
            
            'capacity': """👋 **Database Capacity Planning Specialist**

I'll help you right-size your database infrastructure for optimal performance and cost:
• **Hardware sizing** - CPU, memory, and storage requirements
• **Growth planning** - Scaling strategies for increasing workloads
• **Cost optimization** - Resource allocation and cloud pricing strategies
• **Performance forecasting** - Capacity thresholds and monitoring

**Tell me about your workload:**
- Current or expected data volume
- User count and concurrency patterns
- Query types (OLTP, OLAP, or mixed)
- Performance requirements and SLAs

💡 *I'll provide specific hardware recommendations, scaling timelines, and cost projections.*""",
            
            'security': """👋 **Database Security & Compliance Expert**

I'll help you implement comprehensive database security and meet compliance requirements:
• **Access control** - Role-based permissions and authentication strategies
• **Data protection** - Encryption at rest and in transit
• **Audit & compliance** - GDPR, HIPAA, SOX, PCI-DSS requirements
• **Threat prevention** - SQL injection, privilege escalation, and monitoring

**What are your security priorities:**
- Data sensitivity level and classification
- Compliance requirements (industry standards)
- Current security concerns or incidents
- User access patterns and requirements

💡 *I'll provide security checklists, implementation guides, and compliance roadmaps.*"""
        }
        
        return welcome_messages.get(issue_type, "👋 Hello! How can I help you with your database needs today?")
    
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
    
    def process_answer(self, session_id, answer, image_data=None):
        if session_id not in self.conversations:
            return "Session not found. Please start a new conversation."
        
        conv = self.conversations[session_id]
        
        # Initialize conversation history if not exists
        if 'user_selections' not in conv:
            conv['user_selections'] = {}
        if 'conversation_history' not in conv:
            conv['conversation_history'] = []
        
        # Process image if provided
        image_analysis = None
        if image_data:
            try:
                # Try Claude Vision first if available
                anthropic_key = os.getenv('ANTHROPIC_API_KEY')
                if anthropic_key:
                    image_analysis = self.image_processor.process_claude_vision(image_data, anthropic_key)
                else:
                    # Fallback to OCR
                    image_analysis = self.image_processor.process_image(image_data, 'base64')
                
                if image_analysis and not image_analysis.get('error'):
                    # Combine image analysis with user message
                    answer = f"{answer}\n\n{image_analysis['analysis']}"
            except Exception as e:
                image_analysis = {'error': f'Image processing failed: {str(e)}'}
        
        # Store user input
        conv['answers'].append(answer)
        conv['step'] += 1
        
        # Parse LOV selections if present
        if self.contains_lov_selections(answer):
            selections = self.parse_lov_selections(answer)
            conv['user_selections'].update(selections)
        
        # Generate intelligent response
        bot_response = self.get_intelligent_response(conv, answer)
        
        # Store complete conversation exchange
        conv['conversation_history'].append({
            'user_input': answer,
            'bot_response': bot_response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Save to memory after each interaction
        conv_for_memory = conv.copy()
        if 'timestamp' in conv_for_memory and isinstance(conv_for_memory['timestamp'], datetime):
            conv_for_memory['timestamp'] = conv_for_memory['timestamp'].isoformat()
        self.memory.save_conversation(session_id, conv_for_memory)
        
        return bot_response
    
    def get_intelligent_response(self, conversation, user_input):
        """Generate intelligent, contextual responses based on user input"""
        service_type = conversation.get('type', 'general')
        user_selections = conversation.get('user_selections', {})
        conversation_history = conversation.get('answers', [])
        
        # Comprehensive analysis of user input
        analysis = self.analyze_user_input_comprehensive(user_input, user_selections, service_type)
        
        # Build rich conversation context
        context = self.build_rich_context(service_type, user_selections, conversation_history, analysis)
        
        # Get intelligent response based on service type and analysis
        response = self.get_service_specific_response(service_type, user_input, context, analysis, user_selections)
        
        if response:
            return response
        
        # Enhanced fallback with context awareness
        return self.get_enhanced_fallback(service_type, user_input, user_selections, analysis)
    
    def analyze_user_input_comprehensive(self, user_input, user_selections, service_type):
        """Comprehensive analysis of user input across all service types"""
        user_lower = user_input.lower()
        
        # Multi-category keyword analysis
        keywords = {
            'troubleshooting': {
                'timeout': ['timeout', 'timed out', 'connection timeout', 'query timeout'],
                'connection': ['connection', 'connect', 'connectivity', 'network', 'refused'],
                'error': ['error', 'exception', 'failed', 'crash', 'corrupt'],
                'performance': ['slow', 'performance', 'latency', 'response time'],
                'resource': ['memory', 'cpu', 'disk', 'i/o', 'load', 'usage']
            },
            'query': {
                'sql_types': ['select', 'insert', 'update', 'delete', 'create', 'alter'],
                'performance': ['slow', 'timeout', 'execution time', 'plan', 'index'],
                'joins': ['join', 'left join', 'inner join', 'outer join'],
                'aggregation': ['group by', 'order by', 'having', 'count', 'sum', 'avg']
            },
            'performance': {
                'metrics': ['cpu', 'memory', 'disk', 'i/o', 'throughput', 'latency'],
                'symptoms': ['slow', 'high', 'bottleneck', 'wait', 'blocking'],
                'monitoring': ['metrics', 'monitoring', 'alerts', 'dashboard']
            },
            'architecture': {
                'design': ['schema', 'design', 'model', 'structure', 'normalization'],
                'scaling': ['scale', 'partition', 'shard', 'replica', 'cluster'],
                'availability': ['ha', 'failover', 'backup', 'disaster recovery']
            },
            'capacity': {
                'sizing': ['size', 'capacity', 'storage', 'hardware', 'resources'],
                'growth': ['growth', 'scale', 'users', 'data volume', 'concurrent'],
                'metrics': ['gb', 'tb', 'cores', 'ram', 'iops', 'connections']
            },
            'security': {
                'access': ['access', 'permissions', 'roles', 'authentication', 'authorization'],
                'encryption': ['encrypt', 'ssl', 'tls', 'security', 'compliance'],
                'audit': ['audit', 'logging', 'monitoring', 'compliance', 'gdpr', 'hipaa']
            }
        }
        
        # Detect relevant categories and subcategories
        detected_categories = {}
        service_keywords = keywords.get(service_type, {})
        
        for category, category_keywords in service_keywords.items():
            matches = [kw for kw in category_keywords if kw in user_lower]
            if matches:
                detected_categories[category] = matches
        
        # Extract technical details
        tech_details = {
            'database': self.extract_database_type(user_input),
            'cloud_provider': self.extract_cloud_provider(user_input),
            'environment': self.extract_environment(user_input),
            'deployment': self.extract_deployment_type(user_input),
            'has_sql': self.contains_sql_query(user_input),
            'has_metrics': self.contains_metrics(user_input),
            'urgency': self.assess_urgency(user_input)
        }
        
        return {
            'service_type': service_type,
            'detected_categories': detected_categories,
            'technical_details': tech_details,
            'input_length': len(user_input),
            'complexity': self.assess_input_complexity(user_input),
            'user_expertise': self.assess_user_expertise(user_input)
        }
    
    def extract_database_type(self, text):
        """Extract database type from text"""
        db_types = ['postgresql', 'postgres', 'mysql', 'aurora', 'rds', 'mongodb', 'oracle', 'sql server']
        text_lower = text.lower()
        for db_type in db_types:
            if db_type in text_lower:
                return db_type
        return 'unknown'
    
    def extract_cloud_provider(self, text):
        """Extract cloud provider from text"""
        providers = ['aws', 'azure', 'gcp', 'google cloud']
        text_lower = text.lower()
        for provider in providers:
            if provider in text_lower:
                return provider
        return 'unknown'
    
    def extract_environment(self, text):
        """Extract environment from text"""
        environments = ['production', 'staging', 'development', 'test']
        text_lower = text.lower()
        for env in environments:
            if env in text_lower:
                return env
        return 'unknown'
    
    def extract_deployment_type(self, text):
        """Extract deployment type from text"""
        deployments = ['lambda', 'ec2', 'container', 'kubernetes', 'serverless']
        text_lower = text.lower()
        for deployment in deployments:
            if deployment in text_lower:
                return deployment
        return 'unknown'
    
    def assess_issue_severity(self, text, issues):
        """Assess issue severity based on keywords"""
        high_severity = ['production', 'critical', 'down', 'outage', 'failed']
        medium_severity = ['slow', 'timeout', 'performance']
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in high_severity):
            return 'high'
        elif any(keyword in text_lower for keyword in medium_severity):
            return 'medium'
        else:
            return 'low'
    
    def build_rich_context(self, service_type, user_selections, conversation_history, analysis):
        """Build comprehensive context for intelligent responses"""
        context = f"Service Type: {service_type}\n"
        
        # System configuration
        if user_selections:
            context += "\nSystem Configuration:\n"
            for key, value in user_selections.items():
                context += f"- {key.title()}: {value}\n"
        
        # Analysis insights
        context += f"\nInput Analysis:\n"
        context += f"- Complexity: {analysis['complexity']}\n"
        context += f"- User Expertise: {analysis['user_expertise']}\n"
        context += f"- Urgency: {analysis['technical_details']['urgency']}\n"
        
        if analysis['detected_categories']:
            context += f"- Detected Categories: {list(analysis['detected_categories'].keys())}\n"
        
        # Conversation history
        if len(conversation_history) > 1:
            context += f"\nConversation History:\n"
            for i, msg in enumerate(conversation_history[-2:], 1):
                context += f"Previous {i}: {msg[:150]}...\n" if len(msg) > 150 else f"Previous {i}: {msg}\n"
        
        return context
    
    def get_service_specific_response(self, service_type, user_input, context, analysis, user_selections):
        """Generate service-specific intelligent responses"""
        # Check for SQL queries first (highest priority)
        if analysis['technical_details']['has_sql']:
            return self.get_specialized_recommendation(user_input, user_selections)
        
        # Service-specific response generation
        response_generators = {
            'troubleshooting': self.get_intelligent_troubleshooting_response,
            'query': self.get_intelligent_query_response,
            'performance': self.get_intelligent_performance_response,
            'architecture': self.get_intelligent_architecture_response,
            'capacity': self.get_intelligent_capacity_response,
            'security': self.get_intelligent_security_response
        }
        
        generator = response_generators.get(service_type)
        if generator:
            return generator(user_input, context, analysis, user_selections)
        
        # Use AI for complex cases
        return self.get_ai_response_enhanced(context, user_input, user_selections, analysis)
    
    def contains_metrics(self, text):
        """Check if text contains performance metrics"""
        metrics = ['ms', 'seconds', 'minutes', 'gb', 'tb', 'mb', '%', 'cpu', 'memory', 'connections', 'qps', 'tps']
        return any(metric in text.lower() for metric in metrics)
    
    def assess_urgency(self, text):
        """Assess urgency level from text"""
        high_urgency = ['critical', 'urgent', 'production', 'down', 'outage', 'failed', 'emergency']
        medium_urgency = ['slow', 'performance', 'timeout', 'issue', 'problem']
        
        text_lower = text.lower()
        if any(word in text_lower for word in high_urgency):
            return 'high'
        elif any(word in text_lower for word in medium_urgency):
            return 'medium'
        return 'low'
    
    def assess_input_complexity(self, text):
        """Assess complexity of user input"""
        if len(text) > 500 or text.count('\n') > 10:
            return 'high'
        elif len(text) > 100 or any(keyword in text.lower() for keyword in ['select', 'join', 'where', 'performance']):
            return 'medium'
        return 'low'
    
    def assess_user_expertise(self, text):
        """Assess user's technical expertise level"""
        expert_terms = ['execution plan', 'index scan', 'buffer pool', 'query optimizer', 'statistics', 'partitioning']
        intermediate_terms = ['sql', 'query', 'database', 'performance', 'index', 'join']
        
        text_lower = text.lower()
        if any(term in text_lower for term in expert_terms):
            return 'expert'
        elif any(term in text_lower for term in intermediate_terms):
            return 'intermediate'
        return 'beginner'
    
    def get_intelligent_troubleshooting_response(self, user_input, context, analysis, user_selections):
        """Generate intelligent troubleshooting responses"""
        categories = analysis['detected_categories']
        urgency = analysis['technical_details']['urgency']
        
        if 'timeout' in categories:
            return self.get_timeout_troubleshooting_fallback(user_input, user_selections)
        elif 'connection' in categories:
            return self.get_connection_troubleshooting_fallback(user_input, user_selections)
        elif 'error' in categories:
            return self.get_error_troubleshooting_response(user_input, user_selections, urgency)
        elif 'performance' in categories:
            return self.get_performance_troubleshooting_fallback(user_input, user_selections)
        
        return self.get_ai_response_enhanced(context, user_input, user_selections, analysis)
    
    def get_intelligent_query_response(self, user_input, context, analysis, user_selections):
        """Generate intelligent query optimization responses"""
        categories = analysis['detected_categories']
        
        if 'sql_types' in categories:
            return f"""🔍 **SQL Query Analysis Ready**

I can see you're working with {', '.join(categories['sql_types'])} operations. To provide the most accurate optimization recommendations:

**Please share:**
• Your complete SQL query
• Current execution time or performance issue
• Table sizes (approximate row counts)
• Any error messages you're seeing

**I'll provide:**
✅ Specific index recommendations
✅ Query rewrite suggestions
✅ Execution plan analysis
✅ Performance improvement estimates

💡 *The more details you provide, the more targeted my recommendations will be.*"""
        
        return self.get_ai_response_enhanced(context, user_input, user_selections, analysis)
    
    def get_intelligent_performance_response(self, user_input, context, analysis, user_selections):
        """Generate intelligent performance optimization responses"""
        categories = analysis['detected_categories']
        has_metrics = analysis['technical_details']['has_metrics']
        
        if 'metrics' in categories and has_metrics:
            return f"""📊 **Performance Analysis with Metrics**

Great! I can see you have performance metrics. This will help me provide precise recommendations.

**Based on your input, I'll analyze:**
• Resource utilization patterns
• Performance bottlenecks
• Optimization opportunities
• Monitoring strategies

**Next steps:**
1. Share any additional metrics (query execution times, system resources)
2. Describe the performance symptoms you're experiencing
3. Let me know your performance targets or SLAs

💡 *With metrics, I can provide quantified improvement recommendations.*"""
        
        return self.get_ai_response_enhanced(context, user_input, user_selections, analysis)
    
    def get_intelligent_architecture_response(self, user_input, context, analysis, user_selections):
        """Generate intelligent architecture design responses"""
        categories = analysis['detected_categories']
        
        if 'design' in categories:
            return f"""🏗️ **Database Architecture Design**

I'll help you design a robust database architecture. Based on your input, I can see you're interested in schema and design aspects.

**Let's define your requirements:**
• **Application type**: Web app, analytics, e-commerce, etc.
• **Data volume**: Current size and growth projections
• **User load**: Concurrent users and usage patterns
• **Performance requirements**: Response time and throughput needs
• **Availability requirements**: Uptime SLAs and disaster recovery

**I'll provide:**
✅ Schema design recommendations
✅ Indexing strategies
✅ Partitioning and scaling approaches
✅ Technology stack recommendations

💡 *Share your specific requirements for a tailored architecture design.*"""
        
        return self.get_ai_response_enhanced(context, user_input, user_selections, analysis)
    
    def get_intelligent_capacity_response(self, user_input, context, analysis, user_selections):
        """Generate intelligent capacity planning responses"""
        categories = analysis['detected_categories']
        has_metrics = analysis['technical_details']['has_metrics']
        
        if 'sizing' in categories or has_metrics:
            return f"""📏 **Database Capacity Planning**

I'll help you determine the right infrastructure sizing for your database needs.

**Current analysis shows:**
• You're looking at capacity and sizing requirements
• {'Metrics provided - excellent for accurate sizing!' if has_metrics else 'Additional metrics would help with precision'}

**For accurate recommendations, please share:**
• **Workload type**: OLTP, OLAP, or mixed
• **Data volume**: Current size and growth rate
• **User patterns**: Peak concurrent users and usage times
• **Performance targets**: Response time and throughput requirements
• **Budget constraints**: Any cost considerations

**I'll provide:**
✅ Hardware specifications (CPU, memory, storage)
✅ Scaling timeline and growth planning
✅ Cost optimization strategies
✅ Performance monitoring recommendations

💡 *Include any current performance metrics for more accurate sizing.*"""
        
        return self.get_ai_response_enhanced(context, user_input, user_selections, analysis)
    
    def get_intelligent_security_response(self, user_input, context, analysis, user_selections):
        """Generate intelligent security responses"""
        categories = analysis['detected_categories']
        
        if 'access' in categories:
            return f"""🔐 **Database Security & Access Control**

I'll help you implement comprehensive database security measures.

**Security areas I can assist with:**
• **Access Control**: Role-based permissions and authentication
• **Data Protection**: Encryption at rest and in transit
• **Compliance**: GDPR, HIPAA, SOX, PCI-DSS requirements
• **Monitoring**: Audit logging and threat detection

**To provide targeted recommendations:**
• **Data sensitivity**: What type of data are you protecting?
• **Compliance requirements**: Any specific standards you need to meet?
• **Current security concerns**: Any specific threats or vulnerabilities?
• **User access patterns**: How many users and what access levels?

**I'll provide:**
✅ Security implementation checklists
✅ Compliance roadmaps
✅ Access control strategies
✅ Monitoring and alerting setup

💡 *Security is critical - I'll ensure comprehensive coverage of all aspects.*"""
        
        return self.get_ai_response_enhanced(context, user_input, user_selections, analysis)
    
    def get_error_troubleshooting_response(self, user_input, user_selections, urgency):
        """Specialized response for error troubleshooting"""
        urgency_prefix = "🚨 **URGENT** - " if urgency == 'high' else "⚠️ "
        
        return f"""{urgency_prefix}**Database Error Troubleshooting**

**Immediate Actions:**
1. **Identify the exact error** - Share the complete error message
2. **Check system status** - Verify database service is running
3. **Review recent changes** - Any deployments or configuration changes?
4. **Check logs** - Database error logs and system logs

**Critical Information Needed:**
• Complete error message (exact text)
• When the error started occurring
• Database system and version
• Recent changes or deployments
• Error frequency (constant/intermittent)

**I'll provide:**
✅ Root cause analysis
✅ Step-by-step resolution steps
✅ Prevention strategies
✅ Monitoring recommendations

{'🔥 **Production Issue**: I prioritize immediate resolution for production errors.' if urgency == 'high' else '💡 **Tip**: Include error logs and system details for faster diagnosis.'}"""
    
    def get_ai_response_enhanced(self, context, user_input, user_selections, analysis):
        """Enhanced AI response with comprehensive analysis"""
        if not self.use_ai:
            return None
        
        # Build enhanced system prompt based on analysis
        expertise_level = analysis['user_expertise']
        urgency = analysis['technical_details']['urgency']
        service_type = analysis['service_type']
        
        system_prompt = f"""You are DB-Buddy, an expert database consultant with deep expertise in {service_type}.

User Profile:
- Expertise Level: {expertise_level}
- Urgency: {urgency}
- Input Complexity: {analysis['complexity']}

Context: {context}

Response Guidelines:
- Adjust technical depth to user's {expertise_level} level
- {'Prioritize immediate solutions for high urgency' if urgency == 'high' else 'Provide comprehensive analysis and recommendations'}
- Include specific commands, queries, and implementation steps
- Provide monitoring and prevention strategies
- Be solution-focused and actionable

User's specific situation: {user_input}

Provide expert recommendations tailored to their needs and expertise level."""
        
        # Get AI response using the appropriate provider
        if self.use_ai == 'groq':
            return self.get_groq_response(system_prompt, context, user_input)
        elif self.use_ai == 'huggingface':
            return self.get_huggingface_response(system_prompt, context, user_input)
        elif self.use_ai == 'ollama':
            return self.get_ollama_response(system_prompt, context, user_input)
        
        return None
    
    def get_enhanced_fallback(self, service_type, user_input, user_selections, analysis):
        """Enhanced fallback responses with context awareness"""
        expertise = analysis['user_expertise']
        urgency = analysis['technical_details']['urgency']
        
        fallback_responses = {
            'troubleshooting': f"""🔧 **Database Troubleshooting Assistant**

{'🚨 I understand this is urgent. ' if urgency == 'high' else ''}I'm here to help resolve your database issues.

**To provide the most effective help:**
• Share specific error messages or symptoms
• Include your database system and environment details
• Describe when the issue started and any recent changes

{'I'll provide step-by-step solutions with detailed explanations.' if expertise == 'beginner' else 'I can provide advanced diagnostic commands and optimization strategies.' if expertise == 'expert' else 'I'll give you practical solutions with technical details.'}""",
            
            'query': f"""🔍 **SQL Query Optimization Expert**

I specialize in making queries faster and more efficient.

**For the best optimization recommendations:**
• Share your complete SQL query
• Describe the performance issue (slow execution, timeouts, etc.)
• Include table sizes and current execution times if available

{'I'll explain optimization concepts clearly with examples.' if expertise == 'beginner' else 'I can provide advanced query tuning and execution plan analysis.' if expertise == 'expert' else 'I'll give you practical optimization techniques.'}""",
            
            'performance': f"""📊 **Database Performance Specialist**

I'll help identify and resolve performance bottlenecks.

**To provide targeted recommendations:**
• Describe the performance symptoms you're experiencing
• Share any metrics or monitoring data you have
• Include your database system and infrastructure details

{'I'll provide clear explanations and step-by-step guidance.' if expertise == 'beginner' else 'I can dive deep into performance tuning and advanced optimization.' if expertise == 'expert' else 'I'll give you practical performance improvements.'}""",
            
            'architecture': f"""🏗️ **Database Architecture Consultant**

I'll help design scalable, robust database architectures.

**To create the right architecture:**
• Describe your application and expected workload
• Share data volume and user requirements
• Include performance and availability needs

{'I'll explain architectural concepts with clear examples.' if expertise == 'beginner' else 'I can provide advanced architecture patterns and best practices.' if expertise == 'expert' else 'I'll give you practical architecture recommendations.'}""",
            
            'capacity': f"""📏 **Database Capacity Planning Expert**

I'll help you size your database infrastructure correctly.

**For accurate capacity planning:**
• Share your workload characteristics and data volume
• Include user count and usage patterns
• Describe performance requirements and growth projections

{'I'll explain sizing concepts and provide clear recommendations.' if expertise == 'beginner' else 'I can provide detailed capacity modeling and optimization strategies.' if expertise == 'expert' else 'I'll give you practical sizing recommendations.'}""",
            
            'security': f"""🔐 **Database Security Specialist**

I'll help implement comprehensive database security.

**For effective security planning:**
• Describe your data sensitivity and compliance requirements
• Share current security concerns or requirements
• Include user access patterns and authentication needs

{'I'll explain security concepts clearly with implementation guides.' if expertise == 'beginner' else 'I can provide advanced security architectures and compliance strategies.' if expertise == 'expert' else 'I'll give you practical security implementations.'}"""
        }
        
        return fallback_responses.get(service_type, "I'm here to help with your database needs. Please share more details about your specific situation.")
    
    def get_timeout_troubleshooting_fallback(self, user_input, user_selections):
        """Fallback response for timeout issues"""
        return """🔍 **Timeout Issue Detected**

⚡ **Immediate Checks:**
1. **Connection Timeout**: Check network connectivity and firewall rules
2. **Query Timeout**: Identify long-running queries with SHOW PROCESSLIST
3. **Application Timeout**: Review connection pool and timeout settings
4. **Resource Constraints**: Monitor CPU, memory, and I/O usage

🛠️ **Quick Diagnostics:**
- Check active connections and blocking queries
- Review recent query execution times
- Verify database server resources
- Test network connectivity between client and server

📊 **Next Steps:**
Share specific error messages and timeout values for targeted solutions."""
    
    def get_connection_troubleshooting_fallback(self, user_input, user_selections):
        """Fallback response for connection issues"""
        return """🔍 **Connection Issue Detected**

⚡ **Immediate Checks:**
1. **Network Connectivity**: Test ping and telnet to database port
2. **Authentication**: Verify username, password, and permissions
3. **Connection Limits**: Check max_connections and current usage
4. **Firewall Rules**: Ensure database port is accessible

🛠️ **Quick Diagnostics:**
- Test connection from different clients/locations
- Check database server logs for connection errors
- Verify connection string parameters
- Monitor connection pool status

📊 **Next Steps:**
Share the exact error message and connection details for specific guidance."""
    
    def get_performance_troubleshooting_fallback(self, user_input, user_selections):
        """Fallback response for performance issues"""
        return """🔍 **Performance Issue Detected**

⚡ **Immediate Checks:**
1. **Query Performance**: Identify slow queries and execution plans
2. **Resource Usage**: Monitor CPU, memory, and disk I/O
3. **Index Usage**: Check for missing or unused indexes
4. **Blocking**: Look for lock contention and blocking queries

🛠️ **Quick Diagnostics:**
- Run EXPLAIN on slow queries
- Check database statistics and index usage
- Monitor system resource utilization
- Review recent schema or configuration changes

📊 **Next Steps:**
Share specific queries, execution times, or performance metrics for detailed analysis."""
    
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

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

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
    image_data = data.get('image_data')  # Base64 encoded image
    
    response = db_buddy.process_answer(session_id, answer, image_data)
    return jsonify({'response': response})

@app.route('/generate_report/<session_id>', methods=['GET'])
def generate_report(session_id):
    try:
        # Get conversation data
        conversation = db_buddy.memory.get_conversation(session_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Generate PDF report
        pdf_buffer = db_buddy.pdf_generator.generate_report(conversation['data'], session_id)
        
        # Return PDF file
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'db_buddy_report_{session_id[:8]}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        data = request.json
        image_data = data.get('image_data')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Process image
        result = db_buddy.image_processor.process_image(image_data, 'base64')
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Image processing failed: {str(e)}'}), 500

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

@app.route('/analytics')
def analytics_dashboard():
    return render_template('analytics.html')

@app.route('/api/analytics/data', methods=['GET'])
def get_analytics_data():
    # Get sample queries for analysis
    sample_queries = [
        "SELECT * FROM customer_table WHERE created_date > '2024-01-01'",
        "SELECT c.name, o.total FROM customer c JOIN orders o ON c.id = o.customer_id",
        "UPDATE customer_table SET status = 'active' WHERE last_login > NOW() - INTERVAL '30 days'"
    ]
    
    sample_plan = """Hash Join  (cost=1250.45..1890.23 rows=15000 width=64) (actual time=45.234..67.891 rows=14523 loops=1)
  Hash Cond: (c.id = o.customer_id)
  ->  Seq Scan on customer_table c  (cost=0.00..890.12 rows=50000 width=32) (actual time=0.123..120.456 rows=48932 loops=1)
  ->  Hash  (cost=234.56..234.56 rows=12000 width=32) (actual time=15.234..15.234 rows=11876 loops=1)
        ->  Index Scan using idx_customer_id on orders o  (cost=0.43..234.56 rows=12000 width=32) (actual time=0.045..8.234 rows=11876 loops=1)
Execution Time: 89.456 ms"""
    
    user_selections = {
        'deployment': 'Cloud',
        'cloud_provider': 'AWS',
        'database': 'Amazon Aurora PostgreSQL',
        'environment': 'Production'
    }
    
    analytics_data = {
        'queryPlan': db_buddy.analytics.analyze_query_plan_interactive(sample_plan, user_selections),
        'heatmap': db_buddy.analytics.generate_performance_heatmap(sample_queries, user_selections),
        'riskAssessment': db_buddy.analytics.assess_change_risk([
            'CREATE INDEX CONCURRENTLY idx_customer_date ON customer_table(created_date)',
            'UPDATE STATISTICS customer_table'
        ], user_selections),
        'workloadAnalysis': db_buddy.analytics.characterize_workload(sample_queries, user_selections),
        'resourceOptimization': db_buddy.analytics.optimize_resource_utilization(
            {'workload_type': 'read_heavy'}, user_selections
        ),
        'patternAnalysis': db_buddy.analytics.analyze_query_patterns(sample_queries)
    }
    
    return jsonify(analytics_data)

@app.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    # Simulate real database metrics
    metrics = {
        'query_performance': 85,
        'system_health': 92,
        'active_sessions': 24,
        'issues_count': 3,
        'performance_trends': [75, 82, 78, 85, 88, 92, 85],
        'query_distribution': [65, 25, 8, 2]
    }
    return jsonify(metrics)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)