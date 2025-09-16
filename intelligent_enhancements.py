"""
Advanced Intelligence Enhancements for DB-Buddy
Provides context analysis, response quality validation, and intelligent fallbacks
"""

import re
import json
from datetime import datetime

class IntelligentEnhancements:
    def __init__(self):
        self.context_cache = {}
        self.response_quality_threshold = 0.7
        
    def analyze_context_depth(self, user_input, user_selections, conversation_context):
        """Advanced analysis of user input and context for intelligent responses"""
        analysis = {
            'technical_depth': self.assess_technical_depth(user_input),
            'urgency_level': self.assess_urgency_advanced(user_input),
            'specificity_score': self.calculate_specificity_score(user_input),
            'domain_expertise': self.detect_domain_expertise(user_input),
            'query_complexity': self.analyze_query_complexity(user_input),
            'context_completeness': self.assess_context_completeness(user_selections),
            'response_type_needed': self.determine_response_type(user_input),
            'key_entities': self.extract_key_entities(user_input),
            'performance_indicators': self.detect_performance_indicators(user_input)
        }
        return analysis
    
    def assess_technical_depth(self, text):
        """Assess the technical depth of user input"""
        expert_indicators = [
            'execution plan', 'query optimizer', 'buffer pool', 'statistics', 'cardinality',
            'cost-based optimizer', 'partitioning', 'sharding', 'replication lag', 'wal',
            'checkpoint', 'vacuum', 'analyze', 'explain analyze', 'pg_stat_', 'innodb',
            'transaction isolation', 'deadlock', 'lock escalation', 'index fragmentation'
        ]
        
        intermediate_indicators = [
            'index', 'join', 'where clause', 'primary key', 'foreign key', 'normalization',
            'sql query', 'database design', 'performance', 'optimization', 'backup',
            'restore', 'connection pool', 'timeout', 'slow query'
        ]
        
        text_lower = text.lower()
        expert_count = sum(1 for indicator in expert_indicators if indicator in text_lower)
        intermediate_count = sum(1 for indicator in intermediate_indicators if indicator in text_lower)
        
        if expert_count >= 2:
            return 'expert'
        elif expert_count >= 1 or intermediate_count >= 3:
            return 'intermediate'
        elif intermediate_count >= 1:
            return 'beginner_plus'
        else:
            return 'beginner'
    
    def assess_urgency_advanced(self, text):
        """Advanced urgency assessment with context"""
        critical_indicators = ['production down', 'outage', 'critical error', 'emergency', 'urgent']
        high_indicators = ['production', 'timeout', 'failed', 'error', 'crash', 'corruption']
        medium_indicators = ['slow', 'performance', 'issue', 'problem', 'concern']
        
        text_lower = text.lower()
        
        if any(indicator in text_lower for indicator in critical_indicators):
            return 'critical'
        elif any(indicator in text_lower for indicator in high_indicators):
            return 'high'
        elif any(indicator in text_lower for indicator in medium_indicators):
            return 'medium'
        else:
            return 'low'
    
    def calculate_specificity_score(self, text):
        """Calculate how specific the user's request is"""
        score = 0
        text_lower = text.lower()
        
        # Check for SQL queries
        if any(sql in text_lower for sql in ['select ', 'insert ', 'update ', 'delete ']):
            score += 30
        
        # Check for specific numbers/metrics
        if re.search(r'\d+\s*(ms|seconds?|minutes?|gb|mb|tb|%)', text_lower):
            score += 20
        
        # Check for specific error messages
        if 'error' in text_lower and len(text) > 100:
            score += 15
        
        # Check for table/column references
        if re.search(r'\b\w+\.\w+', text):
            score += 10
        
        # Length and detail bonus
        if len(text) > 200:
            score += 10
        
        return min(score, 100)  # Cap at 100
    
    def detect_domain_expertise(self, text):
        """Detect specific database domain expertise"""
        domains = {
            'performance_tuning': ['optimization', 'tuning', 'performance', 'bottleneck', 'latency'],
            'query_optimization': ['query', 'sql', 'execution plan', 'index', 'join'],
            'database_administration': ['backup', 'restore', 'maintenance', 'monitoring', 'configuration'],
            'architecture_design': ['schema', 'design', 'normalization', 'partitioning', 'scaling'],
            'troubleshooting': ['error', 'issue', 'problem', 'debug', 'diagnose'],
            'security': ['security', 'permissions', 'authentication', 'encryption', 'audit']
        }
        
        text_lower = text.lower()
        detected_domains = []
        
        for domain, keywords in domains.items():
            if sum(1 for keyword in keywords if keyword in text_lower) >= 2:
                detected_domains.append(domain)
        
        return detected_domains
    
    def analyze_query_complexity(self, text):
        """Analyze SQL query complexity if present"""
        if not any(sql in text.lower() for sql in ['select', 'insert', 'update', 'delete']):
            return 'no_sql'
        
        complexity_indicators = {
            'simple': ['select', 'from', 'where'],
            'medium': ['join', 'group by', 'order by', 'having'],
            'complex': ['subquery', 'union', 'window function', 'cte', 'with']
        }
        
        text_lower = text.lower()
        
        if any(indicator in text_lower for indicator in complexity_indicators['complex']):
            return 'complex'
        elif any(indicator in text_lower for indicator in complexity_indicators['medium']):
            return 'medium'
        elif any(indicator in text_lower for indicator in complexity_indicators['simple']):
            return 'simple'
        
        return 'unknown'
    
    def assess_context_completeness(self, user_selections):
        """Assess how complete the user's context information is"""
        if not user_selections:
            return 0
        
        important_fields = ['deployment', 'database', 'environment']
        provided_fields = sum(1 for field in important_fields if user_selections.get(field))
        
        return (provided_fields / len(important_fields)) * 100
    
    def determine_response_type(self, text):
        """Determine what type of response is needed"""
        text_lower = text.lower()
        
        if any(sql in text_lower for sql in ['select ', 'insert ', 'update ', 'delete ', 'create ']):
            return 'sql_analysis'
        elif any(plan in text_lower for plan in ['execution plan', 'explain', 'query plan']):
            return 'execution_plan_analysis'
        elif any(error in text_lower for error in ['error', 'exception', 'failed', 'crash']):
            return 'troubleshooting'
        elif any(perf in text_lower for perf in ['slow', 'performance', 'optimization']):
            return 'performance_optimization'
        elif any(arch in text_lower for arch in ['design', 'architecture', 'schema']):
            return 'architecture_guidance'
        else:
            return 'general_consultation'
    
    def extract_key_entities(self, text):
        """Extract key technical entities from text"""
        entities = []
        
        # Extract table names (simple heuristic)
        table_patterns = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*', text)
        entities.extend([match.split('.')[0] for match in table_patterns])
        
        # Extract database systems
        db_systems = ['postgresql', 'mysql', 'oracle', 'sql server', 'mongodb', 'aurora', 'rds']
        for db in db_systems:
            if db in text.lower():
                entities.append(db)
        
        # Extract cloud providers
        cloud_providers = ['aws', 'azure', 'gcp', 'google cloud']
        for cloud in cloud_providers:
            if cloud in text.lower():
                entities.append(cloud)
        
        return list(set(entities))
    
    def detect_performance_indicators(self, text):
        """Detect performance-related indicators in text"""
        indicators = []
        text_lower = text.lower()
        
        # Time indicators
        if re.search(r'\d+\s*(ms|milliseconds?|seconds?|minutes?)', text_lower):
            indicators.append('execution_time')
        
        # Resource indicators
        if re.search(r'\d+\s*(gb|mb|tb|%)', text_lower):
            indicators.append('resource_usage')
        
        # Performance keywords
        perf_keywords = {
            'slow_query': ['slow', 'timeout', 'long running'],
            'high_cpu': ['cpu', 'processor', 'high load'],
            'memory_issue': ['memory', 'ram', 'out of memory'],
            'io_bottleneck': ['disk', 'i/o', 'storage'],
            'connection_issue': ['connection', 'pool', 'timeout']
        }
        
        for indicator, keywords in perf_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                indicators.append(indicator)
        
        return indicators
    
    def validate_response_quality(self, response, analysis):
        """Validate if the AI response meets quality standards"""
        if not response or len(response.strip()) < 50:
            return False
        
        # Check for generic responses (quality issue)
        generic_phrases = [
            "I see you have", "Please share your", "I can help with", 
            "Let me know if", "Feel free to", "I'd be happy to"
        ]
        
        if any(phrase in response for phrase in generic_phrases) and analysis['specificity_score'] > 50:
            return False
        
        # Check if response addresses the specific domain
        if analysis['domain_expertise']:
            domain_keywords = {
                'query_optimization': ['query', 'index', 'optimization', 'execution'],
                'troubleshooting': ['diagnostic', 'troubleshoot', 'error', 'issue'],
                'performance_tuning': ['performance', 'optimization', 'tuning', 'bottleneck']
            }
            
            for domain in analysis['domain_expertise']:
                if domain in domain_keywords:
                    if not any(keyword in response.lower() for keyword in domain_keywords[domain]):
                        return False
        
        return True
    
    def enhance_response_quality(self, response, analysis, user_selections):
        """Post-process response to enhance quality and completeness"""
        enhanced_response = response
        
        # Add urgency indicators for high-priority issues
        if analysis['urgency_level'] in ['critical', 'high']:
            if not any(indicator in response for indicator in ['🚨', '⚠️', 'URGENT', 'CRITICAL']):
                enhanced_response = f"🚨 **{analysis['urgency_level'].upper()} PRIORITY** 🚨\n\n{enhanced_response}"
        
        # Add deployment-specific recommendations if missing
        if user_selections and not self.has_deployment_guidance(response, user_selections):
            deployment_guidance = self.get_deployment_context(user_selections)
            enhanced_response += f"\n\n{deployment_guidance}"
        
        # Add next steps if missing for high-specificity requests
        if analysis['specificity_score'] > 60 and 'next steps' not in response.lower():
            enhanced_response += "\n\n📋 **Next Steps:**\n1. Implement the recommended changes in a test environment first\n2. Monitor performance metrics before and after changes\n3. Validate improvements and adjust as needed"
        
        return enhanced_response
    
    def get_deployment_context(self, user_selections):
        """Get deployment-specific context and recommendations"""
        if not user_selections:
            return ""
        
        deployment = user_selections.get('deployment', '')
        cloud_provider = user_selections.get('cloud_provider', '')
        database = user_selections.get('database', '')
        
        context = "\n\n🏗️ **DEPLOYMENT-SPECIFIC RECOMMENDATIONS:**\n"
        
        if deployment == 'Cloud' and 'AWS' in cloud_provider:
            if 'Aurora' in database:
                context += "\n**AWS Aurora Optimizations:**\n"
                context += "- Use Aurora Performance Insights for query analysis\n"
                context += "- Leverage Aurora Auto Scaling for read replicas\n"
                context += "- Consider Aurora Serverless v2 for variable workloads\n"
                context += "- Use RDS Proxy for connection pooling and failover\n"
        
        return context
    
    def has_deployment_guidance(self, response, user_selections):
        """Check if response already contains deployment-specific guidance"""
        if not user_selections:
            return True
        
        cloud_provider = user_selections.get('cloud_provider', '').lower()
        return cloud_provider in response.lower() if cloud_provider else True
    
    def get_intelligent_fallback(self, user_input, user_selections, analysis):
        """Intelligent fallback based on context analysis"""
        fallback_type = analysis['response_type_needed']
        urgency = analysis['urgency_level']
        
        urgency_prefix = "🚨 **URGENT** - " if urgency in ['critical', 'high'] else ""
        
        fallbacks = {
            'sql_analysis': f"{urgency_prefix}I can analyze your SQL query. Please share the complete query and describe the performance issue.",
            'execution_plan_analysis': f"{urgency_prefix}I can interpret your execution plan. Please share the complete plan output.",
            'troubleshooting': f"{urgency_prefix}I can help troubleshoot your database issue. Please share the exact error message and system details.",
            'performance_optimization': f"{urgency_prefix}I can help optimize performance. Please describe the symptoms and share any available metrics.",
            'architecture_guidance': "I can help with database architecture design. Please describe your requirements and constraints.",
            'general_consultation': "I'm here to help with your database needs. Please provide more specific details about your situation."
        }
        
        return fallbacks.get(fallback_type, fallbacks['general_consultation'])