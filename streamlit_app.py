import streamlit as st
import requests
import json
from datetime import datetime
import os
from memory import ConversationMemory

# Get API keys from Streamlit secrets or environment variables
def get_api_key(key_name):
    # Try Streamlit secrets first (for cloud deployment)
    try:
        return st.secrets[key_name]
    except:
        # Fallback to environment variables (for local development)
        return os.getenv(key_name)

# Initialize API keys
GROQ_API_KEY = get_api_key('GROQ_API_KEY')
HUGGINGFACE_API_KEY = get_api_key('HUGGINGFACE_API_KEY')

# Initialize memory
if 'memory' not in st.session_state:
    st.session_state.memory = ConversationMemory('streamlit_conversations.json')

# Set page config
st.set_page_config(
    page_title="DB-Buddy - AI Database Assistant",
    page_icon="🗄️",
    layout="wide"
)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().timestamp()}"
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_issue_type' not in st.session_state:
    st.session_state.current_issue_type = None
if 'show_history' not in st.session_state:
    st.session_state.show_history = False

# Header
st.title("🗄️ DB-Buddy - AI Database Assistant")
st.markdown("Your AI-powered database assistant for instant solutions")

# Sidebar for service selection and history
with st.sidebar:
    st.header("Select Service")
    
    issue_types = {
        'troubleshooting': '🔧 Database Troubleshooting',
        'query': '⚡ Query Optimization', 
        'performance': '📊 Performance Analysis',
        'architecture': '🏗️ Architecture & Design',
        'capacity': '📈 Capacity Planning',
        'security': '🔒 Security & Compliance'
    }
    
    selected_service = st.selectbox(
        "Choose your database assistance:",
        options=list(issue_types.keys()),
        format_func=lambda x: issue_types[x],
        index=0 if st.session_state.current_issue_type is None else list(issue_types.keys()).index(st.session_state.current_issue_type)
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("New Chat"):
            st.session_state.messages = []
            st.session_state.current_issue_type = selected_service
            st.session_state.session_id = f"session_{datetime.now().timestamp()}"
            st.session_state.show_history = False
            st.rerun()
    
    with col2:
        if st.button("History"):
            st.session_state.show_history = not st.session_state.show_history
            st.rerun()
    
    # Show conversation history
    if st.session_state.show_history:
        st.subheader("Past Conversations")
        conversations = st.session_state.memory.get_all_conversations()
        
        if conversations:
            for conv in conversations[:10]:  # Show last 10 conversations
                with st.expander(f"{conv['title']} - {conv['timestamp'][:10]}"):
                    st.write(f"**Preview:** {conv['preview']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Load", key=f"load_{conv['session_id']}"):
                            # Load conversation
                            loaded_conv = st.session_state.memory.get_conversation(conv['session_id'])
                            if loaded_conv:
                                st.session_state.current_issue_type = loaded_conv['data']['type']
                                st.session_state.messages = []
                                # Reconstruct messages from conversation data
                                for i, answer in enumerate(loaded_conv['data']['answers']):
                                    st.session_state.messages.append({"role": "user", "content": answer})
                                st.session_state.show_history = False
                                st.rerun()
                    with col2:
                        if st.button(f"Delete", key=f"del_{conv['session_id']}"):
                            st.session_state.memory.delete_conversation(conv['session_id'])
                            st.rerun()
        else:
            st.write("No past conversations found.")

# LOV Selectors
st.subheader("Quick Setup")
col1, col2, col3, col4 = st.columns(4)

with col1:
    deployment = st.selectbox("Deployment:", ["", "On-Premises", "Cloud", "Hybrid"])

with col2:
    cloud_provider = st.selectbox("Cloud Provider:", 
        ["", "AWS", "Azure", "GCP", "Oracle Cloud", "IBM Cloud"],
        disabled=deployment != "Cloud"
    )

with col3:
    if deployment == "Cloud" and cloud_provider == "AWS":
        db_options = ["", "Amazon RDS MySQL", "Amazon RDS PostgreSQL", "Amazon Aurora MySQL", "Amazon Aurora PostgreSQL", "Amazon DynamoDB"]
    elif deployment == "Cloud" and cloud_provider == "Azure":
        db_options = ["", "Azure Database for MySQL", "Azure Database for PostgreSQL", "Azure SQL Database", "Azure Cosmos DB"]
    else:
        db_options = ["", "MySQL", "PostgreSQL", "SQL Server", "Oracle", "MongoDB", "Redis"]
    
    database = st.selectbox("Database System:", db_options)

with col4:
    environment = st.selectbox("Environment:", ["", "Development", "Staging", "Production"])

if st.button("Insert Selections"):
    if any([deployment, cloud_provider, database, environment]):
        selection_text = ""
        if deployment: selection_text += f"Deployment: {deployment}\n"
        if cloud_provider: selection_text += f"Cloud Provider: {cloud_provider}\n"
        if database: selection_text += f"Database System: {database}\n"
        if environment: selection_text += f"Environment: {environment}\n"
        
        st.session_state.messages.append({"role": "user", "content": selection_text.strip()})
        st.rerun()

# Chat Interface
if not st.session_state.show_history:
    st.subheader("Chat")
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if not st.session_state.show_history:
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Save to memory
        conversation_data = {
            'type': st.session_state.current_issue_type or 'general',
            'answers': [msg['content'] for msg in st.session_state.messages if msg['role'] == 'user'],
            'user_selections': {
                'deployment': deployment,
                'cloud_provider': cloud_provider,
                'database': database,
                'environment': environment
            }
        }
        st.session_state.memory.save_conversation(st.session_state.session_id, conversation_data)
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response (simplified for demo)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if st.session_state.current_issue_type:
                    response = f"""## 🔧 Database Analysis & Recommendations

Based on your {st.session_state.current_issue_type} request:

**🔍 Diagnostic Queries:**
- Check current database configuration
- Review performance metrics
- Analyze query execution plans

**📊 Analysis:**
Your setup appears to be {database if database else 'a standard database'} in {environment if environment else 'an unspecified'} environment.

**⚡ Immediate Actions:**
1. Run diagnostic queries to gather baseline metrics
2. Review current configuration settings
3. Check for obvious performance bottlenecks

**📈 Verification:**
Monitor key performance indicators after implementing changes.

**🛡️ Next Steps:**
Consult with your DBA team for production implementation."""
                else:
                    response = "Please select a service type from the sidebar to get started!"
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# Instructions
with st.expander("How to use DB-Buddy"):
    st.markdown("""
    1. **Select Service**: Choose your database assistance type from the sidebar
    2. **Quick Setup**: Use the dropdowns to specify your database environment
    3. **Insert Selections**: Click to add your configuration to the chat
    4. **Describe Issue**: Type your specific database question or problem
    5. **Get Recommendations**: Receive tailored advice and diagnostic queries
    """)