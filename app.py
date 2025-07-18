import streamlit as st
import os
import uuid
import time
import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# ---------------------- Logger Setup ----------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------------------- Init Session States ----------------------
for key in ["chat_sessions", "current_chat_id", "conversation", "theme", "ratings", "music_playing", "prefill"]:
    if key not in st.session_state:
        st.session_state[key] = {} if key in ["chat_sessions", "ratings"] else None if key == "current_chat_id" else ""

# ---------------------- LLM Setup ----------------------
def initialize_llm(model_name, temperature, max_tokens):
    try:
        groq_api_key = st.secrets["GROQ_API_KEY"]
        return ChatGroq(
            groq_api_key=groq_api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            model_kwargs={"top_p": 0.9, "frequency_penalty": 0.5, "presence_penalty": 0.5}
        )
    except Exception as e:
        logger.error(f"LLM Init Error: {e}")
        st.error("Check your API key in `.streamlit/secrets.toml`")
        return None

def setup_conversation_chain():
    llm = initialize_llm(selected_model, temperature, max_tokens)
    if not llm:
        return

    history_context = ""
    if st.session_state.current_chat_id:
        history = st.session_state.chat_sessions.get(st.session_state.current_chat_id, [])
        history_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-6:]])

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are Gynx Ai by Muhammad Awais Laal. Provide clear, structured, non-paragraph replies using bullet points or sections.
Context: {history_context}"""),
        ("human", "{question}")
    ])

    st.session_state.conversation = (
        {"question": RunnablePassthrough()}
        | prompt
        | llm
    )

# ---------------------- Sidebar ----------------------
with st.sidebar:
    st.title("🎛️ Settings")

    # 🌗 Theme toggle with JS
    theme = st.radio("Theme", ["Light", "Dark"], index=0 if st.session_state.theme != "Dark" else 1)
    if theme != st.session_state.theme:
        st.session_state.theme = theme
        toggle_script = """
            <script>
            document.documentElement.setAttribute('data-theme', '%s');
            </script>
        """ % ('dark' if theme == 'Dark' else 'light')
        st.markdown(toggle_script, unsafe_allow_html=True)

    # 🎵 Music control
    st.subheader("🔊 Background Nature Music")
    music_toggle = st.checkbox("Play Ambient Birdsong", value=True if st.session_state.music_playing else False)
    st.session_state.music_playing = music_toggle

    # ⚙️ Model options
    with st.expander("🧠 Model Settings", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_model = st.selectbox("Model", ["llama3-70b-8192", "llama3-8b-8192", "gemma2-9b-it"])
        with col2:
            temperature = st.slider("Creativity", 0.0, 1.0, 0.7, 0.05)
        max_tokens = st.slider("Max Tokens", 100, 4000, 2000, 100)

    # 💬 Sessions
    with st.expander("💾 Chats", expanded=True):
        if st.button("➕ New Chat", use_container_width=True):
            new_id = str(uuid.uuid4())
            st.session_state.chat_sessions[new_id] = []
            st.session_state.ratings[new_id] = []
            st.session_state.current_chat_id = new_id
            st.rerun()

        if st.session_state.chat_sessions:
            options = {f"Chat {i+1} ({len(msgs)} msgs)": cid for i, (cid, msgs) in enumerate(st.session_state.chat_sessions.items())}
            selected = st.selectbox("Select Chat", list(options.keys()))
            st.session_state.current_chat_id = options[selected]

    # ⭐ Rating system
    if st.session_state.current_chat_id:
        rating = st.slider("Rate This Chat", 1, 5, 3)
        if st.button("Submit Rating"):
            st.session_state.ratings[st.session_state.current_chat_id].append(rating)
            st.success("Thanks for rating!")

    # 📊 Dashboard
    st.markdown("### 📊 Ratings Dashboard")
    for cid, scores in st.session_state.ratings.items():
        avg = round(sum(scores) / len(scores), 2) if scores else 0
        st.write(f"Chat {list(st.session_state.chat_sessions).index(cid)+1}: ⭐ {avg} ({len(scores)} votes)")

    # 👨‍💻 Developer Info
    st.markdown("---")
    st.markdown("""
    <div style='background:#f0f8ff; padding:1rem; border-left:4px solid #075E54; border-radius:10px'>
        <h4 style='color:#075E54;'>Gynx Ai</h4>
        <p>Conversational assistant powered by LLMs & LangChain.</p>
        <p><strong>By:</strong> Muhammad Awais Laal</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------- Music Autoplay (Birdsong) ----------------------
if st.session_state.music_playing:
    st.markdown("""
    <audio autoplay loop>
      <source src="https://cdn.pixabay.com/download/audio/2021/08/04/audio_1f76e568db.mp3?filename=birdsong-in-forest-8435.mp3" type="audio/mpeg">
    </audio>
    """, unsafe_allow_html=True)

# ---------------------- Main Chat ----------------------
st.title("🧠 Gynx Ai Assistant")

# 💡 Suggestions (working now)
suggestions = ["What's AI?", "Top 3 books on success", "Python vs JavaScript", "Meditation benefits"]
st.markdown("##### 💡 Suggestions:")
cols = st.columns(2)
for i in range(2):
    with cols[i]:
        if st.button(suggestions[i]):
            st.session_state.prefill = suggestions[i]
    with cols[i]:
        if st.button(suggestions[i+2]):
            st.session_state.prefill = suggestions[i+2]

# ---------------------- Chat UI ----------------------
if st.session_state.current_chat_id:
    history = st.session_state.chat_sessions[st.session_state.current_chat_id]
    for msg in history:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
else:
    st.info("Start chatting by entering your prompt below.")

# Chat Input
prompt = st.chat_input("Ask anything...", value=st.session_state.prefill if st.session_state.prefill else "")
st.session_state.prefill = ""

if prompt:
    cid = st.session_state.current_chat_id
    if not cid:
        new_id = str(uuid.uuid4())
        st.session_state.chat_sessions[new_id] = []
        st.session_state.ratings[new_id] = []
        st.session_state.current_chat_id = new_id
        cid = new_id

    st.session_state.chat_sessions[cid].append({"role": "user", "content": prompt, "timestamp": time.time()})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    if not st.session_state.conversation:
        setup_conversation_chain()

    if st.session_state.conversation:
        try:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    response = st.session_state.conversation.invoke({"question": prompt})
                    answer = response.content
                    display = st.empty()
                    full_text = ""
                    for word in answer.split():
                        full_text += word + " "
                        display.markdown(full_text + "▌")
                        time.sleep(0.02)
                    display.markdown(full_text)
                    st.session_state.chat_sessions[cid].append({"role": "assistant", "content": full_text, "timestamp": time.time()})
        except Exception as e:
            logger.error(e)
            st.error("Something went wrong.")
