from langchain.agents import create_agent
from langchain_xai import ChatXAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, Sequence, List
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage
import psutil   # ← NEW for memory tracking
from .tools.github_tools import list_repo_files, read_file, create_pr
from .tools.sandbox import run_in_sandbox
from .agents.base import load_prompt
from dotenv import load_dotenv

load_dotenv()

fast_llm = ChatXAI(model="grok-4-1-fast-reasoning", temperature=0.1, max_tokens=1536)
pr_llm = ChatXAI(model="grok-4-1-fast-non-reasoning", temperature=0.0, max_tokens=1024)
reasoner_llm = ChatXAI(model="grok-4", temperature=0.2, max_tokens=3072)

class AgentState(TypedDict):
    messages: Annotated[Sequence, add_messages]
    next: str
    turn: Annotated[int, lambda a, b: b]
    trace: Annotated[List[str], lambda a, b: a + b]
    delta_trace: Annotated[List[str], lambda a, b: b]
    last_agent: str
    original_human_request: str

# Tools
common_tools = [list_repo_files, read_file]
tester_tools = common_tools + [run_in_sandbox]
pr_tools = common_tools + [create_pr]

# Specialist agents
planner = create_agent(model=fast_llm, tools=common_tools, system_prompt=load_prompt("planner"))
coder = create_agent(model=pr_llm, tools=common_tools, system_prompt=load_prompt("coder"))
tester = create_agent(model=fast_llm, tools=tester_tools, system_prompt=load_prompt("tester"))

# PR_Creator uses the non-reasoning model
pr_creator = create_agent(model=pr_llm, tools=pr_tools, system_prompt=load_prompt("pr_creator"))

# Reasoner (expensive) stays on grok-4
reasoner_llm = ChatXAI(
    model="grok-4",
    temperature=0.2,
    max_tokens=1536   # lowered significantly to save memory
)
reasoner = create_agent(model=reasoner_llm, tools=[], system_prompt=load_prompt("reasoner"))

def get_memory_usage():
    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024 / 1024
    return f"{mem_mb:.1f} MB"

def supervisor_node(state: AgentState):
    current_turn = state.get("turn", 0) + 1
    full_trace = state.get("trace", [])
    last_agent = state.get("last_agent", "user")
    
    new_lines = [f"🔄 [Turn {current_turn}] Supervisor (last: {last_agent}) deciding...\n"]
    
    supervisor_prompt = load_prompt("supervisor")
    messages = [supervisor_prompt] + state["messages"][-15:]
    
    response = fast_llm.invoke(messages)
    content = response.content.strip().lower()
    new_lines.append(f"   Raw: {content}\n")
    
    # Smart routing + Reasoner trigger
    if any(word in content for word in ["stuck", "unclear", "help", "confused", "ambiguous"]):
        next_agent = "reasoner"
    elif last_agent == "planner" or "**plan complete**" in content:
        next_agent = "coder"
    elif "planner" in content:
        next_agent = "planner"
    elif "coder" in content:
        next_agent = "coder"
    elif "tester" in content:
        next_agent = "tester"
    elif any(x in content for x in ["pr_creator", "prcreator", "pr creator", "pullrequest"]):
        next_agent = "pr_creator"
    elif "reasoner" in content:
        next_agent = "reasoner"
    elif any(x in content for x in ["finish", "done", "complete"]):
        next_agent = "FINISH"
    else:
        next_agent = "coder"
    
    new_lines.append(f"✅ [Turn {current_turn}] Chose: {next_agent}\n\n")
    full_trace.extend(new_lines)
    
    new_lines.append(f"💾 Memory after supervisor: {get_memory_usage()}\n\n")
    full_trace.extend(new_lines)

    return {
        "next": next_agent,
        "turn": current_turn,
        "trace": full_trace,
        "delta_trace": new_lines,
        "last_agent": "supervisor",
        "original_human_request": state.get("original_human_request")
    }

def create_specialist_node(agent, name: str):
    def node(state: AgentState):
        current_turn = state.get("turn", 0)
        full_trace = state.get("trace", [])
        original_request = state.get("original_human_request", "")
        
        new_lines = [f"🛠️ [Turn {current_turn}] {name} is working...\n"]
        
        clean_messages = [HumanMessage(content=f"Original Human request: {original_request}\n\nNow perform your role.")] + list(state["messages"][-10:])
        
        new_lines = [f"🛠️ [Turn {current_turn}] {name} is working...\n"]
        response = agent.invoke({"messages": clean_messages})
        new_lines.append(f"💾 Memory after {name}: {get_memory_usage()}\n")

        # NEW: Show the actual output of the agent in the trace
        if response["messages"]:
            output = response["messages"][-1].content.strip()
            # Limit length for very long outputs (e.g. Coder full files)
            preview = (output[:800] + "\n... (truncated for trace)") if len(output) > 800 else output
            if name != "PR_Creator":   # PR_Creator is tool-only
                new_lines.append(f"📤 {name} Output:\n{preview}\n\n")
        
        full_trace.extend(new_lines)
        
        return {
            "messages": response["messages"],
            "turn": current_turn,
            "trace": full_trace,
            "delta_trace": new_lines,
            "last_agent": name.lower(),
            "original_human_request": original_request
        }
    return node

# Build graph
graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("planner", create_specialist_node(planner, "Planner"))
graph.add_node("coder", create_specialist_node(coder, "Coder"))
graph.add_node("tester", create_specialist_node(tester, "Tester"))
graph.add_node("pr_creator", create_specialist_node(pr_creator, "PR_Creator"))
graph.add_node("reasoner", create_specialist_node(reasoner, "Reasoner"))   # new node

graph.add_edge(START, "supervisor")

graph.add_conditional_edges(
    "supervisor",
    lambda state: state["next"],
    {
        "planner": "planner",
        "coder": "coder",
        "tester": "tester",
        "pr_creator": "pr_creator",
        "reasoner": "reasoner",
        "FINISH": END,
    }
)

for node in ["planner", "coder", "tester", "pr_creator", "reasoner"]:
    graph.add_edge(node, "supervisor")

memory = MemorySaver()
compiled_graph = graph.compile(checkpointer=memory)

agent = compiled_graph