from pathlib import Path
import subprocess
import os

WORKSPACE = Path("/workspace")
REPO_DIR = WORKSPACE / "current_repo"


def clone_repo(repo_full_name: str) -> str:
    """
    Clone (or completely refresh) the target GitHub repository into the staging area.

    Signature: clone_repo(repo_full_name: str) -> str

    Use this tool when:
    - Starting a new task and no repo is cloned yet
    - The user mentions a different repository
    - You need a clean, up-to-date copy of the code

    Do NOT call this tool repeatedly in the same session unless the user changes the repo.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print(f"🔧 clone_repo START - GITHUB_TOKEN not found in environment")
        return "Error: GITHUB_TOKEN not found in environment"

    print(f"🔧 clone_repo START - Cleaning previous clone: {REPO_DIR}")

    # Clean previous clone
    subprocess.run(["rm", "-rf", str(REPO_DIR)], shell=True, check=False)
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🔧 clone_repo CLEANED - Directory ready: {REPO_DIR}")

    clone_url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
    print(f"🔧 clone_repo CLONING - URL: {clone_url.replace(token, '*****')}")

    try:
        result = subprocess.run(
            ["git", "clone", clone_url, str(REPO_DIR)],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"🔧 clone_repo SUCCESS - STDOUT: {result.stdout} - STDERR: {result.stderr}")
        return f"✅ Successfully cloned {repo_full_name} into current_repo/ staging area"
    except subprocess.CalledProcessError as e:
        print(f"🔧 clone_repo ERROR - STDOUT: {e.stdout} - STDERR: {e.stderr}")
        return f"Error cloning {repo_full_name}: {e.stderr.strip()}"


def repo_list_dir(path: str = ".") -> str:
    """
    List all files and directories in the current_repo staging area.

    Signature: repo_list_dir(path: str = ".") -> str

    Use this tool to:
    - Explore the project structure
    - Find relevant files before reading or editing
    - Verify what files exist after cloning

    Call this early in planning or before any repo_read_file / repo_write_file.
    """
    full_path = REPO_DIR / path
    if not full_path.exists():
        return f"Path not found: {path}"
    try:
        files = [str(p.relative_to(REPO_DIR)) for p in full_path.rglob("*") if p.is_file()]
        print(f"🔧 repo_list_dir - Found {len(files)} files in {path}")
        return "\n".join(files)
    except Exception as e:
        print(f"🔧 repo_list_dir ERROR - {path}: {str(e)}")
        return f"Error listing {path}: {str(e)}"


def repo_read_file(path: str) -> str:
    """
    Read the full content of a file from the current_repo staging area.

    Signature: repo_read_file(path: str) -> str

    Use this tool BEFORE making any changes to understand the current code.
    Always call this first when the Coder or Planner needs to see a file.
    """
    try:
        content = (REPO_DIR / path).read_text(encoding="utf-8")
        print(f"🔧 repo_read_file SUCCESS - {path} ({len(content)} chars)")
        return content
    except Exception as e:
        print(f"🔧 repo_read_file ERROR - {path}: {str(e)}")
        return f"Error reading {path}: {str(e)}"


def repo_write_file(path: str, content: str) -> str:
    """
    Write or overwrite a file in the current_repo staging area.

    Signature: repo_write_file(path: str, content: str) -> str

    Use this tool to make changes to the codebase.
    The Coder should always use this for any file modification or creation.
    """
    try:
        (REPO_DIR / path).parent.mkdir(parents=True, exist_ok=True)
        (REPO_DIR / path).write_text(content, encoding="utf-8")
        print(f"🔧 repo_write_file SUCCESS - {path} ({len(content)} chars)")
        return f"✅ Wrote {path} ({len(content)} characters)"
    except Exception as e:
        print(f"🔧 repo_write_file ERROR - {path}: {str(e)}")
        return f"Error writing {path}: {str(e)}"


def repo_run_command(cmd: str, timeout: int = 30) -> str:
    """
    Run a shell command inside the current_repo staging area.

    Signature: repo_run_command(cmd: str, timeout: int = 30) -> str

    Use this tool for:
    - Running tests (pytest, npm test, etc.)
    - Any command that needs to execute in the context of the cloned repo

    Do NOT use this tool for:
    - Git operations

    The Tester should use this for running tests.
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        print(f"🔧 repo_run_command SUCCESS - {cmd} - Exit: {result.returncode}")
        return f"Exit code: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        print(f"🔧 repo_run_command TIMEOUT - {cmd}")
        return "Command timed out after 30s"
    except Exception as e:
        print(f"🔧 repo_run_command ERROR - {cmd}: {str(e)}")
        return f"Error running command: {str(e)}"