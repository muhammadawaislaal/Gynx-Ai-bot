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

# Load environment variables
load_dotenv()

# Initialize LLM with enhanced settings
def initialize_llm(model_name, temperature, max_tokens):
    try:
        logger.info(f"Initializing LLM: {model_name}")
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            st.error("GROQ_API_KEY not found. Please set it in environment variables or .env file.")
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
        ("system", f"""You are Gynx Ai,Developed By Muhammad Awais Laal , an advanced AI assistant. Provide thorough, detailed responses to user questions.
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
/* Main chat container */
.stChatFloatingInputContainer {
    bottom: 20px;
    padding: 0 1rem;
}

/* User message bubble - WhatsApp green style */
[data-testid="stChatMessage-user"] {
    margin-left: auto;
    max-width: 78%;
    border-radius: 18px 18px 0 18px !important;
    background: linear-gradient(135deg, #DCF8C6 0%, #B9F5D0 100%) !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 12px 16px;
    border: none !important;
    color: #000;
}

/* Bot message bubble - light gray with subtle gradient */
[data-testid="stChatMessage-assistant"] {
    margin-right: auto;
    max-width: 78%;
    border-radius: 18px 18px 18px 0 !important;
    background: linear-gradient(135deg, #f0f0f0 0%, #e5e5e5 100%) !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    padding: 12px 16px;
    border: none !important;
    color: #333;
}

/* Message text styling */
.stChatMessage p {
    margin-bottom: 0.4rem;
    line-height: 1.5;
    font-size: 0.95rem;
}

/* Timestamp styling */
.stChatMessage time {
    font-size: 0.7rem;
    color: #666;
    float: right;
    margin-left: 10px;
    margin-top: 4px;
}

/* Avatar styling */
.stChatMessage .stChatAvatar {
    width: 32px !important;
    height: 32px !important;
    font-size: 16px !important;
}

/* Sidebar styling */
.st-emotion-cache-6qob1r {
    background-color: #075E54 !important;
    color: white;
}

/* Button styling */
.stButton>button {
    border: none;
    color: white;
    background: linear-gradient(135deg, #075E54 0%, #128C7E 100%);
    border-radius: 12px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stButton>button:hover {
    background: linear-gradient(135deg, #128C7E 0%, #075E54 100%);
    color: white;
}

/* Title styling */
.stTitle {
    color: #075E54;
    font-weight: 700;
}

/* Spinner styling */
.stSpinner > div {
    margin: 0 auto;
    color: #075E54;
}

/* Developer info card - improved contrast */
.developer-card {
    background-color: #f0f8ff;
    border-radius: 12px;
    padding: 1.2rem;
    margin-top: 2rem;
    border-left: 4px solid #075E54;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.developer-card h4 {
    color: #075E54 !important;
    margin-top: 0;
    font-weight: 600;
}

.developer-card p {
    color: #333 !important;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}

.developer-card hr {
    margin: 0.8rem 0;
    border-color: rgba(0,0,0,0.1);
}

/* Welcome image styling */
.welcome-image {
    border-radius: 12px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* Slider styling */
.stSlider .st-ae {
    background-color: #075E54 !important;
}

/* Selectbox styling */
.stSelectbox .st-ae {
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# Sidebar settings
with st.sidebar:
    st.title("⚙️ Gynx Ai Settings")
    
    # Model settings
    with st.expander("Model Configuration", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_model = st.selectbox(
                "Model", 
                ["llama3-70b-8192", "llama3-8b-8192", "gemma2-9b-it"],
                index=0
            )
        with col2:
            temperature = st.slider("Creativity", 0.0, 1.0, 0.7, 0.05)
        
        max_tokens = st.slider("Response Length", 100, 4000, 2000, 100)
    
    # Chat sessions management
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
    
    # Developer information with improved visibility
    st.markdown("""
    <div class="developer-card">
        <h4>About Gynx Ai</h4>
        <p>A cutting-edge AI assistant that delivers natural, context-aware conversations. Maintains dialogue continuity for coherent discussions and provides insightful, well-structured responses.</p>
        <hr>
        <h4>Developer</h4>
        <p>👨‍💻 <strong>Muhammad Awais Laal</strong></p>
        <p>Generative AI Developer</p>
        <p style="font-size:0.8rem; color:#555;">Built with Streamlit & LangChain</p>
    </div>
    """, unsafe_allow_html=True)

# Main app interface
st.title("💬 Gynx Ai Chat")
st.caption("Your intelligent assistant with conversation memory - Ask me anything!")

# Display chat history with timestamps
if st.session_state.current_chat_id and st.session_state.chat_sessions.get(st.session_state.current_chat_id):
    for message in st.session_state.chat_sessions[st.session_state.current_chat_id]:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
            st.markdown(message["content"])
            st.markdown(f"<time>{time.strftime('%H:%M', time.localtime())}</time>", unsafe_allow_html=True)
else:
    st.info("Start a new conversation by typing a message below...")
    st.image("https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=80", 
             use_container_width=True, 
             caption="Your AI Assistant Ready to Help")

# Chat input with enhanced features
if prompt := st.chat_input("Type your message here..."):
    if not st.session_state.current_chat_id:
        new_chat_id = str(uuid.uuid4())
        st.session_state.chat_sessions[new_chat_id] = []
        st.session_state.current_chat_id = new_chat_id
    
    # Add user message to chat
    st.session_state.chat_sessions[st.session_state.current_chat_id].append({
        "role": "user", 
        "content": prompt,
        "timestamp": time.time()
    })
    
    # Display user message immediately
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        st.markdown(f"<time>{time.strftime('%H:%M', time.localtime())}</time>", unsafe_allow_html=True)
    
    # Initialize conversation if needed
    if not st.session_state.conversation:
        setup_conversation_chain()
    
    # Generate and display response
    if st.session_state.conversation:
        try:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    response = st.session_state.conversation.invoke({"question": prompt})
                    answer = response.content
                    
                    # Stream the response
                    response_container = st.empty()
                    full_response = ""
                    for chunk in answer.split():
                        full_response += chunk + " "
                        response_container.markdown(full_response + "▌")
                        time.sleep(0.05)
                    
                    response_container.markdown(full_response)
                    st.markdown(f"<time>{time.strftime('%H:%M', time.localtime())}</time>", unsafe_allow_html=True)
                
                # Add to chat history
                st.session_state.chat_sessions[st.session_state.current_chat_id].append({
                    "role": "assistant", 
                    "content": full_response,
                    "timestamp": time.time()
                })
                
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            logger.error(f"Response generation error: {str(e)}")
