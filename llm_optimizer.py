"""
LLM Processing Optimizer for DB-Buddy
"""

class LLMOptimizer:
    
    @staticmethod
    def create_structured_prompt(query_analysis, user_context, performance_data):
        """Create structured prompt with clear sections"""
        return f"""You are a PostgreSQL performance expert. Analyze this EXACT query:

QUERY:
{query_analysis['sql_query']}

CONTEXT:
- Table: {query_analysis['table']}
- Environment: {user_context.get('environment', 'Unknown')}
- Current Performance: {performance_data.get('execution_time', 'Unknown')} seconds
- Expected Performance: {performance_data.get('plan_time', 'Unknown')} ms

ANALYSIS REQUIRED:
1. Root cause of performance gap
2. Specific index recommendations
3. Query optimization suggestions
4. Expected improvement percentages

FORMAT: Provide concrete, actionable recommendations with exact SQL commands."""

    @staticmethod
    def optimize_groq_parameters(query_complexity, urgency_level):
        """Optimize Groq API parameters based on context"""
        if urgency_level == 'high':
            return {
                'temperature': 0.05,  # More deterministic for urgent issues
                'max_tokens': 1000,
                'top_p': 0.8
            }
        elif query_complexity == 'high':
            return {
                'temperature': 0.1,   # Balanced for complex analysis
                'max_tokens': 1200,
                'top_p': 0.9
            }
        else:
            return {
                'temperature': 0.15,  # Slightly more creative for simple queries
                'max_tokens': 800,
                'top_p': 0.9
            }

    @staticmethod
    def create_few_shot_examples():
        """Few-shot examples for better LLM performance"""
        return """
EXAMPLE 1:
Query: SELECT * FROM large_table WHERE date_col > '2024-01-01'
Issue: 30 second execution
Solution: CREATE INDEX idx_date ON large_table(date_col); Expected: 2 seconds

EXAMPLE 2:
Query: SELECT jsonb_col FROM table WHERE id = 123
Issue: TOAST table access causing slowness
Solution: SELECT jsonb_col->>'specific_key' instead; Expected: 90% improvement
"""

    @staticmethod
    def validate_llm_response(response, expected_elements):
        """Validate LLM response quality"""
        quality_score = 0
        
        # Check for required elements
        if 'CREATE INDEX' in response: quality_score += 20
        if 'Expected:' in response or 'improvement' in response.lower(): quality_score += 20
        if 'Root cause' in response or 'bottleneck' in response.lower(): quality_score += 20
        if any(db_term in response.lower() for db_term in ['toast', 'jsonb', 'execution plan']): quality_score += 20
        if len(response) > 200: quality_score += 20  # Sufficient detail
        
        return quality_score >= 60  # 60% threshold for acceptable response