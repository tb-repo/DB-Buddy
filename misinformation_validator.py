"""
Misinformation and Hallucination Detection Validator
Prevents false or misleading information in LLM responses
"""
import re
import time
from typing import Dict, List, Tuple, Optional
import logging

class MisinformationValidator:
    def __init__(self):
        # Hallucination indicators
        self.hallucination_patterns = [
            r'always\s+(true|false|works|fails)',
            r'never\s+(happens|works|fails)',
            r'100%\s+(certain|guaranteed|accurate)',
            r'absolutely\s+(guaranteed|certain|never)',
            r'impossible\s+to\s+(fail|break)',
            r'will\s+definitely\s+(work|fix|solve)',
            r'proven\s+fact\s+that',
            r'scientific\s+consensus\s+shows',
            r'all\s+experts\s+agree',
            r'universally\s+accepted'
        ]
        
        # Overconfidence indicators
        self.overconfidence_patterns = [
            r'this\s+is\s+the\s+only\s+solution',
            r'guaranteed\s+to\s+(work|fix)',
            r'will\s+solve\s+all\s+your\s+problems',
            r'perfect\s+solution\s+for',
            r'foolproof\s+method',
            r'cannot\s+possibly\s+fail',
            r'works\s+in\s+all\s+cases',
            r'no\s+exceptions\s+whatsoever'
        ]
        
        # Database-specific misinformation patterns
        self.db_misinformation_patterns = [
            r'this\s+query\s+will\s+never\s+be\s+slow',
            r'indexes\s+always\s+improve\s+performance',
            r'normalization\s+is\s+always\s+better',
            r'nosql\s+is\s+always\s+faster\s+than\s+sql',
            r'cloud\s+databases\s+never\s+fail',
            r'this\s+will\s+work\s+on\s+any\s+database',
            r'no\s+need\s+to\s+test\s+this\s+change',
            r'backup\s+is\s+not\s+necessary'
        ]
        
        # Uncertainty indicators (good signs)
        self.uncertainty_indicators = [
            r'might\s+work',
            r'could\s+help',
            r'typically\s+improves',
            r'in\s+most\s+cases',
            r'generally\s+recommended',
            r'usually\s+effective',
            r'may\s+resolve',
            r'often\s+helps',
            r'consider\s+testing',
            r'verify\s+in\s+your\s+environment'
        ]
        
        # Fact-checking requirements
        self.fact_check_triggers = [
            r'studies\s+show',
            r'research\s+indicates',
            r'statistics\s+prove',
            r'data\s+confirms',
            r'benchmarks\s+demonstrate',
            r'industry\s+standard',
            r'best\s+practice\s+is',
            r'recommended\s+by\s+experts'
        ]
        
        # Bias indicators
        self.bias_patterns = [
            r'obviously\s+better\s+than',
            r'clearly\s+superior\s+to',
            r'everyone\s+knows\s+that',
            r'common\s+sense\s+dictates',
            r'any\s+competent\s+dba\s+would',
            r'only\s+beginners\s+use',
            r'real\s+professionals\s+never'
        ]
        
        # Response quality thresholds
        self.quality_thresholds = {
            'min_uncertainty_ratio': 0.1,  # At least 10% uncertainty indicators
            'max_overconfidence_ratio': 0.05,  # Max 5% overconfidence
            'max_hallucination_score': 3,  # Max 3 hallucination indicators
            'min_verification_mentions': 1  # At least 1 verification reminder
        }
        
        # Database fact database (simplified)
        self.db_facts = {
            'postgresql_max_connections': {'min': 100, 'max': 10000, 'typical': 200},
            'mysql_max_connections': {'min': 151, 'max': 100000, 'typical': 500},
            'index_improvement': {'typical_range': '10-90%', 'depends_on': 'query_pattern'},
            'normalization': {'benefits': ['data_integrity'], 'costs': ['join_overhead']}
        }
    
    def validate_response(self, response: str, context: str = "") -> Dict:
        """Validate response for misinformation and hallucinations"""
        
        # Calculate misinformation scores
        hallucination_score = self._calculate_hallucination_score(response)
        overconfidence_score = self._calculate_overconfidence_score(response)
        bias_score = self._calculate_bias_score(response)
        uncertainty_score = self._calculate_uncertainty_score(response)
        
        # Check for fact-checking requirements
        needs_fact_check = self._needs_fact_checking(response)
        
        # Validate database-specific claims
        db_claims_valid = self._validate_db_claims(response)
        
        # Calculate overall misinformation risk
        risk_score = self._calculate_risk_score(
            hallucination_score, overconfidence_score, bias_score, uncertainty_score
        )
        
        # Generate validation result
        result = {
            'is_valid': risk_score < 0.7,  # Threshold for acceptance
            'risk_score': risk_score,
            'hallucination_score': hallucination_score,
            'overconfidence_score': overconfidence_score,
            'bias_score': bias_score,
            'uncertainty_score': uncertainty_score,
            'needs_fact_check': needs_fact_check,
            'db_claims_valid': db_claims_valid,
            'warnings': self._generate_warnings(risk_score, hallucination_score, overconfidence_score),
            'recommendations': self._generate_recommendations(response, risk_score)
        }
        
        # Log high-risk responses
        if risk_score > 0.5:
            self.log_misinformation_risk(response[:200], risk_score, result)
        
        return result
    
    def _calculate_hallucination_score(self, text: str) -> float:
        """Calculate hallucination risk score"""
        text_lower = text.lower()
        hallucination_count = sum(
            len(re.findall(pattern, text_lower)) for pattern in self.hallucination_patterns
        )
        
        # Normalize by text length
        words = len(text.split())
        return min(1.0, hallucination_count / max(1, words / 100))
    
    def _calculate_overconfidence_score(self, text: str) -> float:
        """Calculate overconfidence risk score"""
        text_lower = text.lower()
        overconfidence_count = sum(
            len(re.findall(pattern, text_lower)) for pattern in self.overconfidence_patterns
        )
        
        words = len(text.split())
        return min(1.0, overconfidence_count / max(1, words / 50))
    
    def _calculate_bias_score(self, text: str) -> float:
        """Calculate bias risk score"""
        text_lower = text.lower()
        bias_count = sum(
            len(re.findall(pattern, text_lower)) for pattern in self.bias_patterns
        )
        
        words = len(text.split())
        return min(1.0, bias_count / max(1, words / 100))
    
    def _calculate_uncertainty_score(self, text: str) -> float:
        """Calculate uncertainty/humility score (higher is better)"""
        text_lower = text.lower()
        uncertainty_count = sum(
            len(re.findall(pattern, text_lower)) for pattern in self.uncertainty_indicators
        )
        
        words = len(text.split())
        return min(1.0, uncertainty_count / max(1, words / 50))
    
    def _needs_fact_checking(self, text: str) -> bool:
        """Check if response makes claims requiring fact-checking"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in self.fact_check_triggers)
    
    def _validate_db_claims(self, text: str) -> bool:
        """Validate database-specific claims against known facts"""
        text_lower = text.lower()
        
        # Check for specific false claims
        false_claims = [
            r'postgresql\s+supports\s+unlimited\s+connections',
            r'indexes\s+never\s+slow\s+down\s+writes',
            r'nosql\s+databases\s+are\s+always\s+acid\s+compliant',
            r'denormalization\s+always\s+improves\s+performance',
            r'cloud\s+databases\s+have\s+100%\s+uptime'
        ]
        
        return not any(re.search(claim, text_lower) for claim in false_claims)
    
    def _calculate_risk_score(self, hallucination: float, overconfidence: float, 
                            bias: float, uncertainty: float) -> float:
        """Calculate overall misinformation risk score"""
        # Higher hallucination, overconfidence, and bias increase risk
        # Higher uncertainty decreases risk
        risk = (hallucination * 0.4 + overconfidence * 0.3 + bias * 0.2) - (uncertainty * 0.1)
        return max(0.0, min(1.0, risk))
    
    def _generate_warnings(self, risk_score: float, hallucination: float, 
                          overconfidence: float) -> List[str]:
        """Generate warnings based on risk scores"""
        warnings = []
        
        if risk_score > 0.7:
            warnings.append("High misinformation risk detected")
        
        if hallucination > 0.3:
            warnings.append("Potential hallucination patterns detected")
        
        if overconfidence > 0.3:
            warnings.append("Overconfident claims detected")
        
        return warnings
    
    def _generate_recommendations(self, response: str, risk_score: float) -> List[str]:
        """Generate recommendations to improve response quality"""
        recommendations = []
        
        if risk_score > 0.5:
            recommendations.append("Add uncertainty qualifiers (e.g., 'typically', 'usually', 'in most cases')")
            recommendations.append("Include verification reminders")
            recommendations.append("Provide testing recommendations")
        
        if not re.search(r'test|verify|validate|confirm', response.lower()):
            recommendations.append("Add testing/verification guidance")
        
        if not re.search(r'may|might|could|typically|usually', response.lower()):
            recommendations.append("Use more cautious language")
        
        return recommendations
    
    def enhance_response_reliability(self, response: str) -> str:
        """Enhance response to reduce misinformation risk"""
        enhanced = response
        
        # Add verification reminders
        if not re.search(r'test|verify|validate', enhanced.lower()):
            enhanced += "\n\n⚠️ **Verification Required**: Test these recommendations in a development environment before production implementation."
        
        # Add uncertainty qualifiers to absolute statements
        enhanced = re.sub(r'\bwill\s+fix\b', 'should help fix', enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r'\bguaranteed\s+to\b', 'likely to', enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r'\balways\s+works\b', 'typically works', enhanced, flags=re.IGNORECASE)
        
        # Add disclaimers for database recommendations
        if re.search(r'index|query|performance', enhanced.lower()):
            enhanced += "\n\n💡 **Note**: Database performance depends on specific data patterns, hardware, and workload characteristics. Results may vary."
        
        return enhanced
    
    def get_overreliance_warning(self, context: str = "") -> str:
        """Generate warning about overreliance on AI recommendations"""
        return """🚨 **AI Reliability Notice**: 

**Verify Before Implementation**:
• Test all recommendations in development first
• Validate performance claims with your specific data
• Consult database documentation for version-specific features
• Consider your unique environment and constraints

**AI Limitations**:
• May not account for all edge cases
• Recommendations based on general patterns
• Cannot replace domain expertise and testing
• May contain outdated or incomplete information

**Best Practice**: Use AI recommendations as starting points, not final solutions."""
    
    def log_misinformation_risk(self, response_snippet: str, risk_score: float, details: Dict):
        """Log high-risk responses for monitoring"""
        logging.warning(f"MISINFORMATION_RISK: Score={risk_score:.2f} | Response: {response_snippet} | Details: {details}")