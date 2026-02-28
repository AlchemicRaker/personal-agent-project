import os
import subprocess
from pathlib import Path
from typing import Optional

WORKSPACE = Path("/workspace")

def clone_repo(repo_full_name: str) -> str:
    """
    Clone (or re-clone) the target GitHub repo into the workspace staging area.
    
    When to use: Call this first if the workspace is empty or needs reset. Only the planner or supervisor should invoke this to initialize the environment. Do not call repeatedly.
    
    Args:
        repo_full_name: Full GitHub repo name (e.g., "user/repo").
    
    Returns: Success message or error.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN not found in environment"

    # Clear previous content to avoid conflicts
    subprocess.run(["rm", "-rf", str(WORKSPACE / "*")], shell=True, cwd=WORKSPACE, check=False)
    
    clone_url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
    try:
        subprocess.run(["git", "clone", clone_url, str(WORKSPACE)], check=True, capture_output=True, text=True)
        return f"Successfully cloned {repo_full_name} into workspace staging area"
    except subprocess.CalledProcessError as e:
        return f"Error cloning {repo_full_name}: {e.stderr}"

def list_dir(path: str = ".") -> str:
    """
    List files in the workspace staging area.
    
    When to use: Use to explore directory structure before reading files. Suitable for planner or reasoner to understand codebase layout.
    
    Args:
        path: Relative path in workspace (default ".").
    
    Returns: Newline-separated list of files or error.
    """
    full_path = WORKSPACE / path
    if not full_path.exists():
        return f"Path not found: {path}"
    return "\n".join([str(p.relative_to(WORKSPACE)) for p in full_path.rglob("*") if p.is_file()])

def read_file(path: str) -> str:
    """
    Read file from workspace staging area.
    
    When to use: Use to inspect file contents after listing dirs. Limit to necessary files to avoid token waste. Planner/coder/tester can use this.
    
    Args:
        path: Relative file path in workspace.
    
    Returns: File content or error.
    """
    try:
        return (WORKSPACE / path).read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading {path}: {str(e)}"

def write_file(path: str, content: str) -> str:
    """
    Write file to workspace staging area.
    
    When to use: Use only by coder to implement changes or by tester to add test files. Do not overwrite without reading first. Validate content before writing.
    
    Args:
        path: Relative file path (creates dirs if needed).
        content: Full content to write (overwrite if exists).
    
    Returns: Success message with char count or error.
    """
    try:
        (WORKSPACE / path).parent.mkdir(parents=True, exist_ok=True)
        (WORKSPACE / path).write_text(content, encoding="utf-8")
        return f"Wrote {path} ({len(content)} chars)"
    except Exception as e:
        return f"Error writing {path}: {str(e)}"

def run_command(cmd: str, timeout: int = 30) -> str:
    """
    Run command inside the workspace staging area.
    
    When to use: Use by coder/tester for installing deps, running tests, or linting. Do not use for git commands (blocked). Keep commands simple and safe.
    
    Args:
        cmd: Shell command (e.g., "pip install -r requirements.txt").
        timeout: Max seconds (default 30).
    
    Returns: Exit code, stdout, stderr or error.
    """
    if cmd.strip().lower().startswith("git "):
        return "Error: Git management commands are not allowed via run_command. Use dedicated GitHub tools."
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return f"Exit code: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"