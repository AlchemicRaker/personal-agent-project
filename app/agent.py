from langchain.agents import create_agent
from langchain_xai import ChatXAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, Sequence
from langgraph.graph.message import add_messages
from .tools.github_tools import list_repo_files, read_file, create_pr
from .tools.sandbox import run_in_sandbox
from .agents.base import load_prompt
from dotenv import load_dotenv

load_dotenv()

llm = ChatXAI(
    model="grok-4", # -1-fast-reasoning",
    temperature=0.1,
    max_tokens=4096
)

class AgentState(TypedDict):
    messages: Annotated[Sequence, add_messages]
    next: str
    turn: Annotated[int, lambda a, b: b]  # turn counter

# Tools
common_tools = [list_repo_files, read_file]
tester_tools = common_tools + [run_in_sandbox]
pr_tools = common_tools + [create_pr]

# Specialist agents
planner = create_agent(model=llm, tools=common_tools, system_prompt=load_prompt("planner"))
coder = create_agent(model=llm, tools=common_tools, system_prompt=load_prompt("coder"))
tester = create_agent(model=llm, tools=tester_tools, system_prompt=load_prompt("tester"))
pr_creator = create_agent(model=llm, tools=pr_tools, system_prompt=load_prompt("pr_creator"))

def supervisor_node(state: AgentState):
    current_turn = state.get("turn", 0) + 1
    print(f"🔄 [Turn {current_turn}] Supervisor deciding next step...")
    
    supervisor_prompt = load_prompt("supervisor")
    messages = [supervisor_prompt] + state["messages"][-12:]
    
    response = llm.invoke(messages)
    content = response.content.strip().lower()
    print(f"   Raw LLM output: {content}")
    
    # Strict keyword matching
    if "planner" in content:
        next_agent = "planner"
    elif "coder" in content:
        next_agent = "coder"
    elif "tester" in content:
        next_agent = "tester"
    elif any(x in content for x in ["pr_creator", "prcreator", "pr creator", "pullrequest"]):
        next_agent = "pr_creator"
    elif any(x in content for x in ["finish", "done", "complete"]):
        next_agent = "FINISH"
    else:
        next_agent = "planner"  # safe fallback
    
    print(f"   ✅ [Turn {current_turn}] Supervisor chose: {next_agent}")
    return {"next": next_agent, "turn": current_turn}

def create_specialist_node(agent, name: str):
    def node(state: AgentState):
        current_turn = state.get("turn", 0)
        print(f"🛠️ [Turn {current_turn}] {name} is working...")
        response = agent.invoke(state)
        return {"messages": response["messages"], "turn": current_turn}
    return node

# Build graph
graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("planner", create_specialist_node(planner, "Planner"))
graph.add_node("coder", create_specialist_node(coder, "Coder"))
graph.add_node("tester", create_specialist_node(tester, "Tester"))
graph.add_node("pr_creator", create_specialist_node(pr_creator, "PR_Creator"))

graph.add_edge(START, "supervisor")

graph.add_conditional_edges(
    "supervisor",
    lambda state: state["next"],
    {
        "planner": "planner",
        "coder": "coder",
        "tester": "tester",
        "pr_creator": "pr_creator",
        "FINISH": END,
    }
)

for node in ["planner", "coder", "tester", "pr_creator"]:
    graph.add_edge(node, "supervisor")

memory = MemorySaver()
compiled_graph = graph.compile(checkpointer=memory)

agent = compiled_graph