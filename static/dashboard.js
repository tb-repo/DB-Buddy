// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    setupEventListeners();
    loadDashboardData();
});

function initializeCharts() {
    // Performance Trends Chart
    const perfCtx = document.getElementById('performanceChart').getContext('2d');
    new Chart(perfCtx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Query Performance (%)',
                data: [75, 82, 78, 85, 88, 92, 85],
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'System Health (%)',
                data: [80, 85, 83, 87, 90, 94, 92],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // Query Time Distribution Chart
    const queryCtx = document.getElementById('queryTimeChart').getContext('2d');
    new Chart(queryCtx, {
        type: 'doughnut',
        data: {
            labels: ['< 100ms', '100ms - 1s', '1s - 5s', '> 5s'],
            datasets: [{
                data: [65, 25, 8, 2],
                backgroundColor: [
                    '#10b981',
                    '#f59e0b',
                    '#ef4444',
                    '#7c2d12'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });
}

function setupEventListeners() {
    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', function() {
        loadDashboardData();
        showNotification('Dashboard refreshed!', 'success');
    });

    // Query analyzer
    document.getElementById('analyzeBtn').addEventListener('click', function() {
        analyzeQuery();
    });

    // Auto-refresh every 30 seconds
    setInterval(loadDashboardData, 30000);
}

function loadDashboardData() {
    // Simulate real-time data updates
    updateMetrics();
    updateProblemAreas();
}

function updateMetrics() {
    // Simulate dynamic metric updates
    const metrics = {
        queryPerf: Math.floor(Math.random() * 20) + 80,
        systemHealth: Math.floor(Math.random() * 15) + 85,
        activeSessions: Math.floor(Math.random() * 30) + 15,
        issuesCount: Math.floor(Math.random() * 5) + 1
    };

    document.getElementById('queryPerf').textContent = metrics.queryPerf + '%';
    document.getElementById('systemHealth').textContent = metrics.systemHealth + '%';
    document.getElementById('activeSessions').textContent = metrics.activeSessions;
    document.getElementById('issuesCount').textContent = metrics.issuesCount;
}

function updateProblemAreas() {
    // This would typically fetch real data from the backend
    console.log('Problem areas updated');
}

function analyzeQuery() {
    const query = document.getElementById('queryInput').value.trim();
    const resultDiv = document.getElementById('planResult');
    
    if (!query) {
        showNotification('Please enter a SQL query to analyze', 'error');
        return;
    }

    // Show loading state
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<div class="loading">🔄 Analyzing query...</div>';

    // Simulate query analysis
    setTimeout(() => {
        const analysis = generateQueryAnalysis(query);
        resultDiv.innerHTML = analysis;
    }, 2000);
}

function generateQueryAnalysis(query) {
    const queryLower = query.toLowerCase();
    let analysis = '<h4>📊 Query Analysis Results</h4>';
    
    // Basic query analysis
    if (queryLower.includes('select')) {
        analysis += '<div class="analysis-item"><strong>Query Type:</strong> SELECT</div>';
        
        if (queryLower.includes('where')) {
            analysis += '<div class="analysis-item good">✅ <strong>WHERE clause detected:</strong> Good for performance</div>';
        } else {
            analysis += '<div class="analysis-item warning">⚠️ <strong>No WHERE clause:</strong> Consider adding filters</div>';
        }
        
        if (queryLower.includes('order by')) {
            analysis += '<div class="analysis-item warning">⚠️ <strong>ORDER BY detected:</strong> Ensure proper indexing</div>';
        }
        
        if (queryLower.includes('*')) {
            analysis += '<div class="analysis-item warning">⚠️ <strong>SELECT * detected:</strong> Consider selecting specific columns</div>';
        }
        
        if (queryLower.includes('join')) {
            analysis += '<div class="analysis-item info">ℹ️ <strong>JOIN detected:</strong> Ensure join columns are indexed</div>';
        }
    }
    
    // Recommendations
    analysis += '<h5>💡 Recommendations:</h5>';
    analysis += '<ul>';
    analysis += '<li>Add indexes on WHERE clause columns</li>';
    analysis += '<li>Consider using LIMIT for large result sets</li>';
    analysis += '<li>Use EXPLAIN ANALYZE to get detailed execution plan</li>';
    analysis += '</ul>';
    
    // Sample EXPLAIN command
    analysis += '<h5>🔍 Run this for detailed analysis:</h5>';
    analysis += `<code>EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) ${query};</code>`;
    
    return analysis;
}

function runDiagnostic(type) {
    const resultDiv = document.getElementById('diagnosticResult');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<div class="loading">🔄 Running diagnostic...</div>';
    
    setTimeout(() => {
        const diagnostic = generateDiagnostic(type);
        resultDiv.innerHTML = diagnostic;
    }, 1500);
}

function generateDiagnostic(type) {
    const diagnostics = {
        connections: `
            <h4>🔗 Connection Health Report</h4>
            <div class="diagnostic-item good">✅ Active Connections: 24/100</div>
            <div class="diagnostic-item good">✅ Connection Pool: Healthy</div>
            <div class="diagnostic-item warning">⚠️ Idle Connections: 8 (consider timeout)</div>
            <h5>Recommended Actions:</h5>
            <code>SELECT count(*) FROM pg_stat_activity WHERE state = 'active';</code>
        `,
        performance: `
            <h4>⚡ Performance Monitor</h4>
            <div class="diagnostic-item good">✅ CPU Usage: 65%</div>
            <div class="diagnostic-item warning">⚠️ Memory Usage: 85%</div>
            <div class="diagnostic-item good">✅ Disk I/O: Normal</div>
            <h5>Recommended Actions:</h5>
            <code>SELECT * FROM pg_stat_activity WHERE query_start < now() - interval '5 minutes';</code>
        `,
        locks: `
            <h4>🔒 Lock Analysis</h4>
            <div class="diagnostic-item good">✅ No blocking locks detected</div>
            <div class="diagnostic-item info">ℹ️ 3 shared locks active</div>
            <div class="diagnostic-item good">✅ Lock wait time: < 1ms</div>
            <h5>Recommended Actions:</h5>
            <code>SELECT * FROM pg_locks WHERE NOT granted;</code>
        `,
        indexes: `
            <h4>📊 Index Usage Analysis</h4>
            <div class="diagnostic-item warning">⚠️ 2 unused indexes found</div>
            <div class="diagnostic-item error">❌ Missing index on users.email</div>
            <div class="diagnostic-item good">✅ Primary indexes: Efficient</div>
            <h5>Recommended Actions:</h5>
            <code>CREATE INDEX CONCURRENTLY idx_users_email ON users(email);</code>
        `
    };
    
    return diagnostics[type] || '<div>Diagnostic not available</div>';
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    
    if (type === 'success') notification.style.background = '#10b981';
    else if (type === 'error') notification.style.background = '#ef4444';
    else notification.style.background = '#3b82f6';
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .loading {
        text-align: center;
        padding: 20px;
        color: #6b7280;
    }
    
    .analysis-item, .diagnostic-item {
        padding: 8px 12px;
        margin: 8px 0;
        border-radius: 6px;
        border-left: 4px solid;
    }
    
    .analysis-item.good, .diagnostic-item.good {
        background: #f0fdf4;
        border-left-color: #10b981;
        color: #065f46;
    }
    
    .analysis-item.warning, .diagnostic-item.warning {
        background: #fffbeb;
        border-left-color: #f59e0b;
        color: #92400e;
    }
    
    .analysis-item.error, .diagnostic-item.error {
        background: #fef2f2;
        border-left-color: #ef4444;
        color: #991b1b;
    }
    
    .analysis-item.info, .diagnostic-item.info {
        background: #f0f9ff;
        border-left-color: #3b82f6;
        color: #1e40af;
    }
`;
document.head.appendChild(style);