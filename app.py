import streamlit as st
import os
import logging
import uuid
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables (for local testing)
load_dotenv()

# Available Groq models (updated list)
AVAILABLE_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile", 
    "llama-3.2-3b-preview",
    "llama-3.2-1b-preview",
    "llama-3.2-90b-text-preview",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"  # Keeping it but it might not work
]

# Initialize LLM with enhanced settings
def initialize_llm(model_name, temperature, max_tokens):
    try:
        logger.info(f"Initializing LLM: {model_name}")
        groq_api_key = st.secrets.get("GROQ_API_KEY")  # ✅ Correct way for Streamlit secrets

        if not groq_api_key:
            st.error("GROQ_API_KEY not found. Please set it in Streamlit secrets.")
            logger.error("GROQ_API_KEY not found")
            return None

        return ChatGroq(
            groq_api_key=groq_api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            model_kwargs={
                "top_p": 0.9,
                "frequency_penalty": 0.5,
                "presence_penalty": 0.5,
            }
        )
    except Exception as e:
        st.error(f"Error initializing {model_name}: {str(e)}")
        logger.error(f"LLM initialization error for {model_name}: {str(e)}")
        return None

# Enhanced conversation chain setup
def setup_conversation_chain():
    llm = initialize_llm(selected_model, temperature, max_tokens)
    if not llm:
        return

    # System prompt with memory context
    if st.session_state.current_chat_id and st.session_state.chat_sessions.get(st.session_state.current_chat_id):
        chat_history = st.session_state.chat_sessions[st.session_state.current_chat_id]
        history_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-6:]])
    else:
        history_context = "No previous messages"

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are Gynx Ai, Developed By Muhammad Awais Laal, an advanced AI assistant. Provide thorough, detailed responses to user questions.
         Remember the following conversation context:
         {history_context}
         
         Current conversation:
         """),
        ("human", "{question}")
    ])

    try:
        logger.info("Setting up conversation chain")
        st.session_state.conversation = (
            {"question": RunnablePassthrough()}
            | prompt
            | llm
        )
        logger.info("Conversation chain set up successfully")
    except Exception as e:
        st.error(f"Error setting up conversation chain: {str(e)}")
        logger.error(f"Conversation chain setup error: {str(e)}")

# Initialize session state
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "conversation" not in st.session_state:
    st.session_state.conversation = None

# Custom CSS for beautiful chat interface
st.markdown("""
<style>
.chat-container {
    max-width: 800px;
    margin: 0 auto;
}

.chat-message {
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
}

.chat-message.user {
    background-color: #2b313e;
    border-left: 4px solid #ff4b4b;
}

.chat-message.assistant {
    background-color: #1e1e1e;
    border-left: 4px solid #00d4aa;
}

.chat-message .avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    margin-right: 1rem;
}

.chat-message .message {
    flex: 1;
}

.chat-message time {
    font-size: 0.8rem;
    color: #888;
    margin-top: 0.5rem;
}

.developer-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 0.5rem;
    color: white;
    margin-top: 2rem;
}

.developer-card h4 {
    margin: 0 0 1rem 0;
    font-size: 1.2rem;
}

.developer-card p {
    margin: 0.5rem 0;
    font-size: 0.9rem;
    line-height: 1.4;
}

.stButton button {
    width: 100%;
    border-radius: 0.5rem;
}

.stSelectbox div[data-baseweb="select"] {
    border-radius: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# Sidebar settings
with st.sidebar:
    st.title("⚙️ Gynx Ai Settings")

    with st.expander("Model Configuration", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_model = st.selectbox(
                "Model",
                AVAILABLE_MODELS,
                index=0  # Default to llama-3.1-8b-instant
            )
        with col2:
            temperature = st.slider("Creativity", 0.0, 1.0, 0.7, 0.05)

        max_tokens = st.slider("Response Length", 100, 4000, 2000, 100)

    with st.expander("Chat Sessions", expanded=True):
        if st.button("➕ New Chat", use_container_width=True, key="new_chat"):
            new_chat_id = str(uuid.uuid4())
            st.session_state.chat_sessions[new_chat_id] = []
            st.session_state.current_chat_id = new_chat_id
            st.rerun()

        if st.session_state.chat_sessions:
            chat_options = {
                f"💬 Chat {i+1} ({len(chat)} msgs)": chat_id
                for i, (chat_id, chat) in enumerate(st.session_state.chat_sessions.items())
            }
            selected_chat = st.selectbox(
                "Active Chat",
                list(chat_options.keys()),
                index=list(chat_options.values()).index(st.session_state.current_chat_id)
                if st.session_state.current_chat_id in chat_options.values() else 0
            )
            st.session_state.current_chat_id = chat_options[selected_chat]

    st.markdown("""
    <div class="developer-card">
        <h4>About Gynx Ai</h4>
        <p>A cutting-edge AI assistant that delivers natural, context-aware conversations. Maintains dialogue continuity for coherent discussions and provides insightful, well-structured responses.</p>
        <hr>
        <h4>Developer</h4>
        <p>👨‍💻 <strong>Muhammad Awais Laal</strong></p>
        <p>Generative AI Developer</p>
        <p style="font-size:0.8rem; color:#ddd;">Built with Streamlit & LangChain</p>
    </div>
    """, unsafe_allow_html=True)

# Main chat UI
st.title("💬 Gynx Ai Chat")
st.caption("Your intelligent assistant with conversation memory - Ask me anything!")

if st.session_state.current_chat_id and st.session_state.chat_sessions.get(st.session_state.current_chat_id):
    for message in st.session_state.chat_sessions[st.session_state.current_chat_id]:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
            st.markdown(message["content"])
            st.markdown(f"<time>{time.strftime('%H:%M', time.localtime())}</time>", unsafe_allow_html=True)
else:
    st.info("Start a new conversation by typing a message below...")
    st.image("https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80",
             width=600,
             caption="Your AI Assistant Ready to Help")

# Chat input
if prompt := st.chat_input("Type your message here..."):
    if not st.session_state.current_chat_id:
        new_chat_id = str(uuid.uuid4())
        st.session_state.chat_sessions[new_chat_id] = []
        st.session_state.current_chat_id = new_chat_id

    st.session_state.chat_sessions[st.session_state.current_chat_id].append({
        "role": "user",
        "content": prompt,
        "timestamp": time.time()
    })

    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        st.markdown(f"<time>{time.strftime('%H:%M', time.localtime())}</time>", unsafe_allow_html=True)

    if not st.session_state.conversation:
        setup_conversation_chain()

    if st.session_state.conversation:
        try:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    response = st.session_state.conversation.invoke({"question": prompt})
                    answer = response.content

                    response_container = st.empty()
                    full_response = ""
                    for chunk in answer.split():
                        full_response += chunk + " "
                        response_container.markdown(full_response + "▌")
                        time.sleep(0.05)

                    response_container.markdown(full_response)
                    st.markdown(f"<time>{time.strftime('%H:%M', time.localtime())}</time>", unsafe_allow_html=True)

                st.session_state.chat_sessions[st.session_state.current_chat_id].append({
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": time.time()
                })

        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            logger.error(f"Response generation error: {str(e)}")
