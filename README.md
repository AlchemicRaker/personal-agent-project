# 🛠️ Software Engineer Agent

**Local Grok-powered AI software engineer** built with LangGraph, Grok-4-1-fast, GitHub tools, and a secure Docker sandbox.

## ✨ New UI Features
- **Sidebar Controls**: Set GitHub repo, clone with one click, list workspace files, **File Browser** (refresh list, read files), manage sessions (new/persistent threads).
- **Repo Header**: Shows active repo.
- **Color-Coded Live Trace**: Green=Coder, Orange=Planner, Blue=Tester, etc. Real-time updates.
- **Metrics Dashboard**: Turns, trace lines, unique agents, **Est. Tokens**.
- **Downloads**: Full trace as .txt.
- **Session Persistence**: Thread IDs for long-running tasks.

Features:
- Reads any public or private GitHub repository (list files, read content)
- Runs arbitrary Python code in an isolated sandbox (no host access)
- Creates branches, commits, and Pull Requests automatically
- Persistent conversation memory (remembers the repo and context across messages)
- Simple Streamlit chat UI
- 100% local & Dockerized — works on Windows 10, Mac, Linux

## Quick Start (CLI Commands)

```
# 1. Clone the repo
git clone https://github.com/example-user/software-engineer-agent.git
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

1. **Set Repo** in sidebar → Clone.
2. **List Files** or use **File Browser** to explore/read files.
3. Chat: "Add hello world to main.py" → Watch color-coded trace → Auto PR!

The agent remembers the repository and all previous steps.

## Common Improvements
Use the agent to self-improve! Examples:
- "Add linting to tester" → Updates tester prompt to run black, ruff, mypy
- "Self-improve prompts" → Enhance planner/coder prompts for better performance
- "Add file search to UI" → Client-side filtering in File Browser
- "Improve loop detection" → Track coder-tester rounds >5 → force PR

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

## Multi-Agent Workflow
✅ **Implemented**: Planner → Coder → Tester → PR Creator (with Reasoner fallback)

---

Made with ❤️ and Grok by [your name]