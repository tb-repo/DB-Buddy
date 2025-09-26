"""
Dynamic AI Response Engine for Enterprise-Grade Database Assistance
Replaces static templates with intelligent, personalized AI generation
"""

import os
import requests
import json
import re
from datetime import datetime

class DynamicAIEngine:
    def __init__(self, use_ai_provider):
        self.use_ai = use_ai_provider
        self.temperature_settings = {
            'critical': 0.05,    # Minimal creativity for production issues
            'high': 0.1,         # Low creativity for urgent issues
            'medium': 0.15,      # Balanced for standard issues
            'low': 0.2           # Slightly more creative for planning
        }
        
    def analyze_jsonb_toast_performance(self, user_input, user_selections):
        """Dynamic AI analysis of JSONB/TOAST performance issues"""
        if not self.use_ai:
            return self._fallback_jsonb_analysis(user_input, user_selections)
        
        # Extract specific details from user input
        analysis = self._extract_performance_details(user_input)
        
        # Build intelligent context
        context = self._build_jsonb_context(analysis, user_selections)
        
        # Generate dynamic response with optimal temperature
        return self._generate_dynamic_response(context, user_input, analysis)
    
    def _extract_performance_details(self, user_input):
        """Extract specific performance metrics and details from user input"""
        analysis = {
            'table_size': self._extract_table_size(user_input),
            'toast_size': self._extract_toast_size(user_input),
            'execution_times': self._extract_execution_times(user_input),
            'table_names': self._extract_table_names(user_input),
            'column_names': self._extract_column_names(user_input),
            'database_type': self._extract_database_type(user_input),
            'environment': self._extract_environment(user_input),
            'urgency_level': self._assess_urgency(user_input),
            'technical_depth': self._assess_technical_depth(user_input),
            'specific_queries': self._extract_sql_queries(user_input)
        }
        return analysis
    
    def _extract_table_size(self, text):
        """Extract table size from text"""
        patterns = [
            r'(\d+(?:\.\d+)?)\s*gb\s+(?:base\s+)?table',
            r'table.*?(\d+(?:\.\d+)?)\s*gb',
            r'(\d+(?:\.\d+)?)\s*gb.*?table'
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return f"{match.group(1)} GB"
        return "Unknown size"
    
    def _extract_toast_size(self, text):
        """Extract TOAST table size from text"""
        patterns = [
            r'(\d+(?:\.\d+)?)\s*gb\s+toast',
            r'toast.*?(\d+(?:\.\d+)?)\s*gb',
            r'(\d+(?:\.\d+)?)\s*gb.*?toast'
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return f"{match.group(1)} GB"
        return "Unknown TOAST size"
    
    def _extract_execution_times(self, text):
        """Extract execution times from text"""
        times = {}
        
        # Pattern for "X seconds" or "X minutes"
        time_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:sec|second)s?',
            r'(\d+(?:\.\d+)?)\s*(?:min|minute)s?',
            r'around\s+(\d+)\s*(?:min|minute)s?',
            r'taking\s+(\d+)\s*(?:min|minute)s?'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                times['execution_time'] = matches
        
        return times
    
    def _extract_table_names(self, text):
        """Extract table names from text"""
        # Look for schema.table patterns
        schema_table_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(schema_table_pattern, text)
        
        # Also look for table names mentioned in context
        table_keywords = ['table', 'from', 'join', 'update', 'insert into']
        table_names = []
        
        for match in matches:
            table_names.append(match)
        
        return table_names if table_names else ["table"]
    
    def _extract_column_names(self, text):
        """Extract column names, especially JSONB columns"""
        jsonb_patterns = [
            r'jsonb\s+columns?[:\s]*([a-zA-Z_][a-zA-Z0-9_,\s]*)',
            r'json\s+columns?[:\s]*([a-zA-Z_][a-zA-Z0-9_,\s]*)',
            r'these\s+are\s+the\s+json\s+columns?[:\s]*([a-zA-Z_][a-zA-Z0-9_,\s]*)'
        ]
        
        columns = []
        for pattern in jsonb_patterns:
            match = re.search(pattern, text.lower())
            if match:
                # Split by comma and clean up
                cols = [col.strip() for col in match.group(1).split(',')]
                columns.extend(cols)
        
        return columns if columns else ["jsonb_column"]
    
    def _extract_database_type(self, text):
        """Extract database type from text"""
        db_types = {
            'postgresql': ['postgresql', 'postgres', 'pg'],
            'mysql': ['mysql', 'mariadb'],
            'oracle': ['oracle'],
            'sql_server': ['sql server', 'sqlserver', 'mssql'],
            'mongodb': ['mongodb', 'mongo']
        }
        
        text_lower = text.lower()
        for db_type, keywords in db_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return db_type
        
        return 'postgresql'  # Default assumption for JSONB
    
    def _extract_environment(self, text):
        """Extract environment details"""
        env_patterns = {
            'aws': ['aws', 'rds', 'aurora'],
            'azure': ['azure', 'sql database'],
            'gcp': ['gcp', 'google cloud', 'cloud sql'],
            'on_premise': ['on-premise', 'on premise', 'local']
        }
        
        text_lower = text.lower()
        for env_type, keywords in env_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return env_type
        
        return 'cloud'
    
    def _assess_urgency(self, text):
        """Assess urgency level from text"""
        critical_keywords = ['production', 'critical', 'urgent', 'down', 'outage', 'failing']
        high_keywords = ['slow', 'performance', 'timeout', 'minutes', 'taking around']
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in critical_keywords):
            return 'critical'
        elif any(keyword in text_lower for keyword in high_keywords):
            return 'high'
        else:
            return 'medium'
    
    def _assess_technical_depth(self, text):
        """Assess user's technical expertise level"""
        expert_terms = ['toast', 'jsonb', 'execution plan', 'de-toast', 'gin index', 'vacuum']
        intermediate_terms = ['query', 'performance', 'index', 'database', 'table']
        
        text_lower = text.lower()
        expert_count = sum(1 for term in expert_terms if term in text_lower)
        intermediate_count = sum(1 for term in intermediate_terms if term in text_lower)
        
        if expert_count >= 2:
            return 'expert'
        elif intermediate_count >= 3:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _extract_sql_queries(self, text):
        """Extract SQL queries from text"""
        # Look for SQL query patterns
        sql_patterns = [
            r'(select\s+.*?(?:;|\n\s*\n))',
            r'(insert\s+.*?(?:;|\n\s*\n))',
            r'(update\s+.*?(?:;|\n\s*\n))',
            r'(create\s+.*?(?:;|\n\s*\n))'
        ]
        
        queries = []
        for pattern in sql_patterns:
            matches = re.findall(pattern, text.lower(), re.DOTALL)
            queries.extend(matches)
        
        return queries
    
    def _build_jsonb_context(self, analysis, user_selections):
        """Build intelligent context for JSONB performance analysis"""
        context = f"""JSONB/TOAST Performance Analysis Context:

SPECIFIC USER ENVIRONMENT:
- Database: {analysis['database_type'].upper()}
- Environment: {analysis['environment']}
- Table Size: {analysis['table_size']}
- TOAST Size: {analysis['toast_size']}
- Execution Times: {analysis['execution_times']}
- Table Names: {', '.join(analysis['table_names'])}
- JSONB Columns: {', '.join(analysis['column_names'])}
- User Expertise: {analysis['technical_depth']}
- Urgency Level: {analysis['urgency_level']}

USER SELECTIONS:
{json.dumps(user_selections, indent=2) if user_selections else 'No additional selections'}

ANALYSIS REQUIREMENTS:
1. Use EXACT table names and column names from user input
2. Reference SPECIFIC performance metrics mentioned
3. Provide personalized recommendations based on their environment
4. Adjust technical depth to user's expertise level
5. Address urgency level appropriately
6. Include specific commands using their actual table/column names
"""
        return context
    
    def _generate_dynamic_response(self, context, user_input, analysis):
        """Generate dynamic AI response with optimal temperature"""
        if not self.use_ai:
            return self._fallback_jsonb_analysis(user_input, None)
        
        # Select optimal temperature based on urgency
        temperature = self.temperature_settings[analysis['urgency_level']]
        
        # Build system prompt for JSONB analysis
        system_prompt = self._build_jsonb_system_prompt(analysis)
        
        # Generate response using AI provider
        if self.use_ai == 'groq':
            return self._get_groq_jsonb_response(system_prompt, context, user_input, temperature)
        elif self.use_ai == 'huggingface':
            return self._get_huggingface_response(system_prompt, context, user_input)
        elif self.use_ai == 'ollama':
            return self._get_ollama_response(system_prompt, context, user_input, temperature)
        
        return self._fallback_jsonb_analysis(user_input, None)
    
    def _build_jsonb_system_prompt(self, analysis):
        """Build system prompt for JSONB analysis"""
        expertise_guidance = {
            'expert': "Provide advanced technical details with specific PostgreSQL internals. Use technical terminology appropriately.",
            'intermediate': "Provide detailed explanations with good technical depth. Explain complex concepts clearly.",
            'beginner': "Provide clear, step-by-step explanations. Define technical terms and focus on practical solutions."
        }
        
        urgency_guidance = {
            'critical': "CRITICAL PRODUCTION ISSUE: Prioritize immediate fixes and emergency procedures. Provide quick wins first.",
            'high': "HIGH PRIORITY: Focus on immediate actionable solutions. Provide quick diagnostic steps.",
            'medium': "Provide comprehensive analysis with both immediate and long-term solutions.",
            'low': "Provide thorough analysis with optimization strategies and best practices."
        }
        
        return f"""You are DB-Buddy, an expert PostgreSQL database consultant specializing in JSONB and TOAST performance optimization.

RESPONSE STYLE:
- Be conversational and practical like a senior DBA colleague
- Start with acknowledgment and root cause explanation
- Use the user's EXACT table names, column names, and metrics
- Provide specific, actionable solutions with expected performance improvements
- Include actual SQL commands using their schema and table names

USER CONTEXT:
- Technical Level: {analysis['technical_depth']} - {expertise_guidance[analysis['technical_depth']]}
- Urgency: {analysis['urgency_level']} - {urgency_guidance[analysis['urgency_level']]}

REQUIREMENTS:
1. Analyze their specific JSONB/TOAST performance issue
2. Use their exact table names and column names in all examples
3. Reference their specific performance metrics (table size, TOAST size, execution times)
4. Provide 3-4 ranked solutions with expected performance improvements
5. Include specific SQL commands they can execute
6. Explain WHY the issue occurs in simple terms
7. Give realistic performance improvement estimates

Focus on practical, implementable solutions using their specific environment details."""
    
    def _get_groq_jsonb_response(self, system_prompt, context, user_input, temperature):
        """Get Groq AI response for JSONB analysis"""
        try:
            headers = {
                'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'llama3-8b-8192',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"{context}\n\nUser's specific situation:\n{user_input}\n\nProvide personalized JSONB/TOAST performance analysis and optimization recommendations using their exact table names, column names, and performance metrics."}
                ],
                'temperature': temperature,
                'max_tokens': 1500,
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
            print(f"Groq API error: {e}")
        
        return None
    
    def _get_huggingface_response(self, system_prompt, context, user_input):
        """Get Hugging Face response for JSONB analysis"""
        try:
            prompt = f"{system_prompt}\n\n{context}\n\nUser situation: {user_input}\n\nProvide personalized JSONB performance analysis:"
            
            headers = {
                'Authorization': f'Bearer {os.getenv("HUGGINGFACE_API_KEY")}',
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
        except Exception as e:
            print(f"Hugging Face API error: {e}")
        
        return None
    
    def _get_ollama_response(self, system_prompt, context, user_input, temperature):
        """Get Ollama response for JSONB analysis"""
        try:
            prompt = f"{system_prompt}\n\n{context}\n\nUser situation: {user_input}\n\nProvide personalized JSONB performance analysis:"
            
            response = requests.post('http://localhost:11434/api/generate',
                json={
                    'model': 'llama3.2:3b',
                    'prompt': prompt,
                    'stream': False,
                    'options': {'temperature': temperature, 'num_predict': 800}
                }, timeout=45)
            
            if response.status_code == 200:
                return response.json().get('response', '').strip()
        except Exception as e:
            print(f"Ollama API error: {e}")
        
        return None
    
    def _fallback_jsonb_analysis(self, user_input, user_selections):
        """Fallback analysis when AI is not available"""
        return """🔍 **JSONB/TOAST Performance Analysis**

**Issue Detected**: Large JSONB columns causing TOAST table bloat and slow query performance.

**Root Cause**: PostgreSQL stores large JSONB data in TOAST (The Oversized-Attribute Storage Technique) tables. When querying JSONB columns, PostgreSQL must retrieve and decompress this data from the TOAST table, causing significant performance overhead.

**Immediate Solutions**:

1. **Query Optimization**:
   - Avoid selecting JSONB columns unless necessary
   - Use specific JSONB key extraction instead of full objects
   - Split queries to separate JSONB retrieval from filtering

2. **Indexing Strategy**:
   - Create GIN indexes on frequently queried JSONB paths
   - Use functional indexes for specific JSONB key extractions

3. **Schema Optimization**:
   - Consider moving JSONB columns to separate tables
   - Extract frequently used JSONB keys to regular columns
   - Implement JSONB compression strategies

**Expected Performance Improvements**:
- Query splitting: 60-90% improvement
- Proper indexing: 70-85% improvement
- Schema optimization: 80-95% improvement

**Next Steps**: Share your specific table schema and query patterns for targeted optimization recommendations."""

    def generate_execution_time_analysis(self, user_input, user_selections):
        """Dynamic analysis of execution time discrepancies"""
        if not self.use_ai:
            return self._fallback_execution_analysis(user_input)
        
        analysis = self._extract_execution_details(user_input)
        context = self._build_execution_context(analysis, user_selections)
        
        return self._generate_execution_response(context, user_input, analysis)
    
    def _extract_execution_details(self, user_input):
        """Extract execution time details from user input"""
        return {
            'estimated_time': self._extract_estimated_time(user_input),
            'actual_time': self._extract_actual_time(user_input),
            'query_complexity': self._assess_query_complexity(user_input),
            'operations': self._extract_operations(user_input),
            'table_names': self._extract_table_names(user_input),
            'urgency_level': self._assess_urgency(user_input),
            'technical_depth': self._assess_technical_depth(user_input)
        }
    
    def _extract_estimated_time(self, text):
        """Extract estimated execution time"""
        patterns = [
            r'(\d+(?:\.\d+)?)\s*ms.*?estimated',
            r'estimated.*?(\d+(?:\.\d+)?)\s*ms',
            r'plan.*?(\d+(?:\.\d+)?)\s*ms'
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return f"{match.group(1)}ms"
        return "Unknown"
    
    def _extract_actual_time(self, text):
        """Extract actual execution time"""
        patterns = [
            r'(\d+(?:\.\d+)?)\s*s.*?actual',
            r'actual.*?(\d+(?:\.\d+)?)\s*s',
            r'taking.*?(\d+(?:\.\d+)?)\s*s'
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return f"{match.group(1)}s"
        return "Unknown"
    
    def _assess_query_complexity(self, text):
        """Assess query complexity based on operations"""
        complex_operations = ['json_build_object', 'array_agg', 'window function', 'nested query', 'subquery']
        complexity_score = sum(1 for op in complex_operations if op in text.lower())
        
        if complexity_score >= 3:
            return 'high'
        elif complexity_score >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _extract_operations(self, text):
        """Extract SQL operations from text"""
        operations = []
        operation_patterns = {
            'json_aggregation': ['json_build_object', 'array_agg'],
            'window_functions': ['count() over', 'max() over', 'row_number()'],
            'joins': ['join', 'left join', 'inner join'],
            'subqueries': ['select.*select', 'nested', 'subquery']
        }
        
        text_lower = text.lower()
        for op_type, keywords in operation_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                operations.append(op_type)
        
        return operations
    
    def _build_execution_context(self, analysis, user_selections):
        """Build context for execution time analysis"""
        return f"""Execution Time Discrepancy Analysis Context:

PERFORMANCE METRICS:
- Estimated Time: {analysis['estimated_time']}
- Actual Time: {analysis['actual_time']}
- Query Complexity: {analysis['query_complexity']}
- Operations: {', '.join(analysis['operations'])}
- Table Names: {', '.join(analysis['table_names'])}

USER PROFILE:
- Technical Level: {analysis['technical_depth']}
- Urgency: {analysis['urgency_level']}

ENVIRONMENT:
{json.dumps(user_selections, indent=2) if user_selections else 'No environment details'}

ANALYSIS FOCUS:
1. Explain the root cause of the time discrepancy
2. Use specific table names and operations from user input
3. Provide ranked solutions with performance impact estimates
4. Include specific SQL commands for their environment
"""
    
    def _generate_execution_response(self, context, user_input, analysis):
        """Generate dynamic response for execution time analysis"""
        temperature = self.temperature_settings[analysis['urgency_level']]
        system_prompt = self._build_execution_system_prompt(analysis)
        
        if self.use_ai == 'groq':
            return self._get_groq_execution_response(system_prompt, context, user_input, temperature)
        
        return self._fallback_execution_analysis(user_input)
    
    def _build_execution_system_prompt(self, analysis):
        """Build system prompt for execution time analysis"""
        return f"""You are DB-Buddy, a PostgreSQL performance expert specializing in execution plan analysis and query optimization.

RESPONSE REQUIREMENTS:
- Explain WHY there's a {analysis['estimated_time']} vs {analysis['actual_time']} discrepancy
- Use the user's exact table names and operations in all examples
- Provide specific, actionable solutions ranked by impact
- Include realistic performance improvement estimates
- Focus on {analysis['query_complexity']} complexity query optimization

USER CONTEXT:
- Technical Level: {analysis['technical_depth']}
- Urgency: {analysis['urgency_level']}
- Query Operations: {', '.join(analysis['operations'])}

Be conversational, practical, and provide immediate actionable solutions."""
    
    def _get_groq_execution_response(self, system_prompt, context, user_input, temperature):
        """Get Groq response for execution time analysis"""
        try:
            headers = {
                'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'llama3-8b-8192',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"{context}\n\nUser's execution time issue:\n{user_input}\n\nProvide personalized analysis of the execution time discrepancy with specific solutions."}
                ],
                'temperature': temperature,
                'max_tokens': 1200,
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
            print(f"Groq API error: {e}")
        
        return None
    
    def _fallback_execution_analysis(self, user_input):
        """Fallback execution time analysis"""
        return """🔍 **Execution Time Discrepancy Analysis**

**Issue**: Significant gap between estimated and actual execution times indicates PostgreSQL's query planner underestimated the actual cost.

**Common Causes**:
1. **JSON Processing Overhead**: Planner doesn't account for JSON serialization costs
2. **Window Function Costs**: Sorting and partitioning overhead underestimated
3. **Nested Query Complexity**: Materialization costs not properly calculated
4. **Resource Contention**: System load not reflected in planning

**Immediate Solutions**:
1. Update table statistics: `ANALYZE table_name;`
2. Remove redundant conditions and NULL checks
3. Optimize date filtering to use indexes
4. Add LIMIT clauses to prevent runaway queries

**Expected Improvements**: 60-95% performance improvement with proper optimization."""