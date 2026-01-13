"""
Human Agent Profiles for Wixen Chatbot
Defines 5 Human profiles + 1 AI Profile
"""

# Base URL for frontend assets
ASSET_BASE_URL = "/assets/agents/"

AGENT_PROFILES = [
    {
        "id": 1,
        "name": "Sarah",
        "role": "Senior Support Specialist",
        "country": "USA",
        "avatar": f"{ASSET_BASE_URL}sarah.jpg",
        "greeting": "Hi! I'm Sarah. I'm here to help you with any detailed questions about UMTI Tech Solutions. How can I assist you today?"
    },
    {
        "id": 2,
        "name": "Fatima",
        "role": "Solutions Consultant",
        "country": "Pakistan",
        "avatar": f"{ASSET_BASE_URL}fatima.jpg",
        "greeting": "Welcome! I'm Fatima. I specialize in our technical solutions. How may I guide you specifically regarding your project?"
    },
    {
        "id": 3,
        "name": "James",
        "role": "Technical Lead",
        "country": "UK",
        "avatar": f"{ASSET_BASE_URL}james.jpg",
        "greeting": "Hello, I'm James. I can help with technical architecture and deeply complex queries. What's on your mind?"
    },
    {
        "id": 4,
        "name": "David",
        "role": "Client Success Manager",
        "country": "USA",
        "avatar": f"{ASSET_BASE_URL}david.jpg",
        "greeting": "Hey there! I'm David. I want to ensure you have the best experience with UMTI Tech. How can I facilitate that today?"
    },
    {
        "id": 5,
        "name": "Emily",
        "role": "Business Development",
        "country": "Australia",
        "avatar": "https://i.pravatar.cc/150?img=38", # Placeholder for the 5th human if image absent
        "greeting": "Hi! I'm Emily. Interested in partnering with us? Let's discuss how we can grow together."
    }
]

# AI Agent Profile (default)
AI_AGENT_PROFILE = {
    "id": 0,
    "name": "Wixen",
    "role": "AI Assistant",
    "avatar": f"{ASSET_BASE_URL}wixen_fox.png",
    "greeting": "Hello! I'm Wixen, UMTI Tech Solutions' AI assistant. How can I help you today? 🦊"
}

def get_agent_profile(agent_id=0):
    """Get agent profile by ID"""
    if agent_id == 0:
        return AI_AGENT_PROFILE
    
    for profile in AGENT_PROFILES:
        if profile["id"] == agent_id:
            return profile
    
    return AI_AGENT_PROFILE

def get_all_human_profiles():
    """Get all human agent profiles"""
    return AGENT_PROFILES

def get_random_human_profile(exclude_id=None):
    """Get a random human profile, optionally excluding one"""
    import random
    available = [p for p in AGENT_PROFILES if p["id"] != exclude_id]
    return random.choice(available) if available else AGENT_PROFILES[0]

# Global rotation tracker
CURRENT_ROTATION_INDEX = -1

def get_next_human_agent(current_id=None):
    """
    Get the next human agent in the sequence GLOBALLY.
    This ensures that even if page refreshes or multiple users connect,
    it cycles 1->2->3->4->5.
    """
    global CURRENT_ROTATION_INDEX
    
    # Increment global index
    CURRENT_ROTATION_INDEX = (CURRENT_ROTATION_INDEX + 1) % len(AGENT_PROFILES)
    
    return AGENT_PROFILES[CURRENT_ROTATION_INDEX]
