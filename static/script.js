let sessionId = null;
let currentIssueType = null;
let isTyping = false;

const issueTypeNames = {
    'troubleshooting': 'Database Troubleshooting',
    'query': 'Query Optimization',
    'performance': 'Performance Analysis',
    'architecture': 'Architecture & Design',
    'capacity': 'Capacity Planning',
    'security': 'Security & Compliance'
};

function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function showHome() {
    const chatInterface = document.getElementById('chatInterface');
    chatInterface.style.display = 'none';
    chatInterface.classList.remove('active');
    document.getElementById('welcomeScreen').style.display = 'block';
    document.getElementById('homeBtn').style.display = 'inline-block';
    document.getElementById('resetBtn').style.display = 'none';
    
    // Clear chat
    document.getElementById('chatMessages').innerHTML = '';
    sessionId = null;
    currentIssueType = null;
}

function startConversation(issueType) {
    console.log('Starting conversation for:', issueType);
    
    sessionId = generateSessionId();
    currentIssueType = issueType;
    currentIssueTypeForSelectors = issueType;
    
    // Update UI
    const welcomeScreen = document.getElementById('welcomeScreen');
    const chatInterface = document.getElementById('chatInterface');
    
    console.log('Hiding welcome screen, showing chat interface');
    welcomeScreen.style.display = 'none';
    chatInterface.style.display = 'flex';
    chatInterface.classList.add('active');
    
    document.getElementById('homeBtn').style.display = 'inline-block';
    document.getElementById('resetBtn').style.display = 'inline-block';
    
    // Update chat title
    document.getElementById('chatTitle').textContent = issueTypeNames[issueType];
    
    // Initialize issue type options
    updateIssueTypeOptions(issueType);
    
    // Show typing indicator
    showTypingIndicator();
    
    fetch('/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: sessionId,
            issue_type: issueType
        })
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        hideTypingIndicator();
        if (data.question) {
            setTimeout(() => addMessage(data.question, 'bot'), 500);
        }
        if (data.ai_status) {
            document.getElementById('aiStatus').textContent = data.ai_status;
        }
    })
    .catch(error => {
        hideTypingIndicator();
        console.error('Error:', error);
        addMessage('Sorry, there was an error starting the conversation. Please try again.', 'bot');
    });
}

function sendAnswer() {
    const input = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const answer = input.value.trim();
    
    if (!answer || isTyping) return;
    
    // Disable input while processing
    input.disabled = true;
    sendBtn.disabled = true;
    
    addMessage(answer, 'user');
    input.value = '';
    
    showTypingIndicator();
    
    fetch('/answer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: sessionId,
            answer: answer
        })
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();
        if (data.response) {
            setTimeout(() => addMessage(data.response, 'bot'), 300);
        }
    })
    .catch(error => {
        hideTypingIndicator();
        console.error('Error:', error);
        addMessage('Sorry, there was an error processing your answer. Please try again.', 'bot');
    })
    .finally(() => {
        // Re-enable input
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
    });
}

function addMessage(text, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    
    // Smooth scroll to bottom
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
}

function showTypingIndicator() {
    isTyping = true;
    const indicator = document.getElementById('typingIndicator');
    indicator.style.display = 'flex';
    
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
}

function hideTypingIndicator() {
    isTyping = false;
    const indicator = document.getElementById('typingIndicator');
    indicator.style.display = 'none';
}

function handleKeyPress(event) {
    const textarea = event.target;
    
    // Auto-resize textarea
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    
    // Handle Enter key
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendAnswer();
    }
}

function autoResizeTextarea() {
    const textarea = document.getElementById('userInput');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 150) + 'px';
        });
    }
}

function resetChat() {
    if (confirm('Are you sure you want to start a new conversation? This will clear the current chat.')) {
        showHome();
    }
}

let currentIssueTypeForSelectors = null;

function toggleQuickSelectors() {
    const selectors = document.getElementById('quickSelectors');
    const isVisible = selectors.style.display !== 'none';
    selectors.style.display = isVisible ? 'none' : 'flex';
    
    if (!isVisible && currentIssueTypeForSelectors) {
        updateIssueTypeOptions(currentIssueTypeForSelectors);
    }
}

function updateCloudProvider() {
    const deployment = document.getElementById('deploymentSelect').value;
    const cloudProviderGroup = document.getElementById('cloudProviderGroup');
    
    if (deployment === 'Cloud' || deployment === 'Hybrid') {
        cloudProviderGroup.style.display = 'block';
    } else {
        cloudProviderGroup.style.display = 'none';
        document.getElementById('cloudProviderSelect').value = '';
    }
    updateDatabaseOptions();
}

function updateDatabaseOptions() {
    const deployment = document.getElementById('deploymentSelect').value;
    const cloudProvider = document.getElementById('cloudProviderSelect').value;
    const dbSystemSelect = document.getElementById('dbSystemSelect');
    
    // Clear existing options
    dbSystemSelect.innerHTML = '<option value="">Select...</option>';
    
    let dbOptions = [];
    
    if (deployment === 'Cloud' && cloudProvider) {
        const cloudDbOptions = {
            'AWS': [
                'Amazon RDS MySQL', 'Amazon RDS PostgreSQL', 'Amazon RDS SQL Server',
                'Amazon Aurora MySQL', 'Amazon Aurora PostgreSQL', 'Amazon DynamoDB',
                'Amazon DocumentDB', 'Amazon ElastiCache Redis', 'Amazon Redshift'
            ],
            'Azure': [
                'Azure Database for MySQL', 'Azure Database for PostgreSQL',
                'Azure SQL Database', 'Azure SQL Managed Instance', 'Azure Cosmos DB',
                'Azure Cache for Redis', 'Azure Synapse Analytics'
            ],
            'GCP': [
                'Cloud SQL MySQL', 'Cloud SQL PostgreSQL', 'Cloud SQL SQL Server',
                'Cloud Spanner', 'Firestore', 'Cloud Bigtable', 'Cloud Memorystore Redis'
            ],
            'Oracle Cloud': [
                'Oracle Autonomous Database', 'Oracle Database', 'MySQL HeatWave',
                'Oracle NoSQL Database'
            ],
            'IBM Cloud': [
                'IBM Db2', 'IBM Cloudant', 'IBM Databases for PostgreSQL', 'IBM Databases for MySQL'
            ]
        };
        dbOptions = cloudDbOptions[cloudProvider] || [];
    } else {
        // On-premises or no cloud provider selected
        dbOptions = [
            'MySQL', 'PostgreSQL', 'SQL Server', 'Oracle',
            'MongoDB', 'Redis', 'MariaDB', 'Cassandra'
        ];
    }
    
    dbOptions.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        dbSystemSelect.appendChild(optionElement);
    });
}

function updateIssueTypeOptions(issueType) {
    const issueTypeSelect = document.getElementById('issueTypeSelect');
    const deployment = document.getElementById('deploymentSelect').value;
    const cloudProvider = document.getElementById('cloudProviderSelect').value;
    
    // Clear existing options
    issueTypeSelect.innerHTML = '<option value="">Select...</option>';
    
    let issueOptions = {};
    
    if (deployment === 'Cloud') {
        // Cloud-specific issues
        issueOptions = {
            'troubleshooting': [
                'Connection timeout', 'Service unavailable', 'Scaling issues', 'Backup failures',
                'Cross-region latency', 'Service limits exceeded', 'Authentication errors'
            ],
            'query': [
                'Slow cloud queries', 'Cross-AZ latency', 'Serverless cold starts',
                'Read replica lag', 'Connection pooling issues'
            ],
            'performance': [
                'Auto-scaling not working', 'IOPS limits', 'Compute unit exhaustion',
                'Network bandwidth limits', 'Storage performance issues'
            ],
            'architecture': [
                'Multi-region setup', 'Disaster recovery', 'High availability',
                'Microservices data strategy', 'Cloud migration planning'
            ],
            'capacity': [
                'Auto-scaling configuration', 'Reserved capacity planning', 'Cost optimization',
                'Multi-region capacity', 'Serverless scaling limits'
            ],
            'security': [
                'IAM configuration', 'VPC security', 'Encryption at rest/transit',
                'Compliance auditing', 'Key management', 'Network security groups'
            ]
        };
    } else {
        // On-premises issues
        issueOptions = {
            'troubleshooting': [
                'Slow queries', 'Connection errors', 'Database crashes', 'Data corruption',
                'Timeout issues', 'Lock contention', 'Replication issues'
            ],
            'query': [
                'Slow SELECT query', 'Complex JOIN performance', 'INSERT bottleneck',
                'UPDATE timeout', 'DELETE taking too long', 'Query optimization needed'
            ],
            'performance': [
                'High CPU usage', 'Memory issues', 'I/O bottleneck', 'Slow response times',
                'Connection pool exhaustion', 'Disk space issues'
            ],
            'architecture': [
                'New system design', 'Migration planning', 'Scaling strategy',
                'High availability setup', 'Disaster recovery', 'Hardware planning'
            ],
            'capacity': [
                'Hardware sizing', 'Storage planning', 'Performance scaling',
                'User load planning', 'Growth projection', 'Infrastructure costs'
            ],
            'security': [
                'Access control setup', 'Encryption implementation', 'Audit configuration',
                'Compliance requirements', 'Vulnerability assessment', 'Backup security'
            ]
        };
    }
    
    if (issueOptions[issueType]) {
        issueOptions[issueType].forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            issueTypeSelect.appendChild(optionElement);
        });
    }
}

function insertSelections() {
    const deployment = document.getElementById('deploymentSelect').value;
    const cloudProvider = document.getElementById('cloudProviderSelect').value;
    const dbSystem = document.getElementById('dbSystemSelect').value;
    const issueType = document.getElementById('issueTypeSelect').value;
    const environment = document.getElementById('environmentSelect').value;
    const userInput = document.getElementById('userInput');
    
    let insertText = '';
    if (deployment) insertText += `Deployment: ${deployment}\n`;
    if (cloudProvider) insertText += `Cloud Provider: ${cloudProvider}\n`;
    if (dbSystem) insertText += `Database: ${dbSystem}\n`;
    if (issueType) insertText += `Issue: ${issueType}\n`;
    if (environment) insertText += `Environment: ${environment}\n`;
    
    if (insertText) {
        const currentText = userInput.value;
        userInput.value = insertText + (currentText ? '\n' + currentText : '');
        autoResizeTextarea();
        userInput.focus();
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Setup textarea auto-resize
    autoResizeTextarea();
    
    // Focus on input when chat is active
    const userInput = document.getElementById('userInput');
    if (userInput) {
        userInput.addEventListener('focus', function() {
            this.style.borderColor = 'var(--primary-color)';
        });
        
        userInput.addEventListener('blur', function() {
            this.style.borderColor = 'var(--border-color)';
        });
    }
    
    // Add welcome message animation
    setTimeout(() => {
        document.body.classList.add('loaded');
    }, 100);
});