from dotenv import load_dotenv
load_dotenv()

from langchain.agents import create_agent
from langchain_xai import ChatXAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, Sequence, List, Dict
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage
import psutil

# Tools
from .tools.repo_tools import clone_repo, repo_list_dir, repo_read_file, repo_write_file, repo_run_command
from .tools.memory_tools import memory_read_user_rules, memory_append_user_rule, memory_ingest_short_term, memory_ingest_long_term, memory_read_short_term, memory_read_long_term
from .tools.temp_tools import temp_write, temp_read
from .tools.github_tools import create_pull_request
from .agents.base import load_prompt

from functools import wraps
import streamlit as st
from langchain_core.tools import BaseTool

def counted_tool(tool):
    """Auto-increments st.session_state.tool_call_counts on every call."""
    @wraps(tool)
    def wrapper(*args, **kwargs):
        if "tool_call_counts" not in st.session_state:
            st.session_state.tool_call_counts = {}

        # Works for both plain functions and StructuredTool / @tool
        tool_name = getattr(tool, "name", tool.__name__)

        st.session_state.tool_call_counts[tool_name] = (
            st.session_state.tool_call_counts.get(tool_name, 0) + 1
        )

        # Optional debug (remove later)
        print(f"🔧 {tool_name} called → total {st.session_state.tool_call_counts[tool_name]}")

        return tool(*args, **kwargs)

    return wrapper

fast_llm = ChatXAI(model="grok-4-1-fast-reasoning", temperature=0.1, max_tokens=1536)
pr_llm = ChatXAI(model="grok-4-1-fast-non-reasoning", temperature=0.0, max_tokens=1024)
reasoner_llm = ChatXAI(model="grok-4", temperature=0.2, max_tokens=4096)

class AgentState(TypedDict):
    messages: Annotated[Sequence, add_messages]
    next: str
    turn: Annotated[int, lambda a, b: b]
    trace: Annotated[List[str], lambda a, b: a + b]
    delta_trace: Annotated[List[str], lambda a, b: b]
    last_agent: str
    original_human_request: str
    last_planner_plan: str
    last_reasoner_advice: str
    coder_tester_rounds: Annotated[int, lambda a, b: b or 0]
    tool_call_counts: Annotated[Dict[str, int], lambda a, b: {**a, **b} or {}]
    node_hit_counts: Annotated[Dict[str, int], lambda a, b: {**a, **b} or {}]

def get_memory_usage() -> str:
    return f"{psutil.Process().memory_info().rss / (1024*1024):.1f} MB"

# All tools
tools = [
    repo_list_dir, repo_read_file, repo_write_file, repo_run_command,
    memory_read_user_rules, memory_append_user_rule, memory_ingest_short_term, memory_ingest_long_term,
    memory_read_short_term, memory_read_long_term,
    temp_write, temp_read,
    create_pull_request
]

# Agents with curated tools
planner = create_agent(
    model=fast_llm,
    tools=[counted_tool(t) for t in [clone_repo, repo_list_dir, repo_read_file, memory_read_user_rules, memory_read_short_term, memory_read_long_term]],
    system_prompt=load_prompt("planner")
)
coder = create_agent(model=pr_llm, tools=[counted_tool(t) for t in [repo_list_dir, repo_read_file, repo_write_file, repo_run_command, temp_write, temp_read]], system_prompt=load_prompt("coder"))
tester = create_agent(model=fast_llm, tools=[counted_tool(t) for t in [repo_list_dir, repo_read_file, repo_run_command]], system_prompt=load_prompt("tester"))
pr_creator = create_agent(model=pr_llm, tools=[counted_tool(t) for t in [create_pull_request, repo_list_dir, repo_read_file]], system_prompt=load_prompt("pr_creator"))
reasoner = create_agent(model=reasoner_llm, tools=[counted_tool(t) for t in [repo_list_dir, repo_read_file, memory_read_user_rules, memory_append_user_rule, memory_ingest_short_term, memory_ingest_long_term, memory_read_short_term, memory_read_long_term]], system_prompt=load_prompt("reasoner"))

def increment_counts(state: AgentState, node_name: str):
    state["node_hit_counts"][node_name] = state["node_hit_counts"].get(node_name, 0) + 1
    return state

def supervisor_node(state: AgentState):
    current_turn = state.get("turn", 0) + 1
    full_trace = state.get("trace", [])
    last_agent = state.get("last_agent", "user")
    coder_tester_rounds = state.get("coder_tester_rounds", 0)
    increment_counts(state, "supervisor")

    new_lines = [f"🔄 [Turn {current_turn}] Supervisor (last: {last_agent}) deciding...\n"]

    supervisor_prompt = load_prompt("supervisor")
    messages = [supervisor_prompt] + list(state["messages"][-15:])

    response = fast_llm.invoke(messages)
    content = response.content.strip().lower()
    new_lines.append(f"   Raw: {content}\n")

    # STRONG TERMINATION + loop protection
    if last_agent == "pr_creator":
        next_agent = "FINISH"   # ← Force end after PR creation
    elif last_agent == "tester" and "coder" in content:
        coder_tester_rounds += 1
        if coder_tester_rounds >= 3:
            next_agent = "pr_creator"
        else:
            next_agent = "coder"
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
    elif any(x in content for x in ["reasoner", "stuck", "unclear", "help", "confused", "ambiguous"]):
        next_agent = "reasoner"
    elif any(x in content for x in ["finish", "done", "complete"]):
        next_agent = "FINISH"
    else:
        next_agent = "coder"

    new_lines.append(f"✅ [Turn {current_turn}] Chose: {next_agent} (coder/tester rounds: {coder_tester_rounds})\n")
    new_lines.append(f"💾 Memory: {get_memory_usage()}\n\n")

    full_trace.extend(new_lines)

    return {
        "next": next_agent,
        "turn": current_turn,
        "trace": full_trace,
        "delta_trace": new_lines,
        "last_agent": "supervisor",
        "original_human_request": state.get("original_human_request"),
        "last_planner_plan": state.get("last_planner_plan"),
        "last_reasoner_advice": state.get("last_reasoner_advice"),
        "coder_tester_rounds": coder_tester_rounds
    }

def create_specialist_node(agent, name: str):
    def node(state: AgentState):
        current_turn = state.get("turn", 0)
        full_trace = state.get("trace", [])
        original_request = state.get("original_human_request", "")
        increment_counts(state, name.lower())

        new_lines = [f"🛠️ [Turn {current_turn}] {name} is working...\n"]

        # Smart rolling window + preserve key outputs
        history = list(state["messages"][-12:])
        if original_request:
            history.insert(0, HumanMessage(content=f"ORIGINAL HUMAN REQUEST: {original_request}"))
        if state.get("last_planner_plan"):
            history.insert(1, HumanMessage(content=f"LATEST PLANNER PLAN:\n{state['last_planner_plan']}"))
        if state.get("last_reasoner_advice"):
            history.insert(2, HumanMessage(content=f"LATEST REASONER ADVICE:\n{state['last_reasoner_advice']}"))

        response = agent.invoke({"messages": history})

        # Preserve key outputs
        if response["messages"]:
            last_output = response["messages"][-1].content.strip()
            if name == "Planner":
                state["last_planner_plan"] = last_output[:1200]
            elif name == "Reasoner":
                state["last_reasoner_advice"] = last_output[:1200]

            preview = last_output[:700] + ("..." if len(last_output) > 700 else "")
            if name != "PR_Creator":
                new_lines.append(f"📤 {name} Output Preview:\n{preview}\n\n")

        new_lines.append(f"💾 Memory after {name}: {get_memory_usage()}\n\n")
        full_trace.extend(new_lines)

        return {
            "messages": response["messages"],
            "turn": current_turn,
            "trace": full_trace,
            "delta_trace": new_lines,
            "last_agent": name.lower(),
            "original_human_request": original_request,
            "last_planner_plan": state.get("last_planner_plan"),
            "last_reasoner_advice": state.get("last_reasoner_advice"),
            "coder_tester_rounds": state.get("coder_tester_rounds", 0)
        }
    return node

def final_report_node(state: AgentState):
    tool_stats = "\n".join([f"- {tool}: {count} times" for tool, count in sorted(state.get("tool_call_counts", {}).items())])
    node_stats = "\n".join([f"- {node}: {count} times" for node, count in sorted(state.get("node_hit_counts", {}).items())])

    report = f"""
**Final Agent Statistics**

**Tool Calls:**
{tool_stats or "No tools called"}

**Node Hits:**
{node_stats or "No nodes hit"}

**Session complete.** Memory has been ingested and persisted.
"""
    state["messages"].append(HumanMessage(content=report))
    return state

# Build graph
graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("planner", create_specialist_node(planner, "Planner"))
graph.add_node("coder", create_specialist_node(coder, "Coder"))
graph.add_node("tester", create_specialist_node(tester, "Tester"))
graph.add_node("pr_creator", create_specialist_node(pr_creator, "PR_Creator"))
graph.add_node("reasoner", create_specialist_node(reasoner, "Reasoner"))
graph.add_node("final_report", final_report_node)

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
        "FINISH": "final_report",
    }
)

for node in ["planner", "coder", "tester", "reasoner"]:
    graph.add_edge(node, "supervisor")

graph.add_edge("pr_creator", "final_report")
graph.add_edge("final_report", END)

memory = MemorySaver()
compiled_graph = graph.compile(checkpointer=memory)

agent = compiled_graph