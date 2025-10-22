let sessionId = null;
let currentIssueType = null;
let isTyping = false;
let currentImageData = null;

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

// IDP AI Policy - Data Security Validation
function validateInputSecurity(userInput) {
    const sensitivePatterns = [
        /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,  // Credit card
        /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,  // Email
        /\b\d{3}[\s-]?\d{2}[\s-]?\d{4}\b/g,  // SSN pattern
        /password[\s]*[:=][\s]*[^\s]+/gi,  // Password
        /api[_\s]*key[\s]*[:=][\s]*[^\s]+/gi,  // API key
    ];
    
    for (let pattern of sensitivePatterns) {
        if (pattern.test(userInput)) {
            return false;
        }
    }
    return true;
}

function sendAnswer() {
    const input = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const answer = input.value.trim();
    
    if ((!answer && !currentImageData) || isTyping) return;
    
    // Input validation
    if (answer && answer.length < 3) {
        alert('⚠️ Please enter a meaningful message (at least 3 characters).');
        return;
    }
    
    if (answer && answer.length > 10000) {
        alert('⚠️ Message too long. Please limit to 10,000 characters.');
        return;
    }
    
    // IDP AI Policy - Data Security Check
    if (answer && !validateInputSecurity(answer)) {
        alert('🛡️ IDP AI Policy Violation: Sensitive data detected. Please remove personal, confidential, or sensitive information before proceeding.');
        return;
    }
    
    // Disable input while processing
    input.disabled = true;
    sendBtn.disabled = true;
    
    if (answer) {
        addMessage(answer, 'user');
    }
    
    input.value = '';
    
    showTypingIndicator();
    
    const requestBody = {
        session_id: sessionId,
        answer: answer || 'Image uploaded'
    };
    
    if (currentImageData) {
        requestBody.image_data = currentImageData;
    }
    
    fetch('/answer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
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
        // Re-enable input and reset height
        input.disabled = false;
        sendBtn.disabled = false;
        input.style.height = '50px';
        currentImageData = null; // Clear image data
        clearImagePreview();
        input.focus();
    });
}

function addMessage(text, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    
    // Remove typing indicator if present
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Add IDP AI Policy compliance footer to AI responses
    if (sender === 'bot' && text && !text.startsWith('🏢 **DB-Buddy')) {
        text += '\n\n---\n🛡️ *This response follows IDP\'s SMART AI Golden Rules. Always verify AI outputs for accuracy and relevance before implementation.*';
    }
    
    // Handle markdown-like formatting for better readability
    const formattedText = formatMessageText(text);
    contentDiv.innerHTML = formattedText;
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    
    // Smooth scroll to bottom with delay for better UX
    setTimeout(() => {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

function formatMessageText(text) {
    // Basic formatting for better readability
    let formatted = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
        .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
        .replace(/`(.*?)`/g, '<code>$1</code>') // Inline code
        .replace(/\n/g, '<br>') // Line breaks
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>'); // Code blocks
    
    return formatted;
}

function showTypingIndicator() {
    isTyping = true;
    
    // Create typing indicator dynamically
    const messagesContainer = document.getElementById('chatMessages');
    const existingIndicator = document.getElementById('typingIndicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    const indicator = document.createElement('div');
    indicator.id = 'typingIndicator';
    indicator.className = 'typing-indicator';
    indicator.innerHTML = `
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <span class="typing-text">DB-Buddy is analyzing...</span>
    `;
    
    messagesContainer.appendChild(indicator);
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
}

function hideTypingIndicator() {
    isTyping = false;
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

function handleKeyPress(event) {
    const textarea = event.target;
    
    // Auto-resize textarea with better reset
    textarea.style.height = '50px';
    const newHeight = Math.min(textarea.scrollHeight, 120);
    textarea.style.height = newHeight + 'px';
    
    // Handle Enter key
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendAnswer();
        // Reset textarea height after sending
        setTimeout(() => {
            textarea.style.height = '60px';
        }, 100);
    }
}

function autoResizeTextarea() {
    const textarea = document.getElementById('userInput');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = '50px';
            const newHeight = Math.min(this.scrollHeight, 120);
            this.style.height = newHeight + 'px';
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
        // Trigger resize
        userInput.style.height = '50px';
        const newHeight = Math.min(userInput.scrollHeight, 120);
        userInput.style.height = newHeight + 'px';
        userInput.focus();
    }
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('Please select a valid image file.');
        return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('Image size must be less than 5MB.');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        currentImageData = e.target.result.split(',')[1]; // Remove data URL prefix
        showImagePreview(e.target.result);
        
        // Show upload indicator
        const indicator = document.createElement('div');
        indicator.className = 'image-upload-indicator';
        indicator.innerHTML = '<i class="fas fa-image"></i> Image ready to send';
        
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.appendChild(indicator);
        
        // Scroll to bottom
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    };
    
    reader.readAsDataURL(file);
}

function showImagePreview(imageSrc) {
    const preview = document.createElement('img');
    preview.src = imageSrc;
    preview.className = 'image-preview';
    preview.id = 'currentImagePreview';
    
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.appendChild(preview);
}

function clearImagePreview() {
    const preview = document.getElementById('currentImagePreview');
    if (preview) {
        preview.remove();
    }
    
    const indicators = document.querySelectorAll('.image-upload-indicator');
    indicators.forEach(indicator => indicator.remove());
}

function generateReport() {
    if (!sessionId) {
        alert('No active conversation to generate report for.');
        return;
    }
    
    // Show loading indicator
    const reportBtn = document.querySelector('.report-btn');
    const originalIcon = reportBtn.innerHTML;
    reportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    reportBtn.disabled = true;
    
    // Generate and download report
    fetch(`/generate_report/${sessionId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to generate report');
            }
            return response.blob();
        })
        .then(blob => {
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `db_buddy_report_${sessionId.substring(0, 8)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // Show success message
            addMessage('📄 PDF report generated and downloaded successfully!', 'bot');
        })
        .catch(error => {
            console.error('Error generating report:', error);
            addMessage('Sorry, there was an error generating the PDF report. Please try again.', 'bot');
        })
        .finally(() => {
            // Restore button
            reportBtn.innerHTML = originalIcon;
            reportBtn.disabled = false;
        });
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