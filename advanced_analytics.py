import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import hashlib

class AdvancedAnalytics:
    def __init__(self):
        self.query_patterns = {}
        self.workload_data = {}
        self.performance_history = {}
    
    def analyze_query_plan_interactive(self, execution_plan: str, user_selections: Dict) -> Dict:
        """Generate interactive query plan data"""
        lines = execution_plan.split('\n')
        plan_nodes = []
        
        for i, line in enumerate(lines):
            if '->' in line or 'Scan' in line or 'Join' in line:
                node = self._parse_plan_node(line, i)
                if node:
                    plan_nodes.append(node)
        
        return {
            'nodes': plan_nodes,
            'total_cost': self._extract_total_cost(execution_plan),
            'execution_time': self._extract_execution_time(execution_plan),
            'bottlenecks': self._identify_bottlenecks(plan_nodes),
            'optimization_suggestions': self._get_node_optimizations(plan_nodes)
        }
    
    def generate_performance_heatmap(self, queries: List[str], user_selections: Dict) -> Dict:
        """Generate performance heatmap data"""
        heatmap_data = {
            'tables': {},
            'operations': {},
            'time_periods': {},
            'severity_levels': {}
        }
        
        for query in queries:
            tables = self._extract_tables(query)
            operations = self._classify_operations(query)
            
            for table in tables:
                if table not in heatmap_data['tables']:
                    heatmap_data['tables'][table] = {'frequency': 0, 'avg_cost': 0, 'issues': []}
                heatmap_data['tables'][table]['frequency'] += 1
                
            for op in operations:
                if op not in heatmap_data['operations']:
                    heatmap_data['operations'][op] = {'count': 0, 'performance_impact': 'medium'}
                heatmap_data['operations'][op]['count'] += 1
        
        return heatmap_data
    
    def assess_change_risk(self, recommendations: List[str], user_selections: Dict) -> Dict:
        """Assess risk of implementing recommendations"""
        risk_assessment = {
            'overall_risk': 'medium',
            'risk_factors': [],
            'mitigation_strategies': [],
            'rollback_plan': [],
            'testing_requirements': []
        }
        
        environment = user_selections.get('environment', '')
        deployment = user_selections.get('deployment', '')
        
        high_risk_keywords = ['drop', 'alter table', 'truncate', 'delete']
        medium_risk_keywords = ['create index', 'update statistics', 'vacuum']
        
        risk_score = 0
        
        for rec in recommendations:
            rec_lower = rec.lower()
            if any(keyword in rec_lower for keyword in high_risk_keywords):
                risk_score += 3
                risk_assessment['risk_factors'].append(f"High-impact operation detected: {rec[:50]}...")
            elif any(keyword in rec_lower for keyword in medium_risk_keywords):
                risk_score += 1
                risk_assessment['risk_factors'].append(f"Medium-impact operation: {rec[:50]}...")
        
        if environment == 'Production':
            risk_score += 2
            risk_assessment['risk_factors'].append("Production environment increases risk")
        
        if risk_score >= 5:
            risk_assessment['overall_risk'] = 'high'
        elif risk_score >= 2:
            risk_assessment['overall_risk'] = 'medium'
        else:
            risk_assessment['overall_risk'] = 'low'
        
        # Add mitigation strategies
        risk_assessment['mitigation_strategies'] = [
            "Test all changes in staging environment first",
            "Create database backup before implementation",
            "Implement changes during maintenance window",
            "Monitor performance metrics during and after changes",
            "Have rollback procedures ready"
        ]
        
        return risk_assessment
    
    def characterize_workload(self, queries: List[str], user_selections: Dict) -> Dict:
        """Analyze and categorize database workload"""
        workload_analysis = {
            'workload_type': 'mixed',
            'query_distribution': {},
            'complexity_analysis': {},
            'resource_patterns': {},
            'optimization_opportunities': []
        }
        
        query_types = {'SELECT': 0, 'INSERT': 0, 'UPDATE': 0, 'DELETE': 0}
        complexity_scores = []
        
        for query in queries:
            query_upper = query.upper()
            
            # Count query types
            for qtype in query_types:
                if qtype in query_upper:
                    query_types[qtype] += 1
                    break
            
            # Analyze complexity
            complexity = self._calculate_query_complexity(query)
            complexity_scores.append(complexity)
        
        total_queries = sum(query_types.values())
        if total_queries > 0:
            workload_analysis['query_distribution'] = {
                k: round((v/total_queries)*100, 1) for k, v in query_types.items()
            }
        
        # Determine workload type
        read_percentage = workload_analysis['query_distribution'].get('SELECT', 0)
        if read_percentage > 80:
            workload_analysis['workload_type'] = 'read_heavy'
        elif read_percentage < 30:
            workload_analysis['workload_type'] = 'write_heavy'
        else:
            workload_analysis['workload_type'] = 'mixed'
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        workload_analysis['complexity_analysis'] = {
            'average_complexity': round(avg_complexity, 2),
            'complexity_distribution': self._categorize_complexity(complexity_scores)
        }
        
        return workload_analysis
    
    def optimize_resource_utilization(self, workload_data: Dict, user_selections: Dict) -> Dict:
        """Provide resource optimization recommendations"""
        optimization = {
            'current_assessment': {},
            'recommendations': [],
            'cost_impact': {},
            'performance_impact': {}
        }
        
        deployment = user_selections.get('deployment', '')
        cloud_provider = user_selections.get('cloud_provider', '')
        db_system = user_selections.get('database', '')
        
        workload_type = workload_data.get('workload_type', 'mixed')
        
        if deployment == 'Cloud' and 'AWS' in cloud_provider:
            if workload_type == 'read_heavy':
                optimization['recommendations'].extend([
                    "Consider Aurora Read Replicas for read scaling",
                    "Use Aurora Auto Scaling for dynamic read replica management",
                    "Implement connection pooling with RDS Proxy",
                    "Consider Aurora Serverless v2 for variable workloads"
                ])
            elif workload_type == 'write_heavy':
                optimization['recommendations'].extend([
                    "Optimize instance class for write performance",
                    "Consider Provisioned IOPS for consistent performance",
                    "Implement write-optimized storage configuration",
                    "Monitor and tune buffer pool settings"
                ])
        
        optimization['cost_impact'] = {
            'estimated_savings': '15-30%',
            'implementation_cost': 'Low to Medium',
            'payback_period': '2-4 months'
        }
        
        return optimization
    
    def analyze_query_patterns(self, queries: List[str]) -> Dict:
        """Identify common patterns and anti-patterns"""
        pattern_analysis = {
            'common_patterns': [],
            'anti_patterns': [],
            'optimization_opportunities': [],
            'pattern_frequency': {}
        }
        
        anti_patterns = {
            'SELECT *': 0,
            'Missing WHERE': 0,
            'Cartesian JOIN': 0,
            'Subquery in SELECT': 0,
            'OR in WHERE': 0
        }
        
        for query in queries:
            query_upper = query.upper()
            
            # Check for anti-patterns
            if 'SELECT *' in query_upper:
                anti_patterns['SELECT *'] += 1
            
            if 'SELECT' in query_upper and 'WHERE' not in query_upper:
                anti_patterns['Missing WHERE'] += 1
            
            if 'JOIN' in query_upper and 'ON' not in query_upper:
                anti_patterns['Cartesian JOIN'] += 1
            
            if query_upper.count('SELECT') > 1:
                anti_patterns['Subquery in SELECT'] += 1
            
            if ' OR ' in query_upper:
                anti_patterns['OR in WHERE'] += 1
        
        # Generate recommendations based on patterns
        for pattern, count in anti_patterns.items():
            if count > 0:
                pattern_analysis['anti_patterns'].append({
                    'pattern': pattern,
                    'frequency': count,
                    'recommendation': self._get_pattern_recommendation(pattern)
                })
        
        return pattern_analysis
    
    def _parse_plan_node(self, line: str, line_num: int) -> Dict:
        """Parse execution plan node"""
        node = {
            'id': line_num,
            'operation': '',
            'cost': 0,
            'rows': 0,
            'time': 0,
            'details': line.strip()
        }
        
        # Extract operation type
        if 'Seq Scan' in line:
            node['operation'] = 'Sequential Scan'
        elif 'Index Scan' in line:
            node['operation'] = 'Index Scan'
        elif 'Hash Join' in line:
            node['operation'] = 'Hash Join'
        elif 'Nested Loop' in line:
            node['operation'] = 'Nested Loop'
        
        # Extract cost
        cost_match = re.search(r'cost=(\d+\.?\d*)', line)
        if cost_match:
            node['cost'] = float(cost_match.group(1))
        
        # Extract rows
        rows_match = re.search(r'rows=(\d+)', line)
        if rows_match:
            node['rows'] = int(rows_match.group(1))
        
        return node
    
    def _extract_total_cost(self, plan: str) -> float:
        """Extract total cost from execution plan"""
        costs = re.findall(r'cost=(\d+\.?\d*)', plan)
        return max([float(c) for c in costs]) if costs else 0
    
    def _extract_execution_time(self, plan: str) -> str:
        """Extract execution time from plan"""
        time_match = re.search(r'Execution Time: ([\d.]+) ms', plan)
        return time_match.group(1) + ' ms' if time_match else 'Unknown'
    
    def _identify_bottlenecks(self, nodes: List[Dict]) -> List[Dict]:
        """Identify performance bottlenecks in plan"""
        bottlenecks = []
        
        for node in nodes:
            if node['cost'] > 1000:  # High cost threshold
                bottlenecks.append({
                    'node_id': node['id'],
                    'issue': 'High cost operation',
                    'severity': 'high',
                    'recommendation': 'Consider indexing or query rewrite'
                })
            
            if node['operation'] == 'Sequential Scan' and node['rows'] > 10000:
                bottlenecks.append({
                    'node_id': node['id'],
                    'issue': 'Large sequential scan',
                    'severity': 'medium',
                    'recommendation': 'Add appropriate index'
                })
        
        return bottlenecks
    
    def _get_node_optimizations(self, nodes: List[Dict]) -> List[str]:
        """Get optimization suggestions for plan nodes"""
        suggestions = []
        
        for node in nodes:
            if node['operation'] == 'Sequential Scan':
                suggestions.append(f"Consider adding index for {node['operation']}")
            elif node['operation'] == 'Hash Join' and node['cost'] > 500:
                suggestions.append(f"Optimize join conditions for {node['operation']}")
        
        return suggestions
    
    def _extract_tables(self, query: str) -> List[str]:
        """Extract table names from query"""
        # Simple regex to find table names after FROM and JOIN
        tables = []
        from_match = re.findall(r'FROM\s+(\w+)', query, re.IGNORECASE)
        join_match = re.findall(r'JOIN\s+(\w+)', query, re.IGNORECASE)
        
        tables.extend(from_match)
        tables.extend(join_match)
        
        return list(set(tables))
    
    def _classify_operations(self, query: str) -> List[str]:
        """Classify query operations"""
        operations = []
        query_upper = query.upper()
        
        if 'SELECT' in query_upper:
            operations.append('SELECT')
        if 'JOIN' in query_upper:
            operations.append('JOIN')
        if 'WHERE' in query_upper:
            operations.append('FILTER')
        if 'ORDER BY' in query_upper:
            operations.append('SORT')
        if 'GROUP BY' in query_upper:
            operations.append('AGGREGATE')
        
        return operations
    
    def _calculate_query_complexity(self, query: str) -> float:
        """Calculate query complexity score"""
        complexity = 0
        query_upper = query.upper()
        
        # Count complexity factors
        complexity += query_upper.count('JOIN') * 2
        complexity += query_upper.count('SUBQUERY') * 3
        complexity += query_upper.count('UNION') * 2
        complexity += query_upper.count('CASE') * 1
        complexity += query_upper.count('GROUP BY') * 1
        complexity += query_upper.count('ORDER BY') * 1
        
        return complexity
    
    def _categorize_complexity(self, scores: List[float]) -> Dict:
        """Categorize complexity scores"""
        if not scores:
            return {'simple': 0, 'moderate': 0, 'complex': 0}
        
        simple = sum(1 for s in scores if s <= 2)
        moderate = sum(1 for s in scores if 2 < s <= 5)
        complex_count = sum(1 for s in scores if s > 5)
        
        total = len(scores)
        return {
            'simple': round((simple/total)*100, 1),
            'moderate': round((moderate/total)*100, 1),
            'complex': round((complex_count/total)*100, 1)
        }
    
    def _get_pattern_recommendation(self, pattern: str) -> str:
        """Get recommendation for anti-pattern"""
        recommendations = {
            'SELECT *': 'Specify only needed columns to reduce I/O and network traffic',
            'Missing WHERE': 'Add WHERE clause to limit rows processed',
            'Cartesian JOIN': 'Add proper JOIN conditions to avoid cartesian products',
            'Subquery in SELECT': 'Consider using JOINs instead of subqueries for better performance',
            'OR in WHERE': 'Consider using UNION or IN clause for better index usage'
        }
        return recommendations.get(pattern, 'Review query structure for optimization opportunities')