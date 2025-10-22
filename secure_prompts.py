"""
Secure System Prompt Management
Prevents sensitive information leakage in system prompts
"""

class SecurePromptManager:
    def __init__(self):
        # Base secure prompt without sensitive details
        self.base_prompt = """You are a database operations assistant. Provide database guidance following security protocols. Focus on database topics only."""
        
    def get_secure_prompt(self, user_context: dict = None) -> str:
        """Generate secure system prompt without sensitive information"""
        
        # Start with secure base
        prompt = self.base_prompt
        
        # Add minimal, non-sensitive context adaptations
        if user_context:
            expertise = user_context.get('expertise_level', 'intermediate')
            urgency = user_context.get('urgency', 'normal')
            
            # Add expertise adaptation WITHOUT revealing internal classification
            if expertise == 'beginner':
                prompt += " Provide step-by-step explanations."
            elif expertise == 'expert':
                prompt += " Focus on technical implementation details."
            
            # Add urgency handling WITHOUT revealing priority system
            if urgency == 'high':
                prompt += " Prioritize immediate solutions."
        
        return prompt
    
    def validate_prompt_security(self, prompt: str) -> dict:
        """Validate that prompt doesn't contain sensitive information"""
        
        # Patterns that should NEVER be in system prompts
        forbidden_patterns = [
            r'password\s*[:=]\s*\w+',
            r'connection\s+string\s*[:=]',
            r'database\s+url\s*[:=]',
            r'api\s+key\s*[:=]',
            r'secret\s*[:=]\s*\w+',
            r'token\s*[:=]\s*\w+',
            r'username\s*[:=]\s*\w+',
            r'host\s*[:=]\s*[\w\.]+'
        ]
        
        # Architecture details that shouldn't be exposed
        architecture_patterns = [
            r'database\s+type:\s+\w+',
            r'cloud\s+provider:\s+\w+',
            r'environment:\s+\w+',
            r'deployment:\s+\w+',
            r'internal\s+classification'
        ]
        
        issues = []
        
        # Check for forbidden sensitive data
        for pattern in forbidden_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                issues.append(f"CRITICAL: Sensitive data pattern: {pattern}")
        
        # Check for architecture exposure
        for pattern in architecture_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                issues.append(f"WARNING: Architecture detail: {pattern}")
        
        return {
            'secure': len([i for i in issues if i.startswith('CRITICAL')]) == 0,
            'issues': issues,
            'risk_level': 'HIGH' if any(i.startswith('CRITICAL') for i in issues) else 'LOW'
        }

import re