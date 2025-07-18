import streamlit as st
import os
import logging
import uuid
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# ---------------------- Logging Setup ----------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------------- LLM Initialization ----------------------
def initialize_llm(model_name, temperature, max_tokens):
    try:
        logger.info(f"Initializing LLM: {model_name}")
        groq_api_key = st.secrets["GROQ_API_KEY"]  # Secure from secrets
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
        logger.error(f"LLM init error: {e}")
        st.error("API Key error. Check your `secrets.toml`.")

# ---------------------- Conversation Chain ----------------------
def setup_conversation_chain():
    llm = initialize_llm(selected_model, temperature, max_tokens)
    if not llm: return

    history_context = ""
    if st.session_state.current_chat_id:
        history = st.session_state.chat_sessions.get(st.session_state.current_chat_id, [])
        history_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-6:]])

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are Gynx Ai by Muhammad Awais Laal. Answer concisely using sections, lists, or bullet points.
Context: {history_context}"""),
        ("human", "{question}")
    ])

    st.session_state.conversation = (
        {"question": RunnablePassthrough()}
        | prompt
        | llm
    )

# ---------------------- Session State Setup ----------------------
for key in ["chat_sessions", "current_chat_id", "conversation", "theme", "ratings"]:
    if key not in st.session_state:
        st.session_state[key] = {} if key in ["chat_sessions", "ratings"] else None

# ---------------------- Sidebar ----------------------
with st.sidebar:
    st.title("⚙️ Gynx Ai Settings")

    # 🌗 Theme Toggle
    theme = st.radio("Choose Theme", ["Light", "Dark"], index=0)
    st.session_state.theme = theme
    if theme == "Dark":
        st.markdown('<style>body{background-color:#1e1e1e;color:white;}</style>', unsafe_allow_html=True)

    # ⚙️ Model Config
    with st.expander("Model Configuration", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_model = st.selectbox("Model", ["llama3-70b-8192", "llama3-8b-8192", "gemma2-9b-it"], index=0)
        with col2:
            temperature = st.slider("Creativity", 0.0, 1.0, 0.7, 0.05)
        max_tokens = st.slider("Response Length", 100, 4000, 2000, 100)

    # 💬 Chat Sessions
    with st.expander("Chat Sessions", expanded=True):
        if st.button("➕ New Chat", use_container_width=True):
            new_id = str(uuid.uuid4())
            st.session_state.chat_sessions[new_id] = []
            st.session_state.ratings[new_id] = []
            st.session_state.current_chat_id = new_id
            st.rerun()

        if st.session_state.chat_sessions:
            options = {f"💬 Chat {i+1} ({len(chat)} msgs)": cid for i, (cid, chat) in enumerate(st.session_state.chat_sessions.items())}
            selected = st.selectbox("Active Chat", list(options.keys()))
            st.session_state.current_chat_id = options[selected]

    # ⭐ Chat Rating System
    if st.session_state.current_chat_id:
        rating = st.slider("Rate this Chat", 1, 5, 3)
        if st.button("Submit Rating"):
            st.session_state.ratings[st.session_state.current_chat_id].append(rating)
            st.success("Rating submitted!")

    # 📊 Rating Dashboard
    st.markdown("---")
    st.markdown("### 📈 Rating Dashboard")
    if st.session_state.ratings:
        for chat_id, ratings in st.session_state.ratings.items():
            avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0
            st.write(f"Chat {list(st.session_state.chat_sessions.keys()).index(chat_id)+1}: ⭐ {avg_rating} ({len(ratings)} votes)")

    # 👨‍💻 Developer Info
    st.markdown("""
    <div style='background:#f0f8ff; padding:1rem; border-left:4px solid #075E54; border-radius:10px'>
        <h4 style='color:#075E54;'>Gynx Ai</h4>
        <p>Intelligent, memory-based assistant with LangChain & Streamlit.</p>
        <p><strong>Developer:</strong> Muhammad Awais Laal</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------- Main UI ----------------------
st.title("💬 Gynx Ai Chat")
st.caption("Ask anything — Gynx Ai replies in clean sections.")

# 🎵 Background Nature Music (relaxing ambient)
st.markdown("""
<audio autoplay loop>
  <source src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3" type="audio/mpeg">
</audio>
""", unsafe_allow_html=True)

# Chat History
if st.session_state.current_chat_id:
    history = st.session_state.chat_sessions.get(st.session_state.current_chat_id, [])
    for msg in history:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
            st.markdown(f"<time>{time.strftime('%H:%M', time.localtime(msg['timestamp']))}</time>", unsafe_allow_html=True)
else:
    st.image("https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=600&q=80", use_container_width=True)
    st.info("Start chatting below to activate your AI session.")

# 🔍 Suggestions
suggestions = ["What’s the weather in Tokyo?", "Summarize a blog post", "Give me startup ideas", "How to learn Python?"]
st.markdown("##### 💡 Suggestions:")
col1, col2 = st.columns(2)
for i in range(2):
    with col1:
        if st.button(suggestions[i]):
            st.query_params(prompt=suggestions[i])
    with col2:
        if st.button(suggestions[i+2]):
            st.query_params(prompt=suggestions[i+2])

# 📝 Chat Input
prompt = st.chat_input("Ask Gynx Ai something...")
if prompt:
    chat_id = st.session_state.current_chat_id
    if not chat_id:
        new_id = str(uuid.uuid4())
        st.session_state.chat_sessions[new_id] = []
        st.session_state.ratings[new_id] = []
        st.session_state.current_chat_id = new_id
        chat_id = new_id

    st.session_state.chat_sessions[chat_id].append({
        "role": "user", "content": prompt, "timestamp": time.time()
    })

    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        st.markdown(f"<time>{time.strftime('%H:%M')}</time>", unsafe_allow_html=True)

    if not st.session_state.conversation:
        setup_conversation_chain()

    # AI Response
    if st.session_state.conversation:
        try:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    response = st.session_state.conversation.invoke({"question": prompt})
                    reply = response.content
                    response_container = st.empty()
                    full = ""
                    for word in reply.split():
                        full += word + " "
                        response_container.markdown(full + "▌")
                        time.sleep(0.03)
                    response_container.markdown(full)
                    st.markdown(f"<time>{time.strftime('%H:%M')}</time>", unsafe_allow_html=True)

                st.session_state.chat_sessions[chat_id].append({
                    "role": "assistant", "content": full, "timestamp": time.time()
                })

        except Exception as e:
            st.error(f"Error: {e}")
            logger.error(f"Response error: {e}")
