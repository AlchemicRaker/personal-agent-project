from github import Github, GithubException
from dotenv import load_dotenv
import os
import subprocess
from pathlib import Path

load_dotenv()
g = Github(os.getenv("GITHUB_TOKEN"))
WORKSPACE = Path("/workspace")

def create_pull_request(repo_full_name: str, title: str, body: str, branch_name: str) -> str:
    """Create a pull request by staging, committing, pushing all changes in the workspace, and opening the PR."""
    try:
        repo = g.get_repo(repo_full_name)
        subprocess.run(["git", "-C", str(WORKSPACE), "checkout", "-b", branch_name], check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(WORKSPACE), "add", "."], check=True, capture_output=True, text=True)
        commit_msg = f"Commit for PR: {title}"
        commit_result = subprocess.run(["git", "-C", str(WORKSPACE), "commit", "-m", commit_msg], capture_output=True, text=True)
        if commit_result.returncode != 0:
            if "nothing to commit" in commit_result.stdout.lower():
                return "No changes to commit. PR not created."
            else:
                raise Exception(f"Commit failed: {commit_result.stderr}")
        push_result = subprocess.run(["git", "-C", str(WORKSPACE), "push", "origin", branch_name], capture_output=True, text=True)
        if push_result.returncode != 0:
            raise Exception(f"Push failed: {push_result.stderr}")
        pr = repo.create_pull(title=title, body=body, head=branch_name, base="main")
        return f"PR created: {pr.html_url}"
    except Exception as e:
        return f"Error creating PR: {str(e)}"