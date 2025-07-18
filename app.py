import streamlit as st
import os
import logging
import uuid
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "music_playing" not in st.session_state:
    st.session_state.music_playing = True
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Sidebar
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

    if st.button("🌓 Toggle Theme"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

    if st.button("🔊 Toggle Bird Music"):
        st.session_state.music_playing = not st.session_state.music_playing
        st.rerun()

    with st.expander("Chat Sessions", expanded=True):
        if st.button("➕ New Chat"):
            new_chat_id = str(uuid.uuid4())
            st.session_state.chat_sessions[new_chat_id] = []
            st.session_state.current_chat_id = new_chat_id
            st.rerun()
        if st.session_state.chat_sessions:
            chat_options = {
                f"💬 Chat {i+1} ({len(chat)} msgs)": cid
                for i, (cid, chat) in enumerate(st.session_state.chat_sessions.items())
            }
            selected_chat = st.selectbox(
                "Active Chat",
                list(chat_options.keys()),
                index=list(chat_options.values()).index(st.session_state.current_chat_id)
                if st.session_state.current_chat_id in chat_options.values() else 0
            )
            st.session_state.current_chat_id = chat_options[selected_chat]

    st.markdown("### 🧠 Rate This Bot")
    st.slider("Overall Rating", 1, 5, 4)

    st.markdown("""
    <hr>
    <h4>About Gynx Ai</h4>
    <p>A conversational assistant built using Groq + LangChain + Streamlit. It retains memory context and delivers step-by-step responses.</p>
    <h4>👨‍💻 Developer</h4>
    <p><strong>Muhammad Awais Laal</strong><br>Generative AI Engineer</p>
    """, unsafe_allow_html=True)

# Music Player
bird_audio_url = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_5db90e3b18.mp3"

if st.session_state.music_playing:
    st.markdown(f"""
        <audio id="birdsong" autoplay loop>
            <source src="{bird_audio_url}" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
        <script>
        const audio = document.getElementById("birdsong");
        document.addEventListener('click', () => {{
            if (audio.paused) {{
                audio.play();
            }}
        }});
        </script>
    """, unsafe_allow_html=True)

# Set theme
if st.session_state.theme == "dark":
    st.markdown(
        """<style>
        body { background-color: #1e1e1e; color: white; }
        </style>""",
        unsafe_allow_html=True
    )

# App Title
st.title("💬 Gynx Ai Chat")
st.caption("Your intelligent assistant with memory – ask anything!")

# Initialize LLM
def initialize_llm(model_name, temperature, max_tokens):
    try:
        api_key = st.secrets["GROQ_API_KEY"]
        return ChatGroq(
            groq_api_key=api_key,
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
        st.error(f"LLM Error: {str(e)}")
        return None

# Conversation Chain
def setup_conversation_chain():
    llm = initialize_llm(selected_model, temperature, max_tokens)
    if not llm:
        return
    history = st.session_state.chat_sessions.get(st.session_state.current_chat_id, [])
    context = "\n".join([f"{m['role']}: {m['content']}" for m in history[-5:]])
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are Gynx Ai, developed by Muhammad Awais Laal. Answer clearly, break down complex info step by step:
        Previous conversation:
        {context}
        """),
        ("human", "{question}")
    ])
    st.session_state.conversation = (
        {"question": RunnablePassthrough()} | prompt | llm
    )

# Display chat history
if st.session_state.current_chat_id:
    history = st.session_state.chat_sessions[st.session_state.current_chat_id]
    for msg in history:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

else:
    st.info("Start a new conversation by typing below.")

# Chat input
if prompt := st.chat_input("Ask anything..."):
    if not st.session_state.current_chat_id:
        new_id = str(uuid.uuid4())
        st.session_state.chat_sessions[new_id] = []
        st.session_state.current_chat_id = new_id

    st.session_state.chat_sessions[st.session_state.current_chat_id].append({
        "role": "user",
        "content": prompt,
        "timestamp": time.time()
    })
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    if not st.session_state.conversation:
        setup_conversation_chain()

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.conversation.invoke({"question": prompt})
                answer = response.content

                # Step-by-step typing animation
                response_container = st.empty()
                final_output = ""
                for word in answer.split():
                    final_output += word + " "
                    response_container.markdown(final_output + "▌")
                    time.sleep(0.04)
                response_container.markdown(final_output)

                st.session_state.chat_sessions[st.session_state.current_chat_id].append({
                    "role": "assistant",
                    "content": final_output,
                    "timestamp": time.time()
                })

            except Exception as e:
                st.error("Error generating response.")
                logger.exception(e)
