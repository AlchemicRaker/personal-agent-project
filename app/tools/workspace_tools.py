import os
import subprocess
from pathlib import Path

WORKSPACE = Path("/workspace")


def clone_repo(repo_full_name: str) -> str:
    """Clone (or re-clone) the target GitHub repo into the workspace staging area."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN not found in environment"

    # Clear previous content to avoid conflicts
    subprocess.run(
        ["rm", "-rf", str(WORKSPACE / "*")], shell=True, cwd=WORKSPACE, check=False
    )

    clone_url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
    try:
        subprocess.run(
            ["git", "clone", clone_url, str(WORKSPACE)],
            check=True,
            capture_output=True,
            text=True,
        )
        return f"Successfully cloned {repo_full_name} into workspace staging area"
    except subprocess.CalledProcessError as e:
        return f"Error cloning {repo_full_name}: {e.stderr}"


def list_dir(path: str = ".") -> str:
    """List files in the workspace staging area."""
    full_path = WORKSPACE / path
    if not full_path.exists():
        return f"Path not found: {path}"
    return "\n".join(
        [str(p.relative_to(WORKSPACE)) for p in full_path.rglob("*") if p.is_file()]
    )


def read_file(path: str) -> str:
    """Read file from workspace staging area."""
    try:
        return (WORKSPACE / path).read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading {path}: {str(e)}"


def write_file(path: str, content: str) -> str:
    """Write file to workspace staging area."""
    try:
        (WORKSPACE / path).parent.mkdir(parents=True, exist_ok=True)
        (WORKSPACE / path).write_text(content, encoding="utf-8")
        return f"Wrote {path} ({len(content)} chars)"
    except Exception as e:
        return f"Error writing {path}: {str(e)}"


def run_command(cmd: str, timeout: int = 30) -> str:
    """Run command inside the workspace staging area."""
    if cmd.strip().lower().startswith("git "):
        return "Error: Git management commands are not allowed via run_command. Use dedicated GitHub tools."
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return f"Exit code: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"
