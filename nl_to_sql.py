import json
import re
from typing import Dict, List, Optional, Tuple
import sqlite3
from datetime import datetime

# Optional database drivers
try:
    import psycopg2
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    
try:
    import pymysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

class NLToSQLConverter:
    def __init__(self):
        self.schema_cache = {}
        self.connection_cache = {}
        
    def connect_database(self, db_config: Dict) -> str:
        """Establish database connection and cache it"""
        db_type = db_config.get('type', 'sqlite')
        conn_key = f"{db_type}_{db_config.get('host', '')}_{db_config.get('database', '')}"
        
        try:
            if db_type == 'sqlite':
                conn = sqlite3.connect(db_config['database'])
            elif db_type == 'postgresql':
                if not HAS_POSTGRES:
                    return "PostgreSQL driver not installed. Run: pip install psycopg2-binary"
                conn = psycopg2.connect(**db_config)
            elif db_type == 'mysql':
                if not HAS_MYSQL:
                    return "MySQL driver not installed. Run: pip install pymysql"
                conn = pymysql.connect(**db_config)
            else:
                return "Unsupported database type"
                
            self.connection_cache[conn_key] = conn
            return conn_key
        except Exception as e:
            return f"Connection failed: {str(e)}"
    
    def analyze_schema(self, conn_key: str) -> Dict:
        """Auto-discover and cache database schema"""
        if conn_key in self.schema_cache:
            return self.schema_cache[conn_key]
            
        conn = self.connection_cache.get(conn_key)
        if not conn:
            return {"error": "No connection found"}
            
        schema = {"tables": {}, "relationships": []}
        cursor = conn.cursor()
        
        try:
            # Get tables
            if 'sqlite' in conn_key:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            elif 'postgresql' in conn_key:
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            elif 'mysql' in conn_key:
                cursor.execute("SHOW TABLES")
                
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get columns for each table
            for table in tables:
                if 'sqlite' in conn_key:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [(row[1], row[2]) for row in cursor.fetchall()]
                elif 'postgresql' in conn_key:
                    cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}'")
                    columns = cursor.fetchall()
                elif 'mysql' in conn_key:
                    cursor.execute(f"DESCRIBE {table}")
                    columns = [(row[0], row[1]) for row in cursor.fetchall()]
                    
                schema["tables"][table] = {
                    "columns": {col[0]: col[1] for col in columns},
                    "sample_data": self._get_sample_data(cursor, table)
                }
                
            self.schema_cache[conn_key] = schema
            return schema
        except Exception as e:
            return {"error": f"Schema analysis failed: {str(e)}"}
    
    def _get_sample_data(self, cursor, table: str) -> List:
        """Get sample data to understand content patterns"""
        try:
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            return cursor.fetchall()
        except:
            return []
    
    def generate_sql(self, natural_query: str, schema: Dict, ai_client=None) -> Dict:
        """Convert natural language to SQL using AI with schema context"""
        if not ai_client:
            return {"error": "AI client required for SQL generation"}
            
        # Build schema context
        schema_context = self._build_schema_context(schema)
        
        prompt = f"""Convert this natural language query to SQL:
Query: "{natural_query}"

Database Schema:
{schema_context}

Rules:
- Use exact table/column names from schema
- Include appropriate JOINs for relationships
- Add WHERE clauses for filters
- Use proper aggregations (COUNT, SUM, AVG, etc.)
- Return only the SQL query, no explanations

SQL:"""

        try:
            response = ai_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            sql_query = response.content[0].text.strip()
            sql_query = re.sub(r'^```sql\s*', '', sql_query)
            sql_query = re.sub(r'\s*```$', '', sql_query)
            
            return {
                "sql": sql_query,
                "confidence": self._assess_confidence(natural_query, sql_query, schema)
            }
        except Exception as e:
            return {"error": f"SQL generation failed: {str(e)}"}
    
    def _build_schema_context(self, schema: Dict) -> str:
        """Build readable schema description for AI"""
        context = []
        for table, info in schema.get("tables", {}).items():
            columns = ", ".join([f"{col}({dtype})" for col, dtype in info["columns"].items()])
            context.append(f"Table {table}: {columns}")
        return "\n".join(context)
    
    def _assess_confidence(self, nl_query: str, sql_query: str, schema: Dict) -> float:
        """Assess confidence in generated SQL"""
        confidence = 0.5
        
        # Check if tables exist in schema
        tables_in_sql = re.findall(r'FROM\s+(\w+)|JOIN\s+(\w+)', sql_query, re.IGNORECASE)
        valid_tables = sum(1 for table_match in tables_in_sql 
                          for table in table_match if table and table in schema.get("tables", {}))
        
        if valid_tables > 0:
            confidence += 0.3
            
        # Check for common patterns
        if any(word in nl_query.lower() for word in ['count', 'total', 'sum', 'average']):
            if any(func in sql_query.upper() for func in ['COUNT', 'SUM', 'AVG']):
                confidence += 0.2
                
        return min(confidence, 1.0)
    
    def execute_query(self, conn_key: str, sql_query: str, limit: int = 100) -> Dict:
        """Safely execute SQL query with limits"""
        conn = self.connection_cache.get(conn_key)
        if not conn:
            return {"error": "No connection found"}
            
        # Security checks
        if not self._is_safe_query(sql_query):
            return {"error": "Query contains potentially unsafe operations"}
            
        try:
            cursor = conn.cursor()
            
            # Add LIMIT if not present for SELECT queries
            if sql_query.strip().upper().startswith('SELECT') and 'LIMIT' not in sql_query.upper():
                sql_query += f" LIMIT {limit}"
                
            cursor.execute(sql_query)
            
            if sql_query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                return {
                    "success": True,
                    "columns": columns,
                    "data": results,
                    "row_count": len(results),
                    "query": sql_query
                }
            else:
                conn.commit()
                return {
                    "success": True,
                    "message": f"Query executed successfully. Rows affected: {cursor.rowcount}",
                    "query": sql_query
                }
                
        except Exception as e:
            return {"error": f"Query execution failed: {str(e)}"}
    
    def _is_safe_query(self, sql_query: str) -> bool:
        """Basic security check for SQL queries"""
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = sql_query.upper()
        
        # Allow only SELECT queries by default
        if not query_upper.strip().startswith('SELECT'):
            return False
            
        # Check for dangerous keywords in SELECT queries
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
                
        return True
    
    def explain_results(self, query_result: Dict, original_query: str, ai_client=None) -> str:
        """Generate human-readable explanation of query results"""
        if not ai_client or not query_result.get("success"):
            return "Unable to explain results"
            
        if query_result.get("data"):
            data_summary = f"Found {query_result['row_count']} rows with columns: {', '.join(query_result['columns'])}"
            sample_data = str(query_result['data'][:3]) if query_result['data'] else "No data"
        else:
            data_summary = query_result.get("message", "Query completed")
            sample_data = ""
            
        prompt = f"""Explain these database query results in simple terms:

Original question: "{original_query}"
SQL executed: {query_result.get('query', '')}
Results: {data_summary}
Sample data: {sample_data}

Provide a clear, non-technical explanation of what the data shows."""

        try:
            response = ai_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except:
            return f"Query returned {query_result.get('row_count', 0)} results"

# Integration class for DB-Buddy
class AskYourDatabaseTool:
    def __init__(self, ai_client=None):
        self.converter = NLToSQLConverter()
        self.ai_client = ai_client
        self.active_connections = {}
    
    def process_natural_query(self, user_input: str, db_config: Dict = None) -> Dict:
        """Main interface for processing natural language database queries"""
        
        # Connect to database if config provided
        if db_config:
            conn_key = self.converter.connect_database(db_config)
            if "failed" in conn_key.lower():
                return {"error": conn_key}
            self.active_connections['current'] = conn_key
        
        conn_key = self.active_connections.get('current')
        if not conn_key:
            return {"error": "No database connection. Please provide database configuration."}
        
        # Analyze schema
        schema = self.converter.analyze_schema(conn_key)
        if "error" in schema:
            return schema
            
        # Generate SQL
        sql_result = self.converter.generate_sql(user_input, schema, self.ai_client)
        if "error" in sql_result:
            return sql_result
            
        # Execute query
        execution_result = self.converter.execute_query(conn_key, sql_result["sql"])
        
        # Explain results
        explanation = self.converter.explain_results(execution_result, user_input, self.ai_client)
        
        return {
            "natural_query": user_input,
            "generated_sql": sql_result["sql"],
            "confidence": sql_result["confidence"],
            "execution_result": execution_result,
            "explanation": explanation,
            "schema_used": len(schema.get("tables", {}))
        }