from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import logging
from config import Config
from config import Config
from agent_profiles import get_agent_profile, get_all_human_profiles, get_random_human_profile, get_next_human_agent, AI_AGENT_PROFILE

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[Config.RATE_LIMIT],
    storage_uri="memory://",
)
limiter.init_app(app)

# Validate configuration
try:
    Config.validate()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {str(e)}")

# Initialize LLM
def get_llm():
    """Initialize and return Groq LLM"""
    try:
        return ChatGroq(
            groq_api_key=Config.GROQ_API_KEY,
            model_name=Config.DEFAULT_MODEL,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS,
            model_kwargs={
                "top_p": 0.9,
                "frequency_penalty": 0.5,
                "presence_penalty": 0.5,
            }
        )
    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        return None

# System prompts
# System prompts
# System prompts
NOVA_AI_PROMPT = """You are Nova, the intelligent AI assistant. 🦊
Your goal is to be helpful, concise, and professional.

When you answer:
1. **Be Concise**: Keep answers short (max 2-3 sentences).
2. **Be Structured**: Use bullet points for lists.
3. **Be Friendly**: Warm, professional tone.

About the project:
- Provide accurate, helpful information about the application and its features when relevant.

IMPORTANT RULES:
1. **NO PRICING**: Do NOT discuss pricing. If asked, reply: "Pricing depends on project scope; please provide details so we can follow up."
2. **HIRING/PROJECTS**: If the user wants to hire or collaborate, ask for contact details and propose follow-up via the appropriate channels.
3. **HUMAN HANDOFF**: If user wants to talk to a human, reply: "Sure, I can help with that."

Previous conversation context:
{context}

Current question:
"""

HUMAN_AGENT_PROMPT = """You are {agent_name}, a {agent_role}.
You receive a chat from a user who was just transferred.

* **Greeting**: "Hi, I'm {agent_name}. How can I help?"
* **Style**: Professional, short, and to the point.
* **Format**: Use bullet points if listing items.

Previous conversation context:
{context}

Current question:
"""

@app.route('/api/chat', methods=['POST'])
@limiter.limit("%s" % Config.RATE_LIMIT)
def chat():
    """Handle chat messages"""
    try:
        data = request.json
        message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])
        current_agent = data.get('current_agent', AI_AGENT_PROFILE)
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Enforce message length limit
        if len(message) > Config.MAX_MESSAGE_LENGTH:
            return jsonify({'error': f'Message too long (max {Config.MAX_MESSAGE_LENGTH} characters)'}), 413
        
        # Build context from conversation history
        # Build context from conversation history (bounded)
        limited_history = conversation_history[-Config.MAX_CONVERSATION_ITEMS:] if conversation_history else []
        context = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in limited_history
        ]) if limited_history else "No previous conversation"
        
        # Determine which prompt to use
        is_human_agent = current_agent.get('id', 0) != 0
        
        # Check if user wants human agent
        switch_to_human = False
        new_agent = None
        message_lower = message.lower()
        
        if not is_human_agent and any(phrase in message_lower for phrase in [
            'human agent', 'real person', 'talk to human', 'speak to human',
            'human support', 'real agent', 'customer service',
            'talk to a human', 'speak to a human', 'connect me', 'talk with a human'
        ]):
            switch_to_human = True
            # Start sequence with the first human agent
            new_agent = get_next_human_agent(0)
        elif is_human_agent and any(phrase in message_lower for phrase in [
            'new agent', 'different agent', 'another agent', 'meet new',
            'switch agent', 'change agent'
        ]):
            switch_to_human = True
            # Get next in sequence
            new_agent = get_next_human_agent(current_agent.get('id'))

        # LOGIC CHANGE: If switching, do NOT ask AI to generate response.
        if switch_to_human:
             answer = "I'll connect you with a human expert right away. Please hold on..."
        else:
             # Regular AI Generation
            if is_human_agent:
                system_prompt = HUMAN_AGENT_PROMPT.format(
                    agent_name=current_agent.get('name', 'Agent'),
                    agent_role=current_agent.get('role', 'Support Agent'),
                    context=context
                )
            else:
                system_prompt = NOVA_AI_PROMPT.format(context=context)
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{question}")
            ])
            
            # Get LLM and generate response
            llm = get_llm()
            if not llm:
                return jsonify({'error': 'AI service unavailable'}), 503
            
            chain = (
                {"question": RunnablePassthrough()}
                | prompt
                | llm
            )
            
            response = chain.invoke({"question": message})
            answer = response.content

        # Sanitize and redact sensitive content from AI response
        def sanitize_text(text: str) -> str:
            import re
            if not isinstance(text, str):
                return text
            # Remove emails
            text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[redacted]", text)
            # Remove obvious organization names (generic redaction)
            text = re.sub(r"(?i)\b(UMTI\s*Tech\s*Solutions|UMTI\s*Tech|UMTI)\b", "[redacted organization]", text)
            # Remove URLs
            text = re.sub(r"https?://\S+", "[redacted url]", text)
            # Trim very long responses
            if len(text) > 2000:
                text = text[:2000] + "..."
            return text

        answer = sanitize_text(answer)
        
        logger.info(f"Message: {message[:50]}... | Response: {answer[:50]}...")
        
        return jsonify({
            'response': answer,
            'switch_to_human': switch_to_human,
            'new_agent': new_agent,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred processing your message'}), 500

@app.route('/api/agent-profiles', methods=['GET'])
def get_profiles():
    """Get all available human agent profiles"""
    try:
        return jsonify({
            'ai_agent': AI_AGENT_PROFILE,
            'human_agents': get_all_human_profiles(),
            'success': True
        })
    except Exception as e:
        logger.error(f"Error fetching profiles: {str(e)}")
        return jsonify({'error': 'Failed to fetch agent profiles'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Nova AI Backend',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    logger.info("Starting Nova AI Backend...")
    logger.info(f"Server running on http://localhost:{Config.PORT}")
    app.run(debug=Config.DEBUG, port=Config.PORT, host='0.0.0.0')
