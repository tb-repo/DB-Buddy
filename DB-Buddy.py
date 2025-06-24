import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory

# Initialize session state variables
if 'buffer_memory' not in st.session_state:
    st.session_state.buffer_memory = ConversationBufferWindowMemory(k=3, return_messages=True)

if "messages" not in st.session_state.keys():  # Initialize the chat message history
    st.session_state.messages = [
        SystemMessage(content=(
            "You are a cool and one-stop chatbot for any database enthusiast. "
            "You only answer database-specific queries or discussions; for anything else, please respond "
            "'Sorry buddy, I can't answer anything outside database-specific topics. Please feel free to ask or chat about any database-specific topics with me. I am happy to assist you!' "
            "Write in a professional, technical tone suitable for enterprise documentation. "
            "Use a conversational, friendly style appropriate for cool and friendly technical and professional interactions. "
            "Adopt a clear, detailed, and bullet-point format for responses. "
            "Consider clarity, specificity, and effectiveness for each response. "
            "If it is going to be a complex technical question, break it down into simpler sub-responses and provide clear explanations. "
            "Always provide your best quality response for any prompt query or discussion."
        )),
        AIMessage(content="How can I help you today?")
    ]

# Initialize ChatOpenAI and ConversationChain
llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    openai_api_key=st.secrets["TOGETHER_API_KEY"],  # Use your actual API key
    openai_api_base="https://api.together.xyz/v1"
)

conversation = ConversationChain(memory=st.session_state.buffer_memory, llm=llm)

# Create user interface
st.title("🗣️ DB-Buddy: Your Database Chatbot")
st.subheader("A one-stop chatbot for all your database-related conversations.")

if prompt := st.chat_input("Your database question"):  # Prompt for user input and save to chat history
    st.session_state.messages.append(HumanMessage(content=prompt))

    # Check if the prompt is related to databases
    if "database" in prompt.lower() or "sql" in prompt.lower() or "db" in prompt.lower():
        # Generate response if the question is relevant
        for message in st.session_state.messages:  # Display the prior chat messages
            if isinstance(message, (HumanMessage, AIMessage)):
                with st.chat_message(message.role):
                    st.write(message.content)

        # If last message is not from AI, generate a new response
        if not isinstance(st.session_state.messages[-1], AIMessage):
            with st.chat_message("AI"):
                with st.spinner("Thinking..."):
                    response = conversation.predict(input=prompt)
                    st.write(response)
                    st.session_state.messages.append(AIMessage(content=response))  # Add response to message history
    else:
        # Respond with a message indicating the topic is out of scope
        with st.chat_message("AI"):
            response = ("Sorry buddy, I can't answer anything outside database-specific topics. "
                        "Please feel free to ask or chat about any database-specific topics with me. "
                        "I am happy to assist you!")
            st.write(response)
            st.session_state.messages.append(AIMessage(content=response))  # Add response to message history
