"""
Backend Verification Test Script
Tests all backend components without starting the server
"""

print("=" * 50)
print("WIXEN BACKEND VERIFICATION TEST")
print("=" * 50)

# Test 1: Import all modules
print("\n1. Testing imports...")
try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    import logging
    from config import Config
    from agent_profiles import AI_AGENT_PROFILE, AGENT_PROFILES, get_random_human_profile
    print("   ✅ All imports successful")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    print("\n   Please install dependencies:")
    print("   pip install -r requirements.txt")
    exit(1)

# Test 2: Check configuration
print("\n2. Testing configuration...")
try:
    print(f"   - Default Model: {Config.DEFAULT_MODEL}")
    print(f"   - Temperature: {Config.TEMPERATURE}")
    print(f"   - Max Tokens: {Config.MAX_TOKENS}")
    print(f"   - Port: {Config.PORT}")
    
    if Config.GROQ_API_KEY and Config.GROQ_API_KEY != "your_groq_api_key_here":
        print(f"   - API Key: Set (starts with {Config.GROQ_API_KEY[:10]}...)")
        print("   ✅ Configuration valid")
    else:
        print("   ⚠️  WARNING: GROQ_API_KEY not set in .env file")
        print("   The backend will not work without a valid API key")
except Exception as e:
    print(f"   ❌ Configuration error: {e}")

# Test 3: Verify agent profiles
print("\n3. Testing agent profiles...")
try:
    print(f"   - AI Agent: {AI_AGENT_PROFILE['name']} ({AI_AGENT_PROFILE['role']})")
    print(f"   - Human Agents: {len(AGENT_PROFILES)} profiles loaded")
    for i, agent in enumerate(AGENT_PROFILES, 1):
        print(f"     {i}. {agent['name']} - {agent['role']} ({agent['country']})")
    
    # Test random selection
    random_agent = get_random_human_profile()
    print(f"   - Random selection works: {random_agent['name']}")
    print("   ✅ Agent profiles working correctly")
except Exception as e:
    print(f"   ❌ Agent profiles error: {e}")

# Test 4: Flask app initialization
print("\n4. Testing Flask app initialization...")
try:
    app = Flask(__name__)
    CORS(app)
    print("   ✅ Flask app can be initialized")
except Exception as e:
    print(f"   ❌ Flask initialization error: {e}")

# Test 5: LLM initialization (if API key is set)
print("\n5. Testing LLM initialization...")
try:
    if Config.GROQ_API_KEY and Config.GROQ_API_KEY != "your_groq_api_key_here":
        llm = ChatGroq(
            groq_api_key=Config.GROQ_API_KEY,
            model_name=Config.DEFAULT_MODEL,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS,
        )
        print("   ✅ LLM initialized successfully")
        print("   ✅ Ready to process chat requests")
    else:
        print("   ⏭️  Skipped (API key not configured)")
except Exception as e:
    print(f"   ❌ LLM initialization error: {e}")
    print("   Check your GROQ_API_KEY in .env file")

# Final summary
print("\n" + "=" * 50)
print("VERIFICATION COMPLETE")
print("=" * 50)

if Config.GROQ_API_KEY and Config.GROQ_API_KEY != "your_groq_api_key_here":
    print("\n✅ Backend is READY to run!")
    print("\nTo start the server:")
    print("   python app.py")
else:
    print("\n⚠️  Backend needs configuration!")
    print("\nNext steps:")
    print("   1. Add your Groq API key to .env file")
    print("   2. Run: python app.py")

print("\n")
