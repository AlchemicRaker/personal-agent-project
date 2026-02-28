from langchain.agents import create_agent
from langchain_xai import ChatXAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, Sequence, List
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage
import psutil

# Import tools
from .tools import tools
from .tools.memory_tools import load_short_term_memory, load_long_term_memory
from .agents.base import load_prompt
from dotenv import load_dotenv

load_dotenv()

# LLMs
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


def get_memory_usage() -> str:
    process = psutil.Process()
    mem_mb = process.memory_info().rss / (1024 * 1024)
    return f"{mem_mb:.1f} MB"


# Agents with updated tools
planner = create_agent(
    model=fast_llm, tools=tools, system_prompt=load_prompt("planner")
)
coder = create_agent(model=pr_llm, tools=tools, system_prompt=load_prompt("coder"))
tester = create_agent(model=fast_llm, tools=tools, system_prompt=load_prompt("tester"))
pr_creator = create_agent(
    model=pr_llm, tools=tools, system_prompt=load_prompt("pr_creator")
)
reasoner = create_agent(
    model=reasoner_llm, tools=tools, system_prompt=load_prompt("reasoner")
)


def supervisor_node(state: AgentState):
    current_turn = state.get("turn", 0) + 1
    full_trace = state.get("trace", [])
    last_agent = state.get("last_agent", "user")
    coder_tester_rounds = state.get("coder_tester_rounds", 0)

    new_lines = [f"Turn {current_turn}] Supervisor (last: {last_agent}) deciding...\n"]

    supervisor_prompt = load_prompt("supervisor")
    messages = [supervisor_prompt] + list(state["messages"][-15:])

    response = fast_llm.invoke(messages)
    content = response.content.strip().lower()
    new_lines.append(f"   Raw: {content}\n")

    # Enhanced loop detection: coder-tester rounds >5 forces PR
    loop_detected = False
    if last_agent == "tester" and "coder" in content:
        coder_tester_rounds += 1
        if coder_tester_rounds > 5:
            loop_detected = True
            next_agent = "pr_creator"
            new_lines.append(
                "🔄 Loop detected (coder-tester >5 rounds) - forcing PR!\n"
            )
        else:
            next_agent = "coder"
    elif last_agent == "pr_creator":
        next_agent = "FINISH"  # Force end after PR creation
    elif last_agent == "planner" or "**plan complete**" in content:
        next_agent = "coder"
    elif "planner" in content:
        next_agent = "planner"
    elif "coder" in content:
        next_agent = "coder"
    elif "tester" in content:
        next_agent = "tester"
    elif any(
        x in content
        for x in ["pr_creator", "prcreator", "pr creator", "pullrequest", "pr"]
    ):
        next_agent = "pr_creator"
    elif any(x in content for x in ["issue", "comment"]):
        next_agent = "reasoner"  # Route issue/comment handling to reasoner for planning
    elif any(
        x in content
        for x in ["reasoner", "stuck", "unclear", "help", "confused", "ambiguous"]
    ):
        next_agent = "reasoner"
    elif any(x in content for x in ["finish", "done", "complete"]):
        next_agent = "FINISH"
    else:
        next_agent = "coder"

    new_lines.append(
        f"Chose: {next_agent} (coder/tester rounds: {coder_tester_rounds})\n"
    )
    if loop_detected:
        new_lines.append("Log: Loop detected\n")
    new_lines.append(f"Memory: {get_memory_usage()}\n\n")

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
        "coder_tester_rounds": coder_tester_rounds,
    }


def create_specialist_node(agent, name: str):
    def node(state: AgentState):
        current_turn = state.get("turn", 0)
        full_trace = state.get("trace", [])
        original_request = state.get("original_human_request", "")

        new_lines = [f"Turn {current_turn}] {name} is working...\n"]

        # Smart rolling window + memory + preserve key outputs
        history = list(state["messages"][-12:])
        
        # Load memory
        short_mem = load_short_term_memory()
        long_mem = load_long_term_memory() if name in ["Planner", "Reasoner"] else ""
        mem_content = ""
        if short_mem:
            mem_content += f"SHORT TERM MEMORY (always):\n{short_mem}\n\n"
        if long_mem:
            mem_content += f"LONG TERM MEMORY:\n{long_mem}"
        
        if mem_content:
            history.insert(0, HumanMessage(content=mem_content))
        
        if original_request:
            history.insert(
                0 if not mem_content else 1,
                HumanMessage(content=f"ORIGINAL HUMAN REQUEST: {original_request}")
            )
        if state.get("last_planner_plan"):
            history.insert(
                len([m for m in history[:3] if "ORIGINAL HUMAN REQUEST" in m.content]) + 1,
                HumanMessage(
                    content=f"LATEST PLANNER PLAN:\n{state['last_planner_plan']}"
                ),
            )
        if state.get("last_reasoner_advice"):
            history.insert(
                len([m for m in history[:4] if "LATEST PLANNER PLAN" in m.content or "ORIGINAL HUMAN REQUEST" in m.content]) + 1,
                HumanMessage(
                    content=f"LATEST REASONER ADVICE:\n{state['last_reasoner_advice']}"
                ),
            )

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
                new_lines.append(f"{name} Output Preview:\n{preview}\n\n")

        new_lines.append(f"Memory after {name}: {get_memory_usage()}\n\n")
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
            "coder_tester_rounds": state.get("coder_tester_rounds", 0),
        }

    return node


# Build graph
graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("planner", create_specialist_node(planner, "Planner"))
graph.add_node("coder", create_specialist_node(coder, "Coder"))
graph.add_node("tester", create_specialist_node(tester, "Tester"))
graph.add_node("pr_creator", create_specialist_node(pr_creator, "PR_Creator"))
graph.add_node("reasoner", create_specialist_node(reasoner, "Reasoner"))

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
    },
)

for node in ["planner", "coder", "tester", "reasoner"]:
    graph.add_edge(node, "supervisor")

# PR_Creator goes directly to END (no need to return to supervisor)
graph.add_edge("pr_creator", END)

memory = MemorySaver()
compiled_graph = graph.compile(checkpointer=memory)

agent = compiled_graph
