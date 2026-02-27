from langchain_core.messages import SystemMessage
from pathlib import Path

def get_prompts_dir():
    """Return absolute path to prompts folder - works reliably in Docker"""
    # app/agents/base.py → app/prompts/
    return Path(__file__).parent.parent / "prompts"

def load_prompt(name: str) -> SystemMessage:
    path = get_prompts_dir() / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path.absolute()}")
    content = path.read_text(encoding="utf-8").strip()
    return SystemMessage(content=content)