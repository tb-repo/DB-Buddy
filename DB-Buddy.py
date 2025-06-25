import streamlit as st
from streamlit_chat import message
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory

#system_message="You are a cool and one-stop chatbot as well as buddy for any database enthusiast. Always respond in a professional, technical tone. Consider clarity, specificity, and effectiveness for each response. Adopt a clear, detailed and bullet-point format for responses. If it is going to be a complex technical question, break down it into simpler sub-responses and provide clear explanations. Use a conversational, friendly style appropriate for cool and friendly technical and professional interactions. Always provide your best quality response for any prompt query or discussion. You only answer database specific queries or discussions; for anything else, please respond 'Sorry buddy, I can't answer anything outside database specific topic. Please feel free to ask or chat about any database specific topics with me. I am happy to assist you!' "
# Initialize session state variables
if 'buffer_memory' not in st.session_state:
    system_message="You are a cool and one-stop chatbot as well as buddy for any database enthusiast. Always respond in a professional, technical tone. Consider clarity, specificity, and effectiveness for each response. Adopt a clear, detailed and bullet-point format for responses. If it is going to be a complex technical question, break down it into simpler sub-responses and provide clear explanations. Use a conversational, friendly style appropriate for cool and friendly technical and professional interactions. Always provide your best quality response for any prompt query or discussion. You only answer database specific queries or discussions; for anything else, please respond 'Sorry buddy, I can't answer anything outside database specific topic. Please feel free to ask or chat about any database specific topics with me. I am happy to assist you!' "
# Initialize session state variables
    st.session_state.buffer_memory = ConversationBufferWindowMemory(k=3, return_messages=True)
    
if "messages" not in st.session_state.keys():  # Initialize the chat message history
    st.session_state.messages = [
                {"role": "DB-Assistant", "content": "How can I help you today?"}
    ]
    

# Initialize ChatOpenAI and ConversationChain
llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    openai_api_key=st.secrets["TOGETHER_API_KEY"],  # use your key
    openai_api_base="https://api.together.xyz/v1"
)

conversation = ConversationChain(memory=st.session_state.buffer_memory, llm=llm)

# Create user interface
st.title("🗣️ DB-Buddy: Your Database Chatbot")
st.subheader("A one-stop chatbot for all your database-related conversations.")

if prompt := st.chat_input("Your database question"):  # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "buddy", "content": prompt})

for message in st.session_state.messages:  # Display the prior chat messages
    # Only display messages from user and assistant
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

# If last message is not from DB-Assistant, generate a new response
if st.session_state.messages[-1]["role"] != "DB-Assistant":
    with st.chat_message("DB-Assistant"):
        with st.spinner("Thinking..."):
            response = conversation.predict(input=prompt)
            st.write(response)
            message = {"role": "DB-Assistant", "content": response}
            st.session_state.messages.append(message)  # Add response to message history
