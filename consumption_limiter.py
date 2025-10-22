"""
Unbounded Consumption Protection
Prevents resource exhaustion and DoS attacks on LLM applications
"""
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging

class ConsumptionLimiter:
    def __init__(self):
        # Rate limiting per user/IP
        self.user_requests = defaultdict(list)
        self.ip_requests = defaultdict(list)
        
        # Token consumption tracking
        self.user_tokens = defaultdict(int)
        self.daily_token_reset = defaultdict(float)
        
        # Request complexity tracking
        self.complexity_cache = {}
        
        # Limits configuration
        self.limits = {
            'requests_per_minute': 10,
            'requests_per_hour': 100,
            'requests_per_day': 500,
            'tokens_per_request': 4000,
            'tokens_per_hour': 50000,
            'tokens_per_day': 200000,
            'max_concurrent_requests': 5,
            'max_input_length': 8000,
            'max_output_length': 2000,
            'complexity_threshold': 0.8
        }
        
        # Active request tracking
        self.active_requests = defaultdict(int)
        self.request_start_times = {}
        
        # Suspicious pattern detection
        self.suspicious_patterns = [
            r'repeat\s+this\s+\d+\s+times',
            r'generate\s+\d+\s+(queries|responses)',
            r'create\s+\d+\s+(tables|indexes)',
            r'loop\s+for\s+\d+\s+iterations',
            r'bulk\s+(insert|update|delete)',
            r'stress\s+test',
            r'benchmark\s+performance'
        ]
        
        # Model theft detection patterns
        self.theft_patterns = [
            r'what\s+are\s+your\s+training\s+parameters',
            r'how\s+were\s+you\s+trained',
            r'what\s+model\s+architecture',
            r'reproduce\s+your\s+responses',
            r'clone\s+your\s+behavior',
            r'extract\s+your\s+weights'
        ]
    
    def check_request_allowed(self, user_id: str, ip_address: str, 
                            input_text: str) -> Tuple[bool, Optional[str]]:
        """Check if request is allowed based on consumption limits"""
        current_time = time.time()
        
        # Check concurrent requests
        if self.active_requests[user_id] >= self.limits['max_concurrent_requests']:
            return False, f"Too many concurrent requests ({self.active_requests[user_id]})"
        
        # Check input length
        if len(input_text) > self.limits['max_input_length']:
            return False, f"Input too long ({len(input_text)} > {self.limits['max_input_length']})"
        
        # Check rate limits
        rate_check = self._check_rate_limits(user_id, ip_address, current_time)
        if not rate_check[0]:
            return rate_check
        
        # Check token consumption
        token_check = self._check_token_limits(user_id, input_text, current_time)
        if not token_check[0]:
            return token_check
        
        # Check for suspicious patterns
        if self._detect_suspicious_patterns(input_text):
            return False, "Suspicious consumption pattern detected"
        
        # Check for model theft attempts
        if self._detect_theft_attempts(input_text):
            return False, "Model extraction attempt detected"
        
        return True, None
    
    def start_request(self, user_id: str, request_id: str):
        """Track request start"""
        self.active_requests[user_id] += 1
        self.request_start_times[request_id] = time.time()
    
    def end_request(self, user_id: str, request_id: str, 
                   output_length: int = 0, tokens_used: int = 0):
        """Track request completion and resource usage"""
        self.active_requests[user_id] = max(0, self.active_requests[user_id] - 1)
        
        if request_id in self.request_start_times:
            duration = time.time() - self.request_start_times[request_id]
            del self.request_start_times[request_id]
            
            # Log long-running requests
            if duration > 30:  # 30 seconds
                logging.warning(f"Long request: {request_id} took {duration:.2f}s")
        
        # Track token usage
        if tokens_used > 0:
            self.user_tokens[user_id] += tokens_used
    
    def _check_rate_limits(self, user_id: str, ip_address: str, 
                          current_time: float) -> Tuple[bool, Optional[str]]:
        """Check rate limiting constraints"""
        # Clean old requests
        self._clean_old_requests(user_id, ip_address, current_time)
        
        # Check per-minute limit
        minute_requests = [t for t in self.user_requests[user_id] 
                          if current_time - t < 60]
        if len(minute_requests) >= self.limits['requests_per_minute']:
            return False, f"Rate limit exceeded: {len(minute_requests)} requests/minute"
        
        # Check per-hour limit
        hour_requests = [t for t in self.user_requests[user_id] 
                        if current_time - t < 3600]
        if len(hour_requests) >= self.limits['requests_per_hour']:
            return False, f"Hourly limit exceeded: {len(hour_requests)} requests/hour"
        
        # Check per-day limit
        day_requests = [t for t in self.user_requests[user_id] 
                       if current_time - t < 86400]
        if len(day_requests) >= self.limits['requests_per_day']:
            return False, f"Daily limit exceeded: {len(day_requests)} requests/day"
        
        # Record request
        self.user_requests[user_id].append(current_time)
        self.ip_requests[ip_address].append(current_time)
        
        return True, None
    
    def _check_token_limits(self, user_id: str, input_text: str, 
                           current_time: float) -> Tuple[bool, Optional[str]]:
        """Check token consumption limits"""
        # Reset daily counters
        if current_time - self.daily_token_reset[user_id] > 86400:
            self.user_tokens[user_id] = 0
            self.daily_token_reset[user_id] = current_time
        
        # Estimate tokens (rough approximation)
        estimated_tokens = len(input_text.split()) * 1.3
        
        # Check per-request token limit
        if estimated_tokens > self.limits['tokens_per_request']:
            return False, f"Request too large: {estimated_tokens:.0f} tokens"
        
        # Check daily token limit
        if self.user_tokens[user_id] + estimated_tokens > self.limits['tokens_per_day']:
            return False, f"Daily token limit exceeded: {self.user_tokens[user_id]:.0f} tokens"
        
        return True, None
    
    def _detect_suspicious_patterns(self, text: str) -> bool:
        """Detect patterns indicating resource abuse"""
        import re
        text_lower = text.lower()
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text_lower):
                logging.warning(f"Suspicious pattern detected: {pattern}")
                return True
        
        # Check for excessive repetition
        words = text_lower.split()
        if len(words) > 50:
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # If any word appears more than 20% of the time, it's suspicious
            max_freq = max(word_freq.values())
            if max_freq > len(words) * 0.2:
                return True
        
        return False
    
    def _detect_theft_attempts(self, text: str) -> bool:
        """Detect model extraction/theft attempts"""
        import re
        text_lower = text.lower()
        
        for pattern in self.theft_patterns:
            if re.search(pattern, text_lower):
                logging.warning(f"Model theft attempt detected: {pattern}")
                return True
        
        return False
    
    def _clean_old_requests(self, user_id: str, ip_address: str, current_time: float):
        """Clean old request records to prevent memory bloat"""
        # Keep only last 24 hours of requests
        cutoff = current_time - 86400
        
        self.user_requests[user_id] = [t for t in self.user_requests[user_id] if t > cutoff]
        self.ip_requests[ip_address] = [t for t in self.ip_requests[ip_address] if t > cutoff]
        
        # Clean empty entries
        if not self.user_requests[user_id]:
            del self.user_requests[user_id]
        if not self.ip_requests[ip_address]:
            del self.ip_requests[ip_address]
    
    def get_usage_stats(self, user_id: str) -> Dict:
        """Get current usage statistics for user"""
        current_time = time.time()
        
        # Count recent requests
        minute_requests = len([t for t in self.user_requests[user_id] 
                              if current_time - t < 60])
        hour_requests = len([t for t in self.user_requests[user_id] 
                            if current_time - t < 3600])
        day_requests = len([t for t in self.user_requests[user_id] 
                           if current_time - t < 86400])
        
        return {
            'requests_last_minute': minute_requests,
            'requests_last_hour': hour_requests,
            'requests_last_day': day_requests,
            'tokens_used_today': self.user_tokens[user_id],
            'active_requests': self.active_requests[user_id],
            'limits': self.limits
        }
    
    def adjust_limits(self, user_tier: str = "free"):
        """Adjust limits based on user tier"""
        if user_tier == "premium":
            self.limits.update({
                'requests_per_minute': 30,
                'requests_per_hour': 500,
                'requests_per_day': 2000,
                'tokens_per_day': 1000000
            })
        elif user_tier == "enterprise":
            self.limits.update({
                'requests_per_minute': 100,
                'requests_per_hour': 2000,
                'requests_per_day': 10000,
                'tokens_per_day': 5000000
            })
    
    def get_circuit_breaker_status(self) -> Dict:
        """Get system-wide circuit breaker status"""
        total_active = sum(self.active_requests.values())
        
        return {
            'total_active_requests': total_active,
            'system_overloaded': total_active > 100,
            'should_throttle': total_active > 50,
            'emergency_mode': total_active > 200
        }