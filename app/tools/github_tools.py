from github import Github, GithubException
from dotenv import load_dotenv
import os
import subprocess
from pathlib import Path

load_dotenv()
g = Github(os.getenv("GITHUB_TOKEN"))

REPO_DIR = Path("/workspace/current_repo")


def create_pull_request(
    repo_full_name: str,
    title: str,
    body: str,
    branch_name: str
) -> str:
    """
    Create a branch, automatically commit ALL changes present in the workspace staging area
    (/workspace/current_repo), push the branch, and open a Pull Request.

    Signature: create_pull_request(repo_full_name: str, title: str, body: str, branch_name: str) -> str

    Use this tool when:
    - The Coder and Tester have finished making and validating changes in the workspace
    - You are ready to ship the work as a PR to the real GitHub repository

    Behavior:
    - Automatically runs `git add -A`, `git commit`, and `git push` on the staging area
    - Creates a new branch and opens a clean PR
    - No need to pass individual file changes (the workspace is the source of truth)

    The body should be clean Markdown (the tool will handle escaping).
    """
    try:
        if not REPO_DIR.exists():
            print(f"🔧 create_pull_request ERROR - repo does not exist")
            return "Error: current_repo staging area not found. Call clone_repo first."

        repo = g.get_repo(repo_full_name)

        # Create branch from main
        main = repo.get_branch("main")
        ref = repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main.commit.sha)

        # Fix common escaping issues from LLM output
        body = (body
            .replace("\\n", "\n")
            .replace("\\\\n", "\n")
            .replace("\\r", "")
            .replace("\\t", "\t")
            .strip())

        # Auto-commit everything in the staging area
        subprocess.run(["git", "add", "-A"], cwd=REPO_DIR, check=True)
        commit_result = subprocess.run(
            ["git", "commit", "-m", f"{title}\n\n{body}"],
            cwd=REPO_DIR,
            capture_output=True,
            text=True
        )

        if commit_result.returncode != 0 and "nothing to commit" in commit_result.stderr.lower():
            print(f"🔧 create_pull_request FAILED - nothing to commit")
            return "⚠️ No changes to commit in the workspace staging area."

        # Push the branch
        subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=REPO_DIR, check=True)

        # Create PR
        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base="main"
        )

        print(f"🔧 create_pull_request SUCCESS - {pr.html_url}")

        return f"✅ PR created successfully!\n\n**Title:** {title}\n**URL:** {pr.html_url}\n**Branch:** {branch_name}"

    except GithubException as ge:
        return f"❌ GitHub API error: {str(ge)}"
    except subprocess.CalledProcessError as e:
        return f"❌ Git command failed: {e.stderr.strip()}"
    except Exception as e:
        return f"❌ Failed to create PR: {str(e)}"