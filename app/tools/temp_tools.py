from pathlib import Path

WORKSPACE = Path("/workspace")
TEMP_DIR = WORKSPACE / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def temp_write(path: str, content: str) -> str:
    """
    Write or overwrite a file in the temporary scratch space (/workspace/temp).
    Useful for temporary notes, test data, intermediate files, etc.
    """
    try:
        full_path = TEMP_DIR / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"✅ Wrote temp/{path} ({len(content)} characters)"
    except Exception as e:
        return f"❌ Error writing temp/{path}: {str(e)}"

def temp_read(path: str) -> str:
    """
    Read a file from the temporary scratch space (/workspace/temp).
    """
    try:
        full_path = TEMP_DIR / path
        if not full_path.exists():
            return f"File not found in temp/: {path}"
        return full_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"❌ Error reading temp/{path}: {str(e)}"

def temp_list_dir() -> str:
    """
    List all files currently in the temp folder (for debugging / visibility).
    """
    try:
        files = [str(p.relative_to(TEMP_DIR)) for p in TEMP_DIR.rglob("*") if p.is_file()]
        return "\n".join(files) if files else "Temp directory is empty."
    except Exception as e:
        return f"❌ Error listing temp/: {str(e)}"