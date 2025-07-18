import streamlit as st
import os
import logging
import uuid
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()  # Load .env if present

# 🔊 Autoplay light bird music
if "music_playing" not in st.session_state:
    st.session_state.music_playing = True

if st.session_state.music_playing:
    st.audio("https://cdn.pixabay.com/download/audio/2022/03/15/audio_5db90e3b18.mp3", autoplay=True)

# Initialize LLM
def initialize_llm(model_name, temperature, max_tokens):
    try:
        groq_api_key = st.secrets.get("GROQ_API_KEY")
        if not groq_api_key:
            st.error("GROQ_API_KEY not set in Streamlit secrets.")
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
        st.error(f"LLM init error: {str(e)}")
        logger.error(str(e))
        return None

# Setup conversation
def setup_conversation_chain():
    llm = initialize_llm(selected_model, temperature, max_tokens)
    if not llm:
        return

    history_context = ""
    if st.session_state.current_chat_id and st.session_state.chat_sessions.get(st.session_state.current_chat_id):
        chat_history = st.session_state.chat_sessions[st.session_state.current_chat_id]
        history_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-6:]])
    else:
        history_context = "No previous messages."

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""
You are Gynx Ai, developed by Muhammad Awais Laal — a helpful, elegant assistant. 
Always respond step-by-step, using numbered or bulleted explanations for clarity. 
Never rush. Ensure responses are easy to follow for beginners.
        
Previous conversation:
{history_context}

Now respond to the current question below.
"""),
        ("human", "{question}")
    ])

    try:
        st.session_state.conversation = (
            {"question": RunnablePassthrough()}
            | prompt
            | llm
        )
    except Exception as e:
        st.error(f"Error in conversation chain: {str(e)}")
        logger.error(str(e))

# Initialize session
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "conversation" not in st.session_state:
    st.session_state.conversation = None

# 💡 Sidebar
with st.sidebar:
    st.title("⚙️ Gynx Ai Settings")

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

    with st.expander("Chat Sessions", expanded=True):
        if st.button("➕ New Chat", use_container_width=True):
            new_chat_id = str(uuid.uuid4())
            st.session_state.chat_sessions[new_chat_id] = []
            st.session_state.current_chat_id = new_chat_id
            st.session_state.conversation = None
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

    if st.button("🔊 Toggle Bird Music"):
        st.session_state.music_playing = not st.session_state.music_playing
        st.rerun()

    st.markdown("""
    <hr>
    <h4>🧠 About Gynx Ai</h4>
    <p>A conversational AI assistant that remembers context and provides beautifully explained answers.</p>
    <p><strong>Developer:</strong> Muhammad Awais Laal</p>
    <p style="font-size:0.85rem;">Built with ❤️ using Streamlit + LangChain + Groq</p>
    """, unsafe_allow_html=True)

# 🧠 Chat UI
st.title("💬 Gynx Ai Chat")
st.caption("Understandable, elegant answers – explained step by step.")

# Display previous messages
if st.session_state.current_chat_id and st.session_state.chat_sessions.get(st.session_state.current_chat_id):
    for msg in st.session_state.chat_sessions[st.session_state.current_chat_id]:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
            st.markdown(f"<time>{time.strftime('%H:%M', time.localtime(msg['timestamp']))}</time>", unsafe_allow_html=True)
else:
    st.info("Start a new chat by typing below ⬇️")

# User input
if prompt := st.chat_input("Ask me anything..."):
    if not st.session_state.current_chat_id:
        new_chat_id = str(uuid.uuid4())
        st.session_state.chat_sessions[new_chat_id] = []
        st.session_state.current_chat_id = new_chat_id

    # Append user message
    st.session_state.chat_sessions[st.session_state.current_chat_id].append({
        "role": "user",
        "content": prompt,
        "timestamp": time.time()
    })

    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Initialize conversation chain
    if not st.session_state.conversation:
        setup_conversation_chain()

    # Generate assistant response
    if st.session_state.conversation:
        try:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Gynx is thinking..."):
                    response = st.session_state.conversation.invoke({"question": prompt})
                    answer = response.content

                    full_response = ""
                    display_area = st.empty()

                    for word in answer.split():
                        full_response += word + " "
                        display_area.markdown(full_response + "▌")
                        time.sleep(0.05)

                    display_area.markdown(full_response)
                    st.session_state.chat_sessions[st.session_state.current_chat_id].append({
                        "role": "assistant",
                        "content": full_response,
                        "timestamp": time.time()
                    })

        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            logger.error(f"Response error: {str(e)}")
