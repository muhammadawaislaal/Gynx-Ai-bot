import streamlit as st
import os
import logging
import uuid
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# ---------------- Setup ---------------- #
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
groq_api_key = st.secrets["GROQ_API_KEY"]

# ---------------- Session State Init ---------------- #
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "music_playing" not in st.session_state:
    st.session_state.music_playing = True
if "rating" not in st.session_state:
    st.session_state.rating = {}
if "prefill" not in st.session_state:
    st.session_state.prefill = ""

# ---------------- Theme ---------------- #
page_bg = "#fff" if st.session_state.theme == "light" else "#1e1e1e"
text_color = "#000" if st.session_state.theme == "light" else "#fff"
st.markdown(f"""
    <style>
        body {{ background-color: {page_bg}; color: {text_color}; }}
        .stApp {{ background-color: {page_bg}; }}
    </style>
""", unsafe_allow_html=True)

# ---------------- Music ---------------- #
if st.session_state.music_playing:
    st.audio("https://cdn.pixabay.com/download/audio/2022/03/15/audio_5db90e3b18.mp3", autoplay=True)

# ---------------- Sidebar ---------------- #
with st.sidebar:
    st.title("⚙️ Gynx Ai Settings")

    # Model Config
    with st.expander("Model Configuration", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_model = st.selectbox("Model", ["llama3-70b-8192", "llama3-8b-8192", "gemma2-9b-it"], index=0)
        with col2:
            temperature = st.slider("Creativity", 0.0, 1.0, 0.7, 0.05)

        max_tokens = st.slider("Response Length", 100, 4000, 2000, 100)

    # Rating System
    with st.expander("⭐ Rate this Chat", expanded=True):
        if st.session_state.current_chat_id:
            rating = st.slider("Your Rating", 1, 5, 3, 1)
            st.session_state.rating[st.session_state.current_chat_id] = rating
            st.write(f"Thanks! You rated this chat: **{rating}/5**")

    # Toggle Music
    if st.button("🔊 Toggle Music"):
        st.session_state.music_playing = not st.session_state.music_playing
        st.rerun()

    # Toggle Theme
    if st.button("🌓 Toggle Theme"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

    # New Chat
    if st.button("➕ New Chat", use_container_width=True, key="new_chat"):
        new_chat_id = str(uuid.uuid4())
        st.session_state.chat_sessions[new_chat_id] = []
        st.session_state.current_chat_id = new_chat_id
        st.session_state.prefill = ""
        st.rerun()

    # Chat Selector
    if st.session_state.chat_sessions:
        chat_options = {f"💬 Chat {i+1} ({len(chat)} msgs)": chat_id
                        for i, (chat_id, chat) in enumerate(st.session_state.chat_sessions.items())}
        selected_chat = st.selectbox("Active Chat", list(chat_options.keys()))
        st.session_state.current_chat_id = chat_options[selected_chat]

    # Developer Info
    st.markdown("""
    <hr>
    <h4>🧠 About Gynx Ai</h4>
    <p>Smart AI assistant developed by <b>Muhammad Awais Laal</b>. Gynx delivers memory-aware, elegant, and natural conversations.</p>
    <p>Built using <b>Streamlit</b>, <b>LangChain</b> and <b>Groq LLM</b>.</p>
    """, unsafe_allow_html=True)

# ---------------- Initialize LLM ---------------- #
def initialize_llm(model_name, temperature, max_tokens):
    try:
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
        return None

# ---------------- Setup Conversation ---------------- #
def setup_conversation_chain():
    llm = initialize_llm(selected_model, temperature, max_tokens)
    if not llm:
        return

    history = ""
    if st.session_state.current_chat_id and st.session_state.chat_sessions.get(st.session_state.current_chat_id):
        chat_history = st.session_state.chat_sessions[st.session_state.current_chat_id]
        history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-6:]])

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"You are Gynx Ai, an assistant created by Muhammad Awais Laal. Previous context:\n{history}\n\nCurrent message:\n"),
        ("human", "{question}")
    ])

    st.session_state.conversation = (
        {"question": RunnablePassthrough()}
        | prompt
        | llm
    )

# ---------------- Chat UI ---------------- #
st.title("💬 Gynx Ai Chat")
st.caption("Your intelligent assistant with memory")

# Suggested Prompts
suggestions = [
    "What are the health benefits of meditation?",
    "Explain how neural networks work",
    "What's the future of AI in education?",
    "Suggest a startup idea for 2025"
]
st.markdown("**💡 Try asking:**")
cols = st.columns(4)
for i in range(4):
    if cols[i].button(suggestions[i]):
        st.session_state.prefill = suggestions[i]
        st.rerun()

# Display Chat
if st.session_state.current_chat_id and st.session_state.chat_sessions.get(st.session_state.current_chat_id):
    for message in st.session_state.chat_sessions[st.session_state.current_chat_id]:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
            st.markdown(message["content"])
            st.markdown(f"<time>{time.strftime('%H:%M', time.localtime(message['timestamp']))}</time>", unsafe_allow_html=True)
else:
    st.info("Start chatting below 👇")

# Input
prompt = st.chat_input("Ask anything...", value=st.session_state.prefill)
st.session_state.prefill = ""  # Reset prefill after used

if prompt:
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

    if not st.session_state.conversation:
        setup_conversation_chain()

    if st.session_state.conversation:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.conversation.invoke({"question": prompt})
                    answer = response.content

                    response_container = st.empty()
                    full_response = ""
                    for chunk in answer.split():
                        full_response += chunk + " "
                        response_container.markdown(full_response + "▌")
                        time.sleep(0.05)

                    response_container.markdown(full_response)
                    st.session_state.chat_sessions[st.session_state.current_chat_id].append({
                        "role": "assistant",
                        "content": full_response,
                        "timestamp": time.time()
                    })
                except Exception as e:
                    st.error(f"Failed to respond: {str(e)}")
