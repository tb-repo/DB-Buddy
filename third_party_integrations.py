"""
Minimal direct integrations with 3rd party AI SQL tools
"""

import requests
import os
from typing import Dict, Optional

class ThirdPartyIntegrations:
    def __init__(self):
        self.api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY')
        }
    
    def use_ai2sql_style(self, natural_query: str, db_type: str = 'postgresql') -> Dict:
        """AI2SQL-style natural language to SQL conversion"""
        if not self.api_keys['openai']:
            return {'error': 'OpenAI API key required'}
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={'Authorization': f'Bearer {self.api_keys["openai"]}'},
                json={
                    'model': 'gpt-3.5-turbo',
                    'messages': [{'role': 'user', 'content': f'Convert to {db_type} SQL: {natural_query}'}],
                    'max_tokens': 200
                },
                timeout=10
            )
            
            if response.status_code == 200:
                sql = response.json()['choices'][0]['message']['content']
                return {'sql': sql, 'confidence': 0.85}
        except:
            pass
        
        return {'error': 'Failed to generate SQL'}
    
    def use_sqlai_style_optimization(self, sql_query: str) -> Dict:
        """SQLAI.ai-style query optimization"""
        if not self.api_keys['anthropic']:
            return {'error': 'Anthropic API key required'}
        
        try:
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={'x-api-key': self.api_keys['anthropic']},
                json={
                    'model': 'claude-3-sonnet-20240229',
                    'max_tokens': 300,
                    'messages': [{'role': 'user', 'content': f'Optimize this SQL: {sql_query}'}]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                optimized = response.json()['content'][0]['text']
                return {'optimized_sql': optimized}
        except:
            pass
        
        return {'error': 'Failed to optimize SQL'}
    
    def use_chat2db_style_error_fix(self, sql_query: str) -> Dict:
        """Chat2DB-style error detection and fixing"""
        errors = []
        fixes = []
        
        # Basic error detection (mimicking Chat2DB approach)
        if not sql_query.strip().endswith(';'):
            errors.append('Missing semicolon')
            fixes.append('Add ; at the end')
        
        if 'SELECT *' in sql_query.upper():
            errors.append('SELECT * usage')
            fixes.append('Specify column names')
        
        return {
            'errors': errors,
            'fixes': fixes,
            'fixed_sql': sql_query + (';' if not sql_query.strip().endswith(';') else '')
        }