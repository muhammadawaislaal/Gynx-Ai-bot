import streamlit as st
import os
import logging
import uuid
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PIL import Image
import pytesseract
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Remove hardcoded Tesseract path for Streamlit Cloud
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Cache embeddings
@st.cache_resource
def get_embeddings():
    try:
        logger.info("Initializing HuggingFace embeddings")
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    except Exception as e:
        st.error(f"Failed to initialize embeddings: {str(e)}")
        logger.error(f"Embedding initialization error: {str(e)}")
        return None

# Initialize LLM
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
            max_tokens=max_tokens
        )
    except Exception as e:
        st.error(f"Error initializing {model_name}: {str(e)}")
        logger.error(f"LLM initialization error for {model_name}: {str(e)}")
        return None

# Process uploaded files
def process_files(uploaded_files):
    try:
        logger.info("Processing uploaded files")
        documents = []
        for uploaded_file in uploaded_files:
            file_ext = uploaded_file.name.split('.')[-1].lower()
            temp_file_path = f"temp_{uuid.uuid4()}.{file_ext}"
            
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            if file_ext == "pdf":
                loader = PyPDFLoader(temp_file_path)
                docs = loader.load()
                documents.extend(docs)
            elif file_ext in ["txt"]:
                loader = TextLoader(temp_file_path)
                docs = loader.load()
                documents.extend(docs)
            elif file_ext in ["png", "jpg", "jpeg"]:
                try:
                    image = Image.open(temp_file_path)
                    text = pytesseract.image_to_string(image)
                    if not text.strip():
                        st.sidebar.warning(f"No text extracted from image {uploaded_file.name}")
                        logger.warning(f"No text extracted from {uploaded_file.name}")
                        continue
                    documents.append({"page_content": text, "metadata": {"source": uploaded_file.name}})
                except Exception as e:
                    st.sidebar.error(f"Error processing image {uploaded_file.name}: {str(e)}")
                    logger.error(f"Image processing error for {uploaded_file.name}: {str(e)}")
            
            os.remove(temp_file_path)
        
        if not documents:
            st.sidebar.error("No valid documents or text extracted from uploaded files.")
            logger.error("No documents processed")
            return False
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        
        embeddings = get_embeddings()
        if not embeddings:
            return False
            
        if st.session_state.vectorstore:
            st.session_state.vectorstore.add_documents(splits)
        else:
            st.session_state.vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=embeddings,
                persist_directory="./chroma_db"
            )
        logger.info("Files processed successfully")
        return True
    except Exception as e:
        st.sidebar.error(f"Error processing files: {str(e)}")
        logger.error(f"File processing error: {str(e)}")
        return False

# Initialize conversation chain
def setup_conversation_chain():
    llm = initialize_llm(selected_model, temperature, max_tokens)
    if not llm:
        return
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are GenixAI, a helpful assistant. Use the following context and chat history to answer the question. If no context is provided, use your general knowledge.\n\nContext: {context}\n\nChat History: {chat_history}"),
        ("human", "{question}")
    ])
    
    try:
        logger.info("Setting up conversation chain")
        if st.session_state.vectorstore:
            st.session_state.conversation = (
                {
                    "context": st.session_state.vectorstore.as_retriever(search_kwargs={"k": 4}),
                    "chat_history": lambda x: [HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"]) for m in x["chat_history"]],
                    "question": RunnablePassthrough()
                }
                | prompt
                | llm
            )
        else:
            st.session_state.conversation = (
                {
                    "context": lambda x: "",
                    "chat_history": lambda x: [HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"]) for m in x["chat_history"]],
                    "question": RunnablePassthrough()
                }
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
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "conversation" not in st.session_state:
    st.session_state.conversation = None

# Inject CSS for right-aligned user messages
st.markdown("""
<style>
.stChatMessage[data-testid="stChatMessage-user"] {
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

# Sidebar settings and chat sessions
with st.sidebar:
    st.title("GenixAI Settings")
    selected_model = st.selectbox("Select Model", ["llama3-8b-8192", "llama3-70b-8192", "gemma2-9b-it"], index=0)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)
    max_tokens = st.slider("Max Tokens", 50, 1000, 70, 10)
    
    st.subheader("Upload Documents/Images")
    uploaded_files = st.file_uploader("Upload PDF, Text, or Image", type=["pdf", "txt", "png", "jpg", "jpeg"], accept_multiple_files=True)
    if uploaded_files and st.button("Process Uploaded Files"):
        with st.spinner("Processing files..."):
            if process_files(uploaded_files):
                setup_conversation_chain()
                st.success("Files processed successfully!")
    
    st.subheader("Chat Sessions")
    if st.button("Create New Chat"):
        new_chat_id = str(uuid.uuid4())
        st.session_state.chat_sessions[new_chat_id] = []
        st.session_state.current_chat_id = new_chat_id
    
    if st.session_state.chat_sessions:
        chat_options = {f"Chat {i+1} ({chat_id[:8]})": chat_id for i, chat_id in enumerate(st.session_state.chat_sessions.keys())}
        selected_chat = st.selectbox("Select Chat Session", list(chat_options.keys()), 
                                  index=list(chat_options.values()).index(st.session_state.current_chat_id) 
                                  if st.session_state.current_chat_id in chat_options.values() else 0)
        st.session_state.current_chat_id = chat_options[selected_chat]
    
    st.subheader("About GenixAI")
    st.markdown("""
    **What**: GenixAI delivers insightful answers and processes documents/images.  
    **How**: Uses advanced generative AI and OCR for accurate responses.  
    **Why**: Boosts productivity with fast, reliable information.  
    **Developer**: Muhammad Awais Laal, Generative AI Developer.
    """)

# Main app layout
st.title("GenixAI")

# Chat interface
st.subheader("Chat")
if st.session_state.current_chat_id and st.session_state.chat_sessions.get(st.session_state.current_chat_id):
    for message in st.session_state.chat_sessions[st.session_state.current_chat_id]:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
            st.markdown(message["content"])
else:
    st.write("Select or create a chat session to start chatting.")

# Chat input
if prompt := st.chat_input("Type your message here..."):
    if not st.session_state.current_chat_id:
        new_chat_id = str(uuid.uuid4())
        st.session_state.chat_sessions[new_chat_id] = []
        st.session_state.current_chat_id = new_chat_id
    
    st.session_state.chat_sessions[st.session_state.current_chat_id].append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    if not st.session_state.conversation:
        setup_conversation_chain()
    
    if st.session_state.conversation:
        try:
            logger.info(f"Generating response for prompt: {prompt}")
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Generating response..."):
                    response = st.session_state.conversation.invoke({
                        "question": prompt,
                        "chat_history": st.session_state.chat_sessions[st.session_state.current_chat_id]
                    })
                    answer = response.content
                    st.markdown(answer)
                    if st.session_state.vectorstore:
                        st.write("Sources:")
                        docs = st.session_state.vectorstore.similarity_search(prompt, k=4)
                        for doc in docs:
                            st.write(f"- {doc.page_content[:100]}... (Source: {doc.metadata.get('source', 'Unknown')})")
                
                st.session_state.chat_sessions[st.session_state.current_chat_id].append({"role": "assistant", "content": answer})
                logger.info("Response generated successfully")
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            logger.error(f"Response generation error: {str(e)}")
    else:
        st.error("Conversation chain not initialized. Please check model settings and try again.")
        logger.error("Conversation chain not initialized")
