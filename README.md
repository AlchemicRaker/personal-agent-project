# 🛠️ Software Engineer Agent

**Local Grok-powered AI software engineer** built with LangGraph, Grok-4-1-fast, GitHub tools, and a secure Docker sandbox.

Features:
- Reads any public or private GitHub repository (list files, read content)
- Lists open pull requests in a repository
- Runs arbitrary Python code in an isolated sandbox (no host access)
- Creates branches, commits, and Pull Requests automatically
- Persistent conversation memory (remembers the repo and context across messages)
- Simple Streamlit chat UI
- 100% local & Dockerized — works on Windows 10, Mac, Linux

## Quick Start (CLI Commands)

```
# 1. Clone the repo
git clone https://github.com/YOUR-USERNAME/software-engineer-agent.git
cd software-engineer-agent

# 2. Set up environment variables
copy .env.example .env     # Windows PowerShell
# cp .env.example .env     # Linux / Mac / Git Bash

# 3. Edit .env (add your keys)
code .env
```

Fill in:
```
XAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
```

```
# 4. Launch the agent
docker compose up --build
```

Open **http://localhost:8501** in your browser.

To stop:
```
docker compose down
```

## How to use

Start a conversation with the repo:
```
We are working on https://github.com/langchain-ai/langgraph
```

Then ask anything:
- List the files
- Read the README
- Run this in sandbox: print("Hello from isolated env")
- Create a new file fix.py with ... and open a PR titled "Add Grok integration"

The agent remembers the repository and all previous steps.

## Project Structure

```
software-engineer-agent/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile.agent
├── sandbox.Dockerfile
├── requirements.txt
└── app/
    ├── agent.py
    ├── streamlit_app.py
    └── tools/
        ├── github_tools.py
        └── sandbox.py
```

## Development

- All code changes are live-mounted into the container
- Restart with `docker compose up --build` after changing Python files
- Add new tools in `app/tools/`

## Tech Stack

- LLM: grok-4-1-fast-reasoning (xAI)
- Framework: LangGraph + LangChain
- UI: Streamlit
- Sandbox: Docker-in-Docker (isolated Python 3.12)
- GitHub: PyGitHub

## Next Steps (planned)

- Multi-agent workflow (Planner → Coder → Tester → PR Creator)
- AWS deployment using FAST template + Cognito + React UI
- GitHub Actions CI/CD

---

Made with ❤️ and Grok by [your name]
