from pathlib import Path
from langchain_xai import ChatXAI
from langchain_core.messages import HumanMessage

MEMORY_DIR = Path("/workspace/memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

USER_RULES = MEMORY_DIR / "user_rules.md"
SHORT_TERM = MEMORY_DIR / "short_term" / "session_notes.md"
LONG_TERM_DIR = MEMORY_DIR / "long_term"
LONG_TERM_DIR.mkdir(parents=True, exist_ok=True)

fast_llm = ChatXAI(model="grok-4-1-fast-reasoning", temperature=0.1, max_tokens=2048)


def memory_read_user_rules() -> str:
    """
    Read the current persistent user rules from memory.

    Signature: memory_read_user_rules() -> str

    Use this tool when:
    - You need to know the human's preferences, corrections, or rules before planning or reasoning
    - Starting a new task or session

    Planner and Reasoner should call this early in their thinking process.
    """
    return USER_RULES.read_text(encoding="utf-8") if USER_RULES.exists() else "No user rules defined yet."


def memory_append_user_rule(rule: str) -> str:
    """
    Append a new user rule or correction to the persistent user_rules.md file.

    Signature: memory_append_user_rule(rule: str) -> str

    Use this tool when:
    - The human gives you a correction or preference ("never do X", "always use Y style", etc.)
    - You want the agent to remember something important for future sessions

    Only Planner and Reasoner should use this tool.
    """
    USER_RULES.parent.mkdir(parents=True, exist_ok=True)
    with open(USER_RULES, "a", encoding="utf-8") as f:
        f.write(f"\n\n--- {rule}")
    return "✅ Added to user_rules.md"


def memory_ingest_short_term(new_info: str) -> str:
    """
    LLM-powered ingest for short-term session memory.

    Signature: memory_ingest_short_term(new_info: str) -> str

    Use this tool when:
    - You want to add important context, decisions, or notes from the current session
    - The short-term memory needs to be intelligently merged and summarized

    The LLM will automatically merge, prune outdated info, and keep it concise.
    Only Planner and Reasoner should call this.
    """
    current = SHORT_TERM.read_text(encoding="utf-8") if SHORT_TERM.exists() else ""
    prompt = f"""Current short-term memory:
{current}

New information to ingest:
{new_info}

Merge intelligently:
- Integrate the new information
- Summarize or remove outdated/irrelevant parts
- Keep it concise (max 1500 characters)
- Preserve important context for the current session

Updated short-term memory:"""

    response = fast_llm.invoke([HumanMessage(content=prompt)])
    updated = response.content.strip()
    SHORT_TERM.parent.mkdir(parents=True, exist_ok=True)
    SHORT_TERM.write_text(updated, encoding="utf-8")
    return f"✅ Ingested into short-term memory (new length: {len(updated)} chars)"


def memory_ingest_long_term(key: str, new_info: str) -> str:
    """
    LLM-powered ingest for long-term memory (keyed files).

    Signature: memory_ingest_long_term(key: str, new_info: str) -> str

    Use this tool when:
    - You want to store important long-term knowledge about the project, architecture, or learned patterns
    - Updating existing long-term memory with new insights

    Only Planner and Reasoner should call this.
    """
    path = LONG_TERM_DIR / f"{key}.md"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    prompt = f"""Current long-term memory for key '{key}':
{current}

New information to ingest:
{new_info}

Merge intelligently:
- Integrate new facts
- Summarize/remove outdated parts
- Keep focused on this key
- Max 2000 characters

Updated long-term memory for '{key}':"""

    response = fast_llm.invoke([HumanMessage(content=prompt)])
    updated = response.content.strip()
    path.write_text(updated, encoding="utf-8")
    return f"✅ Ingested into long-term memory '{key}' (new length: {len(updated)} chars)"


def memory_read_short_term() -> str:
    """
    Read the current short-term session notes from memory.

    Signature: memory_read_short_term() -> str

    Use this tool when:
    - You need to recall what happened earlier in this session
    - Planner or Reasoner needs context from previous turns

    Planner and Reasoner should use this when needed.
    """
    return SHORT_TERM.read_text(encoding="utf-8") if SHORT_TERM.exists() else "No short-term memory yet."


def memory_read_long_term(key: str) -> str:
    """
    Read long-term memory for a specific key.

    Signature: memory_read_long_term(key: str) -> str

    Use this tool when:
    - You need to recall project-specific knowledge, architecture decisions, or learned patterns
    - Planning or reasoning about a topic that has long-term memory stored

    Planner and Reasoner should use this when relevant.
    """
    path = LONG_TERM_DIR / f"{key}.md"
    return path.read_text(encoding="utf-8") if path.exists() else f"No long-term memory for '{key}'."