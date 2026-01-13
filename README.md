# Wixen — AI Chatbot 🚀

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) ![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Node.js](https://img.shields.io/badge/Node-16%2B-green)

Professional, extensible AI chatbot built with a React frontend and Flask backend. Provides conversational AI support with optional human agent handoffs and configurable greetings.

---

## Table of Contents
1. [Highlights](#highlights-️)
2. [Features](#features)
3. [Project Structure](#project-structure)
4. [Quickstart](#quickstart)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Contributing](#contributing)
10. [License & Contact](#license--contact)

---

## Highlights ✨
- Lightweight Flask API with React SPA
- Groq AI (LLaMA) integration via LangChain
- Five human agent profiles with seamless switching
- Auto-rotating greeting messages and responsive UI
- Clear API for integration and customization

![CI](https://github.com/muhammadawaislaal/Multi_Agent-Ai-bot/actions/workflows/ci.yml/badge.svg)

## Features ✅
- Conversational context handling
- Human agent handoff (on-demand or keyword-triggered)
- Animated, responsive chat widget
- Simple configuration through environment variables
- Ready for local development and production deployment

## Project Structure 📁

```
Wixen/
├── backend/                 # Flask API and server-side logic
│   ├── app.py               # Flask application and routes
│   ├── config.py            # App configuration and settings
│   ├── agent_profiles.py    # Predefined human agent data
│   ├── requirements.txt     # Python dependencies
│   └── test_backend.py      # Backend tests
├── frontend/                # React application
│   ├── public/
│   ├── src/
│   │   ├── components/      # Chat widget and UI components
│   │   ├── services/        # API wrapper
│   │   └── styles/
│   └── package.json
└── .env                     # Environment variables (not checked in)
```

---

## Quickstart 🚀

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn
- A Groq API key (or other model provider) — set in `.env`

### Backend (local)
```bash
# from project root
cd backend
python -m venv .venv           # optional but recommended
# activate venv (Windows PowerShell)
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
# create or update .env with GROQ_API_KEY and optional PORT
python app.py
# Server will be available at http://localhost:5000
```

### Frontend (local)
```bash
cd frontend
npm install
npm start
# App available at http://localhost:3000
```

> Tip: Use `REACT_APP_API_URL` in the frontend `.env` when pointing to a different backend URL.

## Screenshot

Add a screenshot to `assets/` (recommended `assets/screenshot.png`) and reference it below. Example:

![Chat widget demo](assets/screenshot.png)

---

## Configuration 🔧
- .env (root or backend):
  - `GROQ_API_KEY` — required for Groq AI
  - `PORT` — backend port (default: 5000)
- `backend/config.py`:
  - `DEFAULT_MODEL`, `TEMPERATURE`, `MAX_TOKENS`
- Frontend `ChatWidget.js`:
  - `GREETING_MESSAGES` — edit greeting text
  - `greetingInterval` — rotation interval (ms)
  - `agentSwitchDelay` — delay before switching to human (ms)

---

## API Reference 🧭

### POST /api/chat
Send a user message and receive an AI or human-agent response.

Request (example):
```json
{
  "message": "Hello",
  "conversation_history": [],
  "current_agent": { "id": 0, "name": "Wixen" }
}
```
Response (example):
```json
{
  "response": "Hi! How can I help?",
  "switch_to_human": false,
  "new_agent": null,
  "success": true
}
```

### GET /api/agent-profiles
Returns the available human agent profiles.

### GET /api/health
Simple health check endpoint; returns service status.

---

## Testing ✅
- Backend tests are provided in `backend/test_backend.py` (uses pytest).

```bash
# from project root
cd backend
pip install -r requirements.txt
pytest -q
```

Add tests for any new behavior you implement.

## Troubleshooting Tips
- If push or authentication to GitHub fails, verify your credentials or use an SSH remote.
- For CORS or API connectivity issues, confirm `REACT_APP_API_URL` and backend `PORT` values.
- If the Groq API rate-limits you, reduce request frequency or contact Groq support.

---

## Deployment & CI/CD 📦
- Containerize backend with a simple `Dockerfile` and deploy to your preferred cloud provider.
- Use GitHub Actions for linting, testing and building the frontend.
- Add repository badges (build, coverage) to this README once CI is configured.

### Example GitHub Actions

This repository includes a lightweight CI workflow (`.github/workflows/ci.yml`) that:
- Installs Python dependencies and runs `pytest` for the backend
- Installs Node and runs `npm ci` and `npm run build` for the frontend (if present)

Once Actions completes, the badge at the top will reflect build status.

---

## Contributing 🤝
- Fork the repository and open a Pull Request for review
- Follow conventional commits and include tests for new features
- Add a clear PR description and reference issues where applicable

> Recommended: add `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` to guide collaborators.

---

## Adding this project to GitHub 🧭
1. Create a new repository on GitHub under your account or organization
2. Initialize local git (if not already):
```bash
git init
git add .
git commit -m "chore: initial project import"
git branch -M main
git remote add origin git@github.com:<your-username>/<repo-name>.git
git push -u origin main
```
3. Configure repository settings: topics, README, license, branch protection and CI workflows.

---

## License & Contact 📄
- **License**: MIT — see `LICENSE` in the repository
- **Maintainer**: Project Maintainers

If you need help preparing this repo for GitHub (badges, GitHub Actions, or release notes), I can add recommended files and CI workflow templates.

---

## Acknowledgements 🙏
Built with React, Flask and Groq AI. UI inspired by modern chat applications; animations by Framer Motion.

