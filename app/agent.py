from langchain.agents import create_agent
from langchain_xai import ChatXAI
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from .tools.github_tools import list_repo_files, read_file, create_pr
from .tools.sandbox import run_in_sandbox
from dotenv import load_dotenv

load_dotenv()

llm = ChatXAI(
    model="grok-4-1-fast-reasoning",
    temperature=0.1,
    max_tokens=4096
)

tools = [list_repo_files, read_file, create_pr, run_in_sandbox]

system_prompt = SystemMessage(content="""
You are an expert software engineer agent. 
You can read any GitHub repo, propose code changes, run tests in a secure sandbox, and create PRs.
Always think step-by-step. Use tools when needed.
When creating a PR, first run tests in the sandbox if possible.
Always challenge your work before presenting it.

This repository (https://github.com/AlchemicRaker/personal-agent-project) contains your own codebase.
It is also your primary assignment at the moment, so you may assume that we are talking about this repository unless some other is mentioned.
""")

memory = MemorySaver()

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
    checkpointer=memory
)