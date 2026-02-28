from github import Github, GithubException
from dotenv import load_dotenv
import os
import subprocess
from pathlib import Path

load_dotenv()
g = Github(os.getenv("GITHUB_TOKEN"))
WORKSPACE = Path("/workspace")

def create_pull_request(repo_full_name: str, title: str, body: str, branch_name: str) -> str:
    """
    Create a pull request using only the PyGithub library. Detects local changes via git status,
    applies them remotely to a new branch via API (creating one commit per file), and opens the PR.
    
    When to use: Call this only after all changes are finalized in the workspace (e.g., by the coder or tester). 
    This tool handles file additions, modifications, and deletions remotely. Ensure workspace is ready.
    
    Args:
        repo_full_name: Full GitHub repo name (e.g., "user/repo").
        title: PR title (keep concise, descriptive).
        body: PR body (include changes summary, issue reference).
        branch_name: New branch name (unique, descriptive like "fix-issue-123").
    
    Returns: URL of created PR or error message. If no changes, returns "No changes to commit."
    """
    try:
        repo = g.get_repo(repo_full_name)
        
        subprocess.run(["git", "-C", str(WORKSPACE), "config", "user.name", "MechaRaker"], check=True)
        subprocess.run(["git", "-C", str(WORKSPACE), "config", "user.email", "MechaRaker@gmail.com"], check=True)
        
        # Create new branch from main
        main_branch = repo.get_branch("main")
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)
        
        # Stage all changes locally (no commit) to standardize git status
        subprocess.run(["git", "-C", str(WORKSPACE), "add", "."], check=True, capture_output=True, text=True)
        
        # Get changes via git status --porcelain
        status_result = subprocess.run(["git", "-C", str(WORKSPACE), "status", "--porcelain"], check=True, capture_output=True, text=True)
        changes = status_result.stdout.strip().splitlines()
        
        if not changes:
            return "No changes to commit. PR not created."
        
        added_files = []
        modified_files = []
        deleted_files = []
        
        for line in changes:
            if line.startswith('A '):
                path = line[2:].strip()
                added_files.append(path)
            elif line.startswith('M '):
                path = line[2:].strip()
                modified_files.append(path)
            elif line.startswith('D '):
                path = line[2:].strip()
                deleted_files.append(path)
            # Note: Ignores renames, conflicts, etc., for simplicity
        
        # Apply changes remotely
        for path in added_files:
            content = (WORKSPACE / path).read_bytes()
            repo.create_file(path=path, message=f"Add {path} for PR: {title}", content=content, branch=branch_name)
        
        for path in modified_files:
            file_content = repo.get_contents(path, ref="main")
            new_content = (WORKSPACE / path).read_bytes()
            repo.update_file(path=path, message=f"Update {path} for PR: {title}", content=new_content, sha=file_content.sha, branch=branch_name)
        
        for path in deleted_files:
            file_content = repo.get_contents(path, ref="main")
            repo.delete_file(path=path, message=f"Delete {path} for PR: {title}", sha=file_content.sha, branch=branch_name)
        
        # Create PR
        pr = repo.create_pull(title=title, body=body, head=branch_name, base="main")
        return f"PR created: {pr.html_url}"
    
    except GithubException as ge:
        return f"GitHub API error: {str(ge)}"
    except Exception as e:
        return f"Error creating PR: {str(e)}"