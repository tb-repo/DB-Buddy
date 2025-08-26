// Analytics Dashboard JavaScript

class AnalyticsDashboard {
    constructor() {
        this.queryPlanData = null;
        this.heatmapData = null;
        this.workloadChart = null;
        this.init();
    }

    init() {
        this.loadAnalyticsData();
        this.setupEventListeners();
    }

    async loadAnalyticsData() {
        try {
            const response = await fetch('/api/analytics/data');
            const data = await response.json();
            
            this.renderQueryPlan(data.queryPlan);
            this.renderPerformanceHeatmap(data.heatmap);
            this.renderRiskAssessment(data.riskAssessment);
            this.renderWorkloadAnalysis(data.workloadAnalysis);
            this.renderResourceOptimization(data.resourceOptimization);
            this.renderPatternAnalysis(data.patternAnalysis);
        } catch (error) {
            console.error('Failed to load analytics data:', error);
            this.loadSampleData();
        }
    }

    loadSampleData() {
        // Sample data for demonstration
        const sampleData = {
            queryPlan: {
                nodes: [
                    { id: 1, operation: 'Hash Join', cost: 1250.45, rows: 15000, time: 45.2, details: 'Hash Join (cost=1250.45..1890.23 rows=15000 width=64)' },
                    { id: 2, operation: 'Sequential Scan', cost: 890.12, rows: 50000, time: 120.5, details: 'Seq Scan on customer_table (cost=0.00..890.12 rows=50000 width=32)' },
                    { id: 3, operation: 'Index Scan', cost: 45.67, rows: 1200, time: 8.3, details: 'Index Scan using idx_customer_id (cost=0.43..45.67 rows=1200 width=16)' }
                ],
                bottlenecks: [
                    { node_id: 1, issue: 'High cost operation', severity: 'high' },
                    { node_id: 2, issue: 'Large sequential scan', severity: 'medium' }
                ]
            },
            heatmap: {
                tables: {
                    'customer_table': { frequency: 45, avg_cost: 890, issues: ['seq_scan'] },
                    'order_table': { frequency: 32, avg_cost: 234, issues: [] },
                    'product_table': { frequency: 28, avg_cost: 156, issues: ['missing_index'] }
                },
                operations: {
                    'SELECT': { count: 85, performance_impact: 'medium' },
                    'JOIN': { count: 42, performance_impact: 'high' },
                    'FILTER': { count: 67, performance_impact: 'low' }
                }
            },
            riskAssessment: {
                overall_risk: 'medium',
                risk_factors: [
                    'Production environment increases risk',
                    'High-impact operation detected: CREATE INDEX...',
                    'Medium-impact operation: UPDATE STATISTICS...'
                ],
                mitigation_strategies: [
                    'Test all changes in staging environment first',
                    'Create database backup before implementation',
                    'Implement changes during maintenance window'
                ]
            },
            workloadAnalysis: {
                workload_type: 'read_heavy',
                query_distribution: { SELECT: 75.5, INSERT: 12.3, UPDATE: 8.7, DELETE: 3.5 },
                complexity_analysis: { average_complexity: 3.2, complexity_distribution: { simple: 45, moderate: 35, complex: 20 } }
            },
            resourceOptimization: {
                recommendations: [
                    'Consider Aurora Read Replicas for read scaling',
                    'Use Aurora Auto Scaling for dynamic management',
                    'Implement connection pooling with RDS Proxy'
                ],
                cost_impact: { estimated_savings: '25%', performance_gain: '35%' }
            },
            patternAnalysis: {
                anti_patterns: [
                    { pattern: 'SELECT *', frequency: 12, recommendation: 'Specify only needed columns' },
                    { pattern: 'Missing WHERE', frequency: 8, recommendation: 'Add WHERE clause to limit rows' }
                ],
                optimization_opportunities: [
                    'Replace subqueries with JOINs in 15 queries',
                    'Add indexes for 8 frequently filtered columns'
                ]
            }
        };

        this.renderQueryPlan(sampleData.queryPlan);
        this.renderPerformanceHeatmap(sampleData.heatmap);
        this.renderRiskAssessment(sampleData.riskAssessment);
        this.renderWorkloadAnalysis(sampleData.workloadAnalysis);
        this.renderResourceOptimization(sampleData.resourceOptimization);
        this.renderPatternAnalysis(sampleData.patternAnalysis);
    }

    renderQueryPlan(data) {
        const container = document.getElementById('query-plan-viz');
        container.innerHTML = '';

        data.nodes.forEach(node => {
            const nodeElement = document.createElement('div');
            nodeElement.className = 'plan-node';
            nodeElement.id = `node-${node.id}`;
            
            // Check if this node is a bottleneck
            const bottleneck = data.bottlenecks.find(b => b.node_id === node.id);
            if (bottleneck) {
                nodeElement.classList.add(bottleneck.severity === 'high' ? 'bottleneck' : 'high-cost');
            }

            nodeElement.innerHTML = `
                <div class="node-header">
                    <strong>${node.operation}</strong>
                    <span class="node-cost">Cost: ${node.cost}</span>
                </div>
                <div class="node-details">
                    <div>Rows: ${node.rows.toLocaleString()}</div>
                    <div>Time: ${node.time}ms</div>
                </div>
                <div class="node-raw">${node.details}</div>
            `;

            nodeElement.addEventListener('click', () => this.showNodeDetails(node, bottleneck));
            container.appendChild(nodeElement);
        });
    }

    renderPerformanceHeatmap(data) {
        const container = document.getElementById('performance-heatmap');
        container.innerHTML = '';

        // Create table heatmap
        const tables = Object.entries(data.tables);
        const maxFrequency = Math.max(...tables.map(([_, table]) => table.frequency));

        tables.forEach(([tableName, tableData]) => {
            const intensity = tableData.frequency / maxFrequency;
            const cell = document.createElement('div');
            cell.className = 'heatmap-cell';
            cell.style.cssText = `
                background: rgba(239, 68, 68, ${intensity});
                color: ${intensity > 0.5 ? 'white' : 'black'};
                padding: 10px;
                margin: 5px;
                border-radius: 6px;
                cursor: pointer;
            `;
            
            cell.innerHTML = `
                <div><strong>${tableName}</strong></div>
                <div>Frequency: ${tableData.frequency}</div>
                <div>Avg Cost: ${tableData.avg_cost}</div>
            `;

            cell.addEventListener('click', () => this.showTableDetails(tableName, tableData));
            container.appendChild(cell);
        });
    }

    renderRiskAssessment(data) {
        const riskLevel = document.getElementById('risk-level');
        const riskFactorsList = document.getElementById('risk-factors-list');
        const mitigationList = document.getElementById('mitigation-list');

        // Set risk level
        riskLevel.className = `risk-level ${data.overall_risk}`;
        riskLevel.querySelector('.risk-score').textContent = data.overall_risk.charAt(0).toUpperCase() + data.overall_risk.slice(1);

        // Populate risk factors
        riskFactorsList.innerHTML = '';
        data.risk_factors.forEach(factor => {
            const li = document.createElement('li');
            li.textContent = factor;
            riskFactorsList.appendChild(li);
        });

        // Populate mitigation strategies
        mitigationList.innerHTML = '';
        data.mitigation_strategies.forEach(strategy => {
            const li = document.createElement('li');
            li.textContent = strategy;
            mitigationList.appendChild(li);
        });
    }

    renderWorkloadAnalysis(data) {
        const workloadType = document.getElementById('workload-type');
        const avgComplexity = document.getElementById('avg-complexity');

        workloadType.textContent = data.workload_type.replace('_', ' ').toUpperCase();
        avgComplexity.textContent = data.complexity_analysis.average_complexity;

        // Create pie chart for query distribution
        const ctx = document.getElementById('workload-distribution').getContext('2d');
        
        if (this.workloadChart) {
            this.workloadChart.destroy();
        }

        this.workloadChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: Object.keys(data.query_distribution),
                datasets: [{
                    data: Object.values(data.query_distribution),
                    backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    renderResourceOptimization(data) {
        const recommendationsContainer = document.getElementById('optimization-recommendations');
        const costSavings = document.getElementById('cost-savings');
        const performanceGain = document.getElementById('performance-gain');

        // Populate recommendations
        recommendationsContainer.innerHTML = '';
        data.recommendations.forEach(rec => {
            const div = document.createElement('div');
            div.className = 'recommendation-item';
            div.innerHTML = `<span>• ${rec}</span>`;
            recommendationsContainer.appendChild(div);
        });

        // Set impact metrics
        costSavings.textContent = data.cost_impact.estimated_savings;
        performanceGain.textContent = data.cost_impact.performance_gain;
    }

    renderPatternAnalysis(data) {
        const antiPatternsContainer = document.getElementById('anti-patterns');
        const optimizationsContainer = document.getElementById('pattern-optimizations');

        // Render anti-patterns
        antiPatternsContainer.innerHTML = '';
        data.anti_patterns.forEach(pattern => {
            const div = document.createElement('div');
            div.className = 'anti-pattern-item';
            div.innerHTML = `
                <div>
                    <strong>${pattern.pattern}</strong>
                    <span class="pattern-frequency">${pattern.frequency} occurrences</span>
                </div>
                <div style="margin-top: 5px; font-size: 14px;">${pattern.recommendation}</div>
            `;
            antiPatternsContainer.appendChild(div);
        });

        // Render optimization opportunities
        optimizationsContainer.innerHTML = '';
        data.optimization_opportunities.forEach(opportunity => {
            const div = document.createElement('div');
            div.className = 'pattern-item';
            div.innerHTML = `<span>• ${opportunity}</span>`;
            optimizationsContainer.appendChild(div);
        });
    }

    setupEventListeners() {
        // Heatmap metric selector
        const heatmapSelect = document.getElementById('heatmap-metric');
        if (heatmapSelect) {
            heatmapSelect.addEventListener('change', (e) => {
                this.updateHeatmapMetric(e.target.value);
            });
        }
    }

    showNodeDetails(node, bottleneck) {
        let details = `Operation: ${node.operation}\nCost: ${node.cost}\nRows: ${node.rows}\nTime: ${node.time}ms`;
        
        if (bottleneck) {
            details += `\n\nIssue: ${bottleneck.issue}\nSeverity: ${bottleneck.severity}`;
        }

        alert(details);
    }

    showTableDetails(tableName, tableData) {
        const details = `Table: ${tableName}\nQuery Frequency: ${tableData.frequency}\nAverage Cost: ${tableData.avg_cost}\nIssues: ${tableData.issues.join(', ') || 'None'}`;
        alert(details);
    }

    updateHeatmapMetric(metric) {
        // Update heatmap based on selected metric
        console.log(`Updating heatmap for metric: ${metric}`);
        // Implementation would update the heatmap visualization
    }
}

// Global functions for plan controls
function expandAll() {
    document.querySelectorAll('.plan-node').forEach(node => {
        node.style.display = 'block';
    });
}

function collapseAll() {
    document.querySelectorAll('.plan-node').forEach(node => {
        if (!node.classList.contains('bottleneck')) {
            node.style.display = 'none';
        }
    });
}

function highlightBottlenecks() {
    document.querySelectorAll('.plan-node').forEach(node => {
        if (node.classList.contains('bottleneck') || node.classList.contains('high-cost')) {
            node.style.border = '3px solid #dc2626';
            node.style.boxShadow = '0 0 10px rgba(220, 38, 38, 0.3)';
        }
    });
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new AnalyticsDashboard();
});