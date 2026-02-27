from pathlib import Path
import subprocess
import os

WORKSPACE = Path("/workspace")
REPO_DIR = WORKSPACE / "current_repo"

def clone_repo(repo_full_name: str) -> str:
    """Centralized: Clone (or refresh) the target repo into /workspace/current_repo"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN not found in environment"

    # Clean previous clone
    subprocess.run(["rm", "-rf", str(REPO_DIR)], shell=True, check=False)
    REPO_DIR.mkdir(parents=True, exist_ok=True)

    clone_url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
    try:
        result = subprocess.run(
            ["git", "clone", clone_url, str(REPO_DIR)],
            capture_output=True,
            text=True,
            check=True
        )
        return f"✅ Successfully cloned {repo_full_name} into current_repo/ staging area"
    except subprocess.CalledProcessError as e:
        return f"Error cloning {repo_full_name}: {e.stderr.strip()}"

def repo_list_dir(path: str = ".") -> str:
    """List files in the current_repo staging area"""
    full_path = REPO_DIR / path
    if not full_path.exists():
        return f"Path not found: {path}"
    try:
        return "\n".join(str(p.relative_to(REPO_DIR)) for p in full_path.rglob("*") if p.is_file())
    except Exception as e:
        return f"Error listing {path}: {str(e)}"

def repo_read_file(path: str) -> str:
    """Read file from current_repo staging area"""
    try:
        return (REPO_DIR / path).read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading {path}: {str(e)}"

def repo_write_file(path: str, content: str) -> str:
    """Write/overwrite file in current_repo staging area"""
    try:
        (REPO_DIR / path).parent.mkdir(parents=True, exist_ok=True)
        (REPO_DIR / path).write_text(content, encoding="utf-8")
        return f"✅ Wrote {path} ({len(content)} characters)"
    except Exception as e:
        return f"Error writing {path}: {str(e)}"

def repo_run_command(cmd: str, timeout: int = 30) -> str:
    """Run shell command inside the current_repo staging area"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return f"Exit code: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30s"
    except Exception as e:
        return f"Error running command: {str(e)}"