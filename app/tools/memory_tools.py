from langchain_xai import ChatXAI
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

MEMORY_PATH = Path("/memory")

llm = ChatXAI(model="grok-4-1-fast-reasoning", temperature=0.1, max_tokens=2048)


def load_short_term_memory() -> str:
    """Load short term memory content."""
    file_path = MEMORY_PATH / "short_term_memory.txt"
    return file_path.read_text(encoding="utf-8") if file_path.exists() else ""


def load_long_term_memory() -> str:
    """Load long term memory content."""
    file_path = MEMORY_PATH / "long_term_memory.txt"
    return file_path.read_text(encoding="utf-8") if file_path.exists() else ""


def ingest_short_term_memory(new_memory: str) -> str:
    """Ingest new short-term memory: deduplicate, clean, append as concise bullets."""
    old_memory = load_short_term_memory()
    
    prompt = f"""Current short-term memory (recent context as bullets):
{old_memory}

New memory to ingest:
{new_memory}

Instructions: 
- Deduplicate and clean the combined memory.
- Keep ONLY recent, relevant context as concise bullet points (max 20 bullets, short).
- Focus on actionable recent events, decisions, context for immediate tasks.
- Output ONLY the updated bullet list, nothing else."""

    response = llm.invoke(prompt)
    updated = response.content.strip()
    
    MEMORY_PATH.mkdir(exist_ok=True)
    (MEMORY_PATH / "short_term_memory.txt").write_text(updated, encoding="utf-8")
    
    return f"Ingested short-term memory. New length: {len(updated)} chars."


def ingest_long_term_memory(new_memory: str) -> str:
    """Ingest new long-term memory: summarize key facts, persistent knowledge."""
    old_memory = load_long_term_memory()
    
    prompt = f"""Current long-term memory (key facts/summaries):
{old_memory}

New memory to ingest:
{new_memory}

Instructions:
- Merge, deduplicate, and summarize into persistent key facts and summaries.
- Focus on stable knowledge, patterns, important decisions (not transient details).
- Use concise paragraphs or structured bullets.
- Output ONLY the updated long-term memory, nothing else."""

    response = llm.invoke(prompt)
    updated = response.content.strip()
    
    MEMORY_PATH.mkdir(exist_ok=True)
    (MEMORY_PATH / "long_term_memory.txt").write_text(updated, encoding="utf-8")
    
    return f"Ingested long-term memory. New length: {len(updated)} chars."
