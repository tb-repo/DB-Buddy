"""
Vector and Embedding Security Validator
Protects against RAG-based attacks and vector manipulation vulnerabilities
"""
import re
import hashlib
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
import time
import json

class VectorSecurityValidator:
    def __init__(self):
        # Vector integrity validation
        self.vector_dimension_limits = {
            'min_dimensions': 50,
            'max_dimensions': 4096,
            'expected_range': (-1.0, 1.0)
        }
        
        # Embedding poisoning detection patterns
        self.poisoning_indicators = [
            r'adversarial\s+embedding',
            r'vector\s+manipulation',
            r'embedding\s+attack',
            r'similarity\s+spoofing',
            r'retrieval\s+poisoning',
            r'context\s+injection\s+via\s+embedding'
        ]
        
        # Malicious retrieval patterns
        self.malicious_retrieval_patterns = [
            r'retrieve\s+all\s+documents',
            r'bypass\s+retrieval\s+filters',
            r'access\s+restricted\s+context',
            r'override\s+similarity\s+threshold',
            r'inject\s+malicious\s+context'
        ]
        
        # Vector source validation
        self.trusted_vector_sources = {
            'openai': 'api.openai.com',
            'huggingface': 'api-inference.huggingface.co',
            'cohere': 'api.cohere.ai'
        }
        
        # Context contamination patterns
        self.contamination_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'eval\s*\(',
            r'document\.cookie',
            r'window\.location',
            r'localStorage\.',
            r'sessionStorage\.'
        ]
        
        # Sensitive information in embeddings
        self.embedding_sensitive_patterns = [
            (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'Credit Card in Vector'),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'Email in Vector'),
            (r'password[\s]*[:=][\s]*[^\s]+', 'Password in Vector'),
            (r'api[\s_]*key[\s]*[:=][\s]*[^\s]+', 'API Key in Vector'),
            (r'bearer[\s]+[a-zA-Z0-9\-._~+/]+=*', 'Bearer Token in Vector')
        ]
        
        # Vector similarity thresholds for anomaly detection
        self.similarity_thresholds = {
            'min_similarity': 0.1,
            'max_similarity': 0.99,
            'anomaly_threshold': 0.95,
            'clustering_threshold': 0.8
        }
        
        # RAG context validation
        self.max_context_length = 8000
        self.max_retrieved_documents = 10
        self.context_diversity_threshold = 0.3
        
        # Vector storage security
        self.vector_checksums = {}
        self.vector_access_log = []
        
        # Embedding model validation
        self.approved_models = {
            'text-embedding-ada-002': {'provider': 'openai', 'dimensions': 1536},
            'sentence-transformers/all-MiniLM-L6-v2': {'provider': 'huggingface', 'dimensions': 384},
            'embed-english-v2.0': {'provider': 'cohere', 'dimensions': 4096}
        }
    
    def validate_vector_input(self, text: str, source: str = "user") -> Tuple[bool, Optional[str]]:
        """Validate text before vector embedding generation"""
        
        # Check for embedding poisoning attempts
        if self._detect_embedding_poisoning(text):
            self.log_security_event("EMBEDDING_POISONING_ATTEMPT", source, text[:100])
            return False, "🚨 Vector Security: Embedding poisoning attempt detected"
        
        # Check for malicious retrieval patterns
        if self._detect_malicious_retrieval(text):
            self.log_security_event("MALICIOUS_RETRIEVAL_ATTEMPT", source, text[:100])
            return False, "🚨 RAG Security: Malicious retrieval pattern detected"
        
        # Validate text length for embedding
        if len(text) > 8000:  # Most embedding models have token limits
            return False, "⚠️ Text too long for safe embedding generation"
        
        # Check for context contamination
        if self._detect_context_contamination(text):
            return False, "🛡️ Context Security: Contamination patterns detected"
        
        # Check for sensitive information
        sensitive_type = self._detect_sensitive_in_embedding(text)
        if sensitive_type:
            return False, f"🔒 Privacy: {sensitive_type} detected in embedding input"
        
        return True, None
    
    def validate_vector_integrity(self, vector: List[float], metadata: Dict = None) -> Dict:
        """Validate vector integrity and detect manipulation"""
        
        if not isinstance(vector, (list, np.ndarray)):
            return {'valid': False, 'reason': 'Invalid vector format'}
        
        vector_array = np.array(vector)
        
        # Dimension validation
        if len(vector_array) < self.vector_dimension_limits['min_dimensions']:
            return {'valid': False, 'reason': 'Vector dimensions too small'}
        
        if len(vector_array) > self.vector_dimension_limits['max_dimensions']:
            return {'valid': False, 'reason': 'Vector dimensions too large'}
        
        # Range validation
        min_val, max_val = self.vector_dimension_limits['expected_range']
        if np.any(vector_array < min_val) or np.any(vector_array > max_val):
            return {'valid': False, 'reason': 'Vector values outside expected range'}
        
        # Statistical anomaly detection
        anomalies = self._detect_vector_anomalies(vector_array)
        if anomalies['has_anomalies']:
            self.log_security_event("VECTOR_ANOMALY", "system", f"Anomalies: {anomalies['details']}")
            return {'valid': False, 'reason': f"Vector anomalies detected: {anomalies['details']}"}
        
        # Generate and store checksum for integrity tracking
        vector_hash = self._generate_vector_checksum(vector_array)
        if metadata:
            self.vector_checksums[metadata.get('id', vector_hash)] = vector_hash
        
        return {'valid': True, 'checksum': vector_hash}
    
    def validate_retrieval_context(self, retrieved_docs: List[Dict], query: str) -> Dict:
        """Validate retrieved context for RAG security"""
        
        if len(retrieved_docs) > self.max_retrieved_documents:
            return {
                'valid': False, 
                'reason': f'Too many documents retrieved: {len(retrieved_docs)} > {self.max_retrieved_documents}'
            }
        
        total_context_length = sum(len(doc.get('content', '')) for doc in retrieved_docs)
        if total_context_length > self.max_context_length:
            return {
                'valid': False,
                'reason': f'Context too long: {total_context_length} > {self.max_context_length}'
            }
        
        # Check context diversity to prevent clustering attacks
        diversity_score = self._calculate_context_diversity(retrieved_docs)
        if diversity_score < self.context_diversity_threshold:
            self.log_security_event("LOW_CONTEXT_DIVERSITY", "system", f"Diversity: {diversity_score}")
            return {
                'valid': False,
                'reason': f'Low context diversity detected: {diversity_score}'
            }
        
        # Validate each document for contamination
        contaminated_docs = []
        for i, doc in enumerate(retrieved_docs):
            content = doc.get('content', '')
            if self._detect_context_contamination(content):
                contaminated_docs.append(i)
        
        if contaminated_docs:
            return {
                'valid': False,
                'reason': f'Contaminated documents detected at indices: {contaminated_docs}'
            }
        
        # Check for sensitive information in retrieved context
        for doc in retrieved_docs:
            sensitive_type = self._detect_sensitive_in_embedding(doc.get('content', ''))
            if sensitive_type:
                return {
                    'valid': False,
                    'reason': f'Sensitive information in retrieved context: {sensitive_type}'
                }
        
        return {'valid': True, 'diversity_score': diversity_score}
    
    def validate_embedding_model(self, model_name: str, provider: str, endpoint: str) -> bool:
        """Validate embedding model against approved list"""
        
        if model_name not in self.approved_models:
            self.log_security_event("UNAPPROVED_EMBEDDING_MODEL", provider, model_name)
            return False
        
        model_info = self.approved_models[model_name]
        if model_info['provider'] != provider:
            return False
        
        if provider not in self.trusted_vector_sources:
            return False
        
        if self.trusted_vector_sources[provider] not in endpoint:
            return False
        
        return True
    
    def sanitize_retrieval_context(self, context: str) -> str:
        """Sanitize retrieved context before use in RAG"""
        
        sanitized = context
        
        # Remove potential XSS/injection patterns
        for pattern in self.contamination_patterns:
            sanitized = re.sub(pattern, '[SANITIZED]', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove sensitive information
        for pattern, info_type in self.embedding_sensitive_patterns:
            sanitized = re.sub(pattern, f'[{info_type} REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Limit context length
        if len(sanitized) > self.max_context_length:
            sanitized = sanitized[:self.max_context_length] + "... [TRUNCATED FOR SECURITY]"
        
        return sanitized
    
    def _detect_embedding_poisoning(self, text: str) -> bool:
        """Detect embedding poisoning attempts"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in self.poisoning_indicators)
    
    def _detect_malicious_retrieval(self, text: str) -> bool:
        """Detect malicious retrieval patterns"""
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in self.malicious_retrieval_patterns)
    
    def _detect_context_contamination(self, text: str) -> bool:
        """Detect context contamination patterns"""
        return any(re.search(pattern, text, re.IGNORECASE | re.DOTALL) for pattern in self.contamination_patterns)
    
    def _detect_sensitive_in_embedding(self, text: str) -> Optional[str]:
        """Detect sensitive information in embedding text"""
        for pattern, info_type in self.embedding_sensitive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return info_type
        return None
    
    def _detect_vector_anomalies(self, vector: np.ndarray) -> Dict:
        """Detect statistical anomalies in vectors"""
        anomalies = []
        
        # Check for unusual statistical properties
        mean_val = np.mean(vector)
        std_val = np.std(vector)
        
        # Detect vectors with unusual mean (too close to extremes)
        if abs(mean_val) > 0.5:
            anomalies.append(f"Unusual mean: {mean_val}")
        
        # Detect vectors with unusual standard deviation
        if std_val < 0.01 or std_val > 1.0:
            anomalies.append(f"Unusual std: {std_val}")
        
        # Check for repeated values (potential manipulation)
        unique_values = len(np.unique(vector))
        if unique_values < len(vector) * 0.8:  # Less than 80% unique values
            anomalies.append(f"Low uniqueness: {unique_values}/{len(vector)}")
        
        # Check for extreme values clustering
        extreme_count = np.sum((vector < -0.8) | (vector > 0.8))
        if extreme_count > len(vector) * 0.1:  # More than 10% extreme values
            anomalies.append(f"Too many extreme values: {extreme_count}")
        
        return {
            'has_anomalies': len(anomalies) > 0,
            'details': anomalies
        }
    
    def _calculate_context_diversity(self, docs: List[Dict]) -> float:
        """Calculate diversity score of retrieved documents"""
        if len(docs) < 2:
            return 1.0
        
        # Simple diversity calculation based on content length variation
        # In a real implementation, you'd use actual vector similarity
        lengths = [len(doc.get('content', '')) for doc in docs]
        if not lengths:
            return 0.0
        
        mean_length = np.mean(lengths)
        std_length = np.std(lengths)
        
        # Normalize diversity score (higher std = more diverse)
        diversity = min(1.0, std_length / (mean_length + 1))
        return diversity
    
    def _generate_vector_checksum(self, vector: np.ndarray) -> str:
        """Generate checksum for vector integrity verification"""
        vector_bytes = vector.tobytes()
        return hashlib.sha256(vector_bytes).hexdigest()[:16]
    
    def verify_vector_integrity(self, vector: np.ndarray, expected_checksum: str) -> bool:
        """Verify vector hasn't been tampered with"""
        current_checksum = self._generate_vector_checksum(vector)
        return current_checksum == expected_checksum
    
    def get_rag_security_config(self) -> Dict:
        """Get RAG security configuration"""
        return {
            'max_context_length': self.max_context_length,
            'max_retrieved_documents': self.max_retrieved_documents,
            'similarity_thresholds': self.similarity_thresholds,
            'context_diversity_threshold': self.context_diversity_threshold,
            'approved_models': list(self.approved_models.keys())
        }
    
    def log_vector_access(self, operation: str, vector_id: str, user_id: str):
        """Log vector access for audit trail"""
        self.vector_access_log.append({
            'timestamp': time.time(),
            'operation': operation,
            'vector_id': vector_id,
            'user_id': user_id
        })
        
        # Keep only recent logs (last 1000 entries)
        if len(self.vector_access_log) > 1000:
            self.vector_access_log = self.vector_access_log[-1000:]
    
    def detect_vector_clustering_attack(self, vectors: List[np.ndarray], threshold: float = None) -> Dict:
        """Detect potential vector clustering attacks"""
        if len(vectors) < 3:
            return {'attack_detected': False, 'reason': 'Insufficient vectors for analysis'}
        
        threshold = threshold or self.similarity_thresholds['clustering_threshold']
        
        # Calculate pairwise similarities (simplified - in practice use cosine similarity)
        high_similarity_pairs = 0
        total_pairs = 0
        
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                # Simplified similarity calculation
                similarity = np.dot(vectors[i], vectors[j]) / (np.linalg.norm(vectors[i]) * np.linalg.norm(vectors[j]))
                total_pairs += 1
                
                if similarity > threshold:
                    high_similarity_pairs += 1
        
        clustering_ratio = high_similarity_pairs / total_pairs if total_pairs > 0 else 0
        
        if clustering_ratio > 0.5:  # More than 50% of pairs are highly similar
            self.log_security_event("VECTOR_CLUSTERING_ATTACK", "system", f"Clustering ratio: {clustering_ratio}")
            return {
                'attack_detected': True,
                'clustering_ratio': clustering_ratio,
                'reason': f'High clustering detected: {clustering_ratio:.2%} of vector pairs are highly similar'
            }
        
        return {'attack_detected': False, 'clustering_ratio': clustering_ratio}
    
    def log_security_event(self, event_type: str, source: str, details: str):
        """Log vector security events"""
        logging.warning(f"VECTOR_SECURITY_EVENT: {event_type} | Source: {source} | Details: {details}")