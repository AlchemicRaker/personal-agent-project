from pathlib import Path

WORKSPACE = Path("/workspace")
TEMP_DIR = WORKSPACE / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def temp_write(path: str, content: str) -> str:
    """
    Write or overwrite a file in the temporary scratch space (/workspace/temp).

    Signature: temp_write(path: str, content: str) -> str

    Use this tool when:
    - You need to create temporary files, test data, intermediate results, or scratch notes
    - The Coder or Tester needs a temporary file for testing or processing

    This is the correct place for any short-lived or debugging files. Never use it for permanent code or memory.
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
    Read the content of a file from the temporary scratch space (/workspace/temp).

    Signature: temp_read(path: str) -> str

    Use this tool when:
    - You need to inspect temporary files created earlier in the session
    - The Tester or Coder needs to verify intermediate results

    Returns the full content or an error message if the file doesn't exist.
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
    List all files and subdirectories currently in the temporary scratch space (/workspace/temp).

    Signature: temp_list_dir() -> str

    Use this tool when:
    - You want to see what temporary files exist in the current session
    - Debugging or exploring what the Coder or Tester has created

    Returns a clean list of file paths relative to the temp folder.
    """
    try:
        files = [str(p.relative_to(TEMP_DIR)) for p in TEMP_DIR.rglob("*") if p.is_file()]
        return "\n".join(files) if files else "Temp directory is empty."
    except Exception as e:
        return f"❌ Error listing temp/: {str(e)}"