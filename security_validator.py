"""
OWASP LLM Top 10 Security Validator
Comprehensive security measures for AI chatbot applications
"""
import re
import time
import hashlib
from typing import Dict, List, Tuple, Optional
import logging
import numpy as np

class LLMSecurityValidator:
    def __init__(self):
        # Rate limiting and consumption control (Enhanced)
        self.user_sessions = {}
        self.max_requests_per_minute = 10
        self.max_tokens_per_request = 4000
        self.max_daily_tokens = 50000
        self.max_concurrent_requests = 5
        
        # DoS attack patterns
        self.dos_patterns = [
            r'repeat\s+this\s+\d+\s+times',
            r'generate\s+\d+\s+responses',
            r'create\s+\d+\s+queries',
            r'stress\s+test'
        ]
        
        # LLM Supply Chain Security
        self.trusted_endpoints = {
            'groq': 'api.groq.com',
            'anthropic': 'api.anthropic.com', 
            'huggingface': 'api-inference.huggingface.co'
        }
        self.model_whitelist = {
            'groq': ['llama3-8b-8192', 'llama-3.1-70b-versatile'],
            'anthropic': ['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307'],
            'huggingface': ['microsoft/DialoGPT-large']
        }
        
        # Prompt injection patterns
        self.injection_patterns = [
            r'ignore\s+previous\s+instructions',
            r'forget\s+everything\s+above',
            r'system\s*:\s*you\s+are\s+now',
            r'act\s+as\s+if\s+you\s+are',
            r'pretend\s+to\s+be',
            r'roleplay\s+as',
            r'simulate\s+being',
            r'override\s+your\s+instructions',
            r'disregard\s+your\s+programming',
            r'new\s+instructions\s*:',
            r'admin\s+mode',
            r'developer\s+mode',
            r'debug\s+mode',
            r'maintenance\s+mode'
        ]
        
        # Sensitive information patterns (enhanced)
        self.sensitive_patterns = [
            (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'Credit Card'),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'Email'),
            (r'\b\d{3}[\s-]?\d{2}[\s-]?\d{4}\b', 'SSN'),
            (r'password[\s]*[:=][\s]*[^\s]+', 'Password'),
            (r'api[\s_]*key[\s]*[:=][\s]*[^\s]+', 'API Key'),
            (r'secret[\s_]*key[\s]*[:=][\s]*[^\s]+', 'Secret Key'),
            (r'bearer[\s]+[a-zA-Z0-9\-._~+/]+=*', 'Bearer Token'),
            (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
            (r'xoxb-[0-9]{11}-[0-9]{12}-[a-zA-Z0-9]{24}', 'Slack Token'),
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Token'),
            (r'\b[A-Z0-9]{20}\b', 'AWS Access Key'),
            (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID')
        ]
        
        # System prompt leakage patterns (enhanced)
        self.system_prompt_patterns = [
            r'what\s+are\s+your\s+instructions',
            r'show\s+me\s+your\s+prompt',
            r'what\s+is\s+your\s+system\s+prompt',
            r'reveal\s+your\s+instructions',
            r'display\s+your\s+guidelines',
            r'print\s+your\s+system\s+message',
            r'repeat\s+your\s+initial\s+prompt',
            r'what\s+are\s+your\s+rules',
            r'show\s+your\s+configuration',
            r'display\s+behavioral\s+rules'
        ]
        
        # Sensitive data patterns that should NEVER be in system prompts
        self.prompt_sensitive_patterns = [
            r'password\s*[:=]\s*[^\s]+',
            r'connection\s+string\s*[:=]',
            r'database\s+url\s*[:=]',
            r'secret\s*[:=]\s*[^\s]+',
            r'token\s*[:=]\s*[^\s]+'
        ]
        
        # Misinformation indicators
        self.misinformation_patterns = [
            r'always\s+true\s+that',
            r'never\s+false\s+that',
            r'100%\s+certain',
            r'absolutely\s+guaranteed',
            r'medical\s+advice',
            r'financial\s+advice',
            r'legal\s+advice'
        ]
        
        # Database-specific allowed topics
        self.allowed_topics = [
            'database', 'sql', 'query', 'performance', 'optimization',
            'index', 'table', 'schema', 'postgresql', 'mysql', 'oracle',
            'mongodb', 'redis', 'troubleshooting', 'backup', 'restore',
            'replication', 'clustering', 'scaling', 'capacity', 'security'
        ]
        
        # Supply chain integrity patterns
        self.malicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'eval\s*\(',
            r'exec\s*\(',
            r'import\s+os',
            r'subprocess\.',
            r'__import__'
        ]
        
        # Training data poisoning indicators
        self.bias_indicators = [
            r'always\s+(men|women|male|female)\s+are',
            r'never\s+trust\s+(people|users)\s+from',
            r'all\s+(database|system)\s+administrators\s+should',
            r'(delete|drop|truncate)\s+all\s+data',
            r'grant\s+all\s+privileges\s+to\s+everyone',
            r'always\s+(true|false|works|fails)',
            r'100%\s+certain',
            r'absolutely\s+guaranteed',
            r'guaranteed\s+to\s+work',
            r'will\s+definitely\s+fix',
            r'impossible\s+to\s+fail'
        ]
        
        # Response quality baselines
        self.response_quality_thresholds = {
            'min_length': 50,
            'max_length': 5000,
            'database_relevance_required': True
        }
        
        # Output usage tracking for anomaly detection
        self.output_usage_log = []
        self.max_outputs_per_minute = 15
        
        # Excessive Agency Control
        self.allowed_operations = {
            'read_only': ['SELECT', 'EXPLAIN', 'SHOW', 'DESCRIBE'],
            'safe_admin': ['CREATE INDEX CONCURRENTLY', 'ANALYZE', 'VACUUM'],
            'restricted': ['CREATE', 'ALTER', 'UPDATE', 'INSERT'],
            'forbidden': ['DROP', 'DELETE', 'TRUNCATE', 'GRANT ALL', 'REVOKE', 'SHUTDOWN']
        }
        
        # Vector and Embedding Security (OWASP LLM #11)
        self.vector_security_patterns = [
            r'vector\s+injection',
            r'embedding\s+manipulation',
            r'similarity\s+spoofing',
            r'retrieval\s+poisoning',
            r'context\s+contamination',
            r'adversarial\s+embedding'
        ]
        
        self.escalation_triggers = [
            r'DROP\s+(DATABASE|TABLE|INDEX)',
            r'DELETE\s+FROM.*WHERE\s+1\s*=\s*1',
            r'TRUNCATE\s+TABLE',
            r'GRANT\s+ALL\s+PRIVILEGES',
            r'ALTER\s+USER.*SUPERUSER',
            r'SHUTDOWN',
            r'KILL\s+CONNECTION'
        ]
        
        # Supply chain integrity patterns
        self.malicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'eval\s*\(',
            r'exec\s*\(',
            r'import\s+os',
            r'subprocess\.',
            r'__import__'
        ]
        
        # RAG and Vector Database Security
        self.rag_security_config = {
            'max_context_length': 8000,
            'max_retrieved_documents': 10,
            'similarity_threshold_min': 0.1,
            'similarity_threshold_max': 0.99
        }
    
    def validate_input(self, user_input: str, user_id: str = "default") -> Tuple[bool, Optional[str]]:
        """Comprehensive input validation against all security risks"""
        
        # 1. Prompt Injection Detection
        if self._detect_prompt_injection(user_input):
            return False, "🚨 Security Alert: Prompt injection attempt detected"
        
        # 2. Sensitive Information Disclosure
        sensitive_type = self._detect_sensitive_info(user_input)
        if sensitive_type:
            return False, f"🛡️ IDP Policy: {sensitive_type} detected. Remove sensitive information"
        
        # 3. System Prompt Leakage Attempt
        if self._detect_system_prompt_leakage(user_input):
            self.log_security_event("SYSTEM_PROMPT_LEAKAGE_ATTEMPT", user_id, user_input[:100])
            return False, "🔒 Security: System information requests not allowed"
        
        # 4. Unbounded Consumption Control
        if not self._check_rate_limits(user_input, user_id):
            return False, "⏱️ Rate limit exceeded. Please wait before sending more requests"
        
        # 5. Topic Validation (Excessive Agency Prevention)
        if not self._validate_topic_scope(user_input):
            return False, "📋 Scope: Please limit requests to database-related topics only"
        
        # 6. Vector and Embedding Security Validation
        if self._detect_vector_attacks(user_input):
            return False, "🚨 Vector Security: RAG manipulation attempt detected"
        
        return True, None
    
    def validate_output(self, ai_output: str) -> str:
        """Validate and sanitize AI output"""
        
        # Supply chain integrity check
        if not self._validate_model_output_integrity(ai_output):
            return "🚨 **Security Alert**: Response blocked due to potential supply chain compromise. Please try again."
        
        # Output handling security validation
        if not self._validate_output_security(ai_output):
            return "🚨 **Security Alert**: Response blocked due to improper output handling risks. Please try again."
        
        # Excessive Agency validation
        agency_result = self._validate_agency_boundaries(ai_output)
        if not agency_result['allowed']:
            return f"🚨 **Agency Control**: {agency_result['reason']}. Escalate to DBA team for: {', '.join(agency_result['violations'])}"
        
        # Context-aware output encoding
        sanitized = self._encode_output_for_context(ai_output)
        
        # Remove any potential sensitive information from output
        for pattern, info_type in self.sensitive_patterns:
            sanitized = re.sub(pattern, f"[{info_type} REDACTED]", sanitized, flags=re.IGNORECASE)
        
        # Add agency warnings if needed
        if agency_result.get('warnings'):
            sanitized += f"\n\n⚠️ **Agency Warning**: {agency_result['warnings']}"
        
        # Add misinformation disclaimer for uncertain statements
        if self._contains_misinformation_risk(sanitized):
            sanitized += "\n\n⚠️ **Disclaimer**: Verify all recommendations in a test environment before production use."
        
        # Add overreliance warning for database recommendations
        if re.search(r'recommend|suggest|should|will\s+fix', sanitized, re.IGNORECASE):
            sanitized += "\n\n💡 **AI Limitation Notice**: These recommendations are based on general patterns. Test thoroughly in your specific environment."
        
        # Add security footer
        sanitized += "\n\n🛡️ *Response validated for security compliance*"
        
        return sanitized
    
    def _detect_prompt_injection(self, text: str) -> bool:
        """Detect prompt injection attempts"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in self.injection_patterns)
    
    def _detect_sensitive_info(self, text: str) -> Optional[str]:
        """Detect sensitive information in input"""
        for pattern, info_type in self.sensitive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return info_type
        return None
    
    def _detect_system_prompt_leakage(self, text: str) -> bool:
        """Detect attempts to extract system prompts"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in self.system_prompt_patterns)
    
    def _check_rate_limits(self, text: str, user_id: str) -> bool:
        """Check rate limits and token consumption"""
        current_time = time.time()
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'requests': [],
                'daily_tokens': 0,
                'last_reset': current_time
            }
        
        session = self.user_sessions[user_id]
        
        # Reset daily counters
        if current_time - session['last_reset'] > 86400:  # 24 hours
            session['daily_tokens'] = 0
            session['last_reset'] = current_time
        
        # Remove old requests (older than 1 minute)
        session['requests'] = [req_time for req_time in session['requests'] 
                              if current_time - req_time < 60]
        
        # Check request rate limit
        if len(session['requests']) >= self.max_requests_per_minute:
            return False
        
        # Estimate token count (rough approximation)
        estimated_tokens = len(text.split()) * 1.3
        
        # Check token limits
        if estimated_tokens > self.max_tokens_per_request:
            return False
        
        if session['daily_tokens'] + estimated_tokens > self.max_daily_tokens:
            return False
        
        # Check for DoS patterns
        if self._detect_dos_patterns(text):
            self.log_security_event("DOS_PATTERN_DETECTED", user_id, text[:100])
            return False
        
        # Update counters
        session['requests'].append(current_time)
        session['daily_tokens'] += estimated_tokens
        
        return True
    
    def _detect_dos_patterns(self, text: str) -> bool:
        """Detect DoS attack patterns"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in self.dos_patterns)
    
    def _validate_topic_scope(self, text: str) -> bool:
        """Validate that request is within allowed database topics"""
        text_lower = text.lower()
        
        # Allow if contains database-related keywords
        if any(topic in text_lower for topic in self.allowed_topics):
            return True
        
        # Allow short conversational responses
        if len(text.strip()) < 20:
            return True
        
        # Reject off-topic requests
        off_topic_indicators = [
            'weather', 'politics', 'personal', 'relationship', 'medical',
            'legal advice', 'financial advice', 'investment', 'crypto',
            'write a story', 'poem', 'joke', 'recipe', 'travel'
        ]
        
        return not any(indicator in text_lower for indicator in off_topic_indicators)
    
    def _contains_misinformation_risk(self, text: str) -> bool:
        """Check if output contains potential misinformation patterns"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in self.misinformation_patterns)
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for HTTP responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    def validate_model_endpoint(self, provider: str, model: str, endpoint: str) -> bool:
        """Validate model and endpoint against whitelist"""
        if provider not in self.trusted_endpoints or provider not in self.model_whitelist:
            return False
        return (self.trusted_endpoints[provider] in endpoint and 
                model in self.model_whitelist[provider])
    
    def _validate_model_output_integrity(self, output: str) -> bool:
        """Check model output for supply chain compromise indicators"""
        # Check for malicious patterns
        for pattern in self.malicious_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                self.log_security_event("SUPPLY_CHAIN_COMPROMISE", "system", f"Malicious pattern: {pattern}")
                return False
        
        # Check for training data poisoning indicators
        for pattern in self.bias_indicators:
            if re.search(pattern, output, re.IGNORECASE):
                self.log_security_event("TRAINING_DATA_POISONING", "system", f"Bias indicator: {pattern}")
                return False
        
        # Basic quality checks
        if len(output) < self.response_quality_thresholds['min_length']:
            self.log_security_event("QUALITY_ANOMALY", "system", "Response too short")
            return False
            
        if len(output) > self.response_quality_thresholds['max_length']:
            self.log_security_event("QUALITY_ANOMALY", "system", "Response too long")
            return False
        
        return True
    
    def _validate_output_security(self, output: str) -> bool:
        """Validate output for improper handling vulnerabilities"""
        # Check for XSS/HTML injection
        xss_patterns = [r'<script', r'javascript:', r'onload=', r'onerror=', r'<iframe', r'<object', r'<embed']
        if any(re.search(pattern, output, re.IGNORECASE) for pattern in xss_patterns):
            self.log_security_event("OUTPUT_XSS_RISK", "system", "XSS pattern detected")
            return False
        
        # Check for SSRF/URL injection
        ssrf_patterns = [r'http://localhost', r'http://127\.', r'http://10\.', r'http://192\.168\.']
        if any(re.search(pattern, output, re.IGNORECASE) for pattern in ssrf_patterns):
            self.log_security_event("OUTPUT_SSRF_RISK", "system", "SSRF pattern detected")
            return False
        
        # Check for privilege escalation commands
        privilege_patterns = [r'GRANT\s+ALL', r'CREATE\s+USER', r'ALTER\s+USER.*SUPERUSER', r'DROP\s+DATABASE']
        if any(re.search(pattern, output, re.IGNORECASE) for pattern in privilege_patterns):
            self.log_security_event("OUTPUT_PRIVILEGE_RISK", "system", "Privilege escalation detected")
            return False
        
        return True
    
    def _encode_output_for_context(self, output: str) -> str:
        """Context-aware output encoding"""
        import html
        # Basic HTML encoding for web context
        encoded = html.escape(output)
        
        # Additional SQL injection prevention in code blocks
        encoded = re.sub(r'(```sql\s*\n)(.*?)(\n```)', 
                        lambda m: m.group(1) + self._sanitize_sql_block(m.group(2)) + m.group(3), 
                        encoded, flags=re.DOTALL)
        
        return encoded
    
    def _sanitize_sql_block(self, sql: str) -> str:
        """Sanitize SQL blocks to prevent injection and excessive agency"""
        sanitized = sql
        
        # Remove forbidden operations
        for op_list in [self.allowed_operations['forbidden'], self.escalation_triggers]:
            for cmd in op_list:
                if isinstance(cmd, str) and not cmd.startswith('r\''):
                    sanitized = re.sub(f'\\b{cmd}\\b', '[RESTRICTED_OPERATION]', sanitized, flags=re.IGNORECASE)
                else:
                    sanitized = re.sub(cmd, '[RESTRICTED_OPERATION]', sanitized, flags=re.IGNORECASE)
        
        # Add approval notice for restricted operations
        for op in self.allowed_operations['restricted']:
            if re.search(f'\\b{op}\\b', sanitized, re.IGNORECASE):
                sanitized += f'\n-- NOTE: {op} requires DBA approval in production'
        
        return sanitized
    
    def _validate_agency_boundaries(self, output: str) -> dict:
        """Validate output against excessive agency boundaries"""
        violations = []
        warnings = []
        
        # Check for forbidden operations
        for pattern in self.escalation_triggers:
            if re.search(pattern, output, re.IGNORECASE):
                violations.append(pattern)
        
        # Check for restricted operations that need approval
        restricted_found = []
        for op in self.allowed_operations['restricted']:
            if re.search(f'\\b{op}\\b', output, re.IGNORECASE):
                restricted_found.append(op)
        
        if violations:
            self.log_security_event("EXCESSIVE_AGENCY", "system", f"Forbidden operations: {violations}")
            return {
                'allowed': False,
                'reason': 'Forbidden database operations detected',
                'violations': violations
            }
        
        if restricted_found:
            warnings.append(f"Restricted operations require DBA approval: {', '.join(restricted_found)}")
        
        return {
            'allowed': True,
            'warnings': ' '.join(warnings) if warnings else None
        }
    
    def validate_system_prompt_security(self, system_prompt: str) -> dict:
        """Validate system prompt for sensitive information leakage"""
        issues = []
        
        # Check for sensitive data in system prompt
        for pattern in self.prompt_sensitive_patterns:
            if re.search(pattern, system_prompt, re.IGNORECASE):
                issues.append(f"Sensitive data pattern detected: {pattern}")
                self.log_security_event("SYSTEM_PROMPT_SENSITIVE_DATA", "system", pattern)
        
        # Check for overly detailed architecture information
        architecture_details = [
            r'database\s+type:\s+\w+',
            r'cloud\s+provider:\s+\w+', 
            r'environment:\s+\w+',
            r'internal\s+classification',
            r'priority\s+level:\s+\w+'
        ]
        
        for pattern in architecture_details:
            if re.search(pattern, system_prompt, re.IGNORECASE):
                issues.append(f"Architecture detail exposed: {pattern}")
        
        return {
            'secure': len(issues) == 0,
            'issues': issues,
            'recommendation': 'Remove sensitive data and detailed architecture info from system prompts'
        }
    
    def get_sanitized_system_prompt(self, base_prompt: str, user_context: dict = None) -> str:
        """Generate sanitized system prompt without sensitive details"""
        # Generic, secure system prompt without sensitive information
        sanitized_prompt = """You are a database operations assistant. Provide helpful database guidance while following security protocols. Focus on database-related topics only."""
        
        # Add minimal, non-sensitive context if needed
        if user_context and user_context.get('expertise_level'):
            expertise = user_context['expertise_level']
            if expertise == 'beginner':
                sanitized_prompt += " Provide detailed explanations."
            elif expertise == 'expert':
                sanitized_prompt += " Focus on advanced technical details."
        
        return sanitized_prompt
    
    def _detect_vector_attacks(self, text: str) -> bool:
        """Detect vector and embedding manipulation attempts"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in self.vector_security_patterns)
    
    def validate_rag_context(self, context: str, source: str = "retrieval") -> Tuple[bool, Optional[str]]:
        """Validate RAG context for security vulnerabilities"""
        
        # Check context length
        if len(context) > self.rag_security_config['max_context_length']:
            return False, f"RAG context too long: {len(context)} > {self.rag_security_config['max_context_length']}"
        
        # Check for context contamination
        for pattern in self.malicious_patterns:
            if re.search(pattern, context, re.IGNORECASE | re.DOTALL):
                self.log_security_event("RAG_CONTEXT_CONTAMINATION", source, f"Pattern: {pattern}")
                return False, "🚨 RAG Security: Context contamination detected"
        
        # Check for sensitive information in context
        for pattern, info_type in self.sensitive_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return False, f"🔒 RAG Privacy: {info_type} detected in context"
        
        return True, None
    
    def sanitize_rag_context(self, context: str) -> str:
        """Sanitize RAG context before use"""
        sanitized = context
        
        # Remove malicious patterns
        for pattern in self.malicious_patterns:
            sanitized = re.sub(pattern, '[SANITIZED]', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove sensitive information
        for pattern, info_type in self.sensitive_patterns:
            sanitized = re.sub(pattern, f'[{info_type} REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > self.rag_security_config['max_context_length']:
            sanitized = sanitized[:self.rag_security_config['max_context_length']] + "... [TRUNCATED]"
        
        return sanitized
    
    def validate_vector_similarity(self, similarity_score: float) -> bool:
        """Validate vector similarity scores for anomalies"""
        min_sim = self.rag_security_config['similarity_threshold_min']
        max_sim = self.rag_security_config['similarity_threshold_max']
        
        if similarity_score < min_sim or similarity_score > max_sim:
            self.log_security_event("VECTOR_SIMILARITY_ANOMALY", "system", f"Score: {similarity_score}")
            return False
        
        return True
    
    def log_security_event(self, event_type: str, user_id: str, details: str):
        """Log security events for monitoring"""
        logging.warning(f"SECURITY_EVENT: {event_type} | User: {user_id} | Details: {details}")