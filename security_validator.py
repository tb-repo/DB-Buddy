"""
OWASP LLM Top 10 Security Validator
Comprehensive security measures for AI chatbot applications
"""
import re
import time
import hashlib
from typing import Dict, List, Tuple, Optional
import logging

class LLMSecurityValidator:
    def __init__(self):
        # Rate limiting and consumption control
        self.user_sessions = {}
        self.max_requests_per_minute = 10
        self.max_tokens_per_request = 4000
        self.max_daily_tokens = 50000
        
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
        
        # System prompt leakage patterns
        self.system_prompt_patterns = [
            r'what\s+are\s+your\s+instructions',
            r'show\s+me\s+your\s+prompt',
            r'what\s+is\s+your\s+system\s+prompt',
            r'reveal\s+your\s+instructions',
            r'display\s+your\s+guidelines',
            r'print\s+your\s+system\s+message'
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
            return False, "🔒 Security: System information requests not allowed"
        
        # 4. Unbounded Consumption Control
        if not self._check_rate_limits(user_input, user_id):
            return False, "⏱️ Rate limit exceeded. Please wait before sending more requests"
        
        # 5. Topic Validation (Excessive Agency Prevention)
        if not self._validate_topic_scope(user_input):
            return False, "📋 Scope: Please limit requests to database-related topics only"
        
        return True, None
    
    def validate_output(self, ai_output: str) -> str:
        """Validate and sanitize AI output"""
        
        # Remove any potential sensitive information from output
        sanitized = ai_output
        for pattern, info_type in self.sensitive_patterns:
            sanitized = re.sub(pattern, f"[{info_type} REDACTED]", sanitized, flags=re.IGNORECASE)
        
        # Add misinformation disclaimer for uncertain statements
        if self._contains_misinformation_risk(sanitized):
            sanitized += "\n\n⚠️ **Disclaimer**: Verify all recommendations in a test environment before production use."
        
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
        
        # Update counters
        session['requests'].append(current_time)
        session['daily_tokens'] += estimated_tokens
        
        return True
    
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
    
    def log_security_event(self, event_type: str, user_id: str, details: str):
        """Log security events for monitoring"""
        logging.warning(f"SECURITY_EVENT: {event_type} | User: {user_id} | Details: {details}")