from github import Github, GithubException
from dotenv import load_dotenv
import os

load_dotenv()
g = Github(os.getenv("GITHUB_TOKEN"))

def create_pr(
    repo_full_name: str,
    title: str,
    body: str,
    branch_name: str,
    files_to_change: dict
) -> str:
    """
    Create a branch, commit changes, and open a Pull Request.
    files_to_change = {"path/to/file.py": "full new content", ...}
    """
    try:
        repo = g.get_repo(repo_full_name)
        
        # Create branch from main
        main = repo.get_branch("main")
        ref = repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main.commit.sha)
        
        # Apply changes
        for path, content in files_to_change.items():
            try:
                file = repo.get_contents(path, ref=branch_name)
                repo.update_file(path, f"Update {path}", content, file.sha, branch=branch_name)
            except GithubException:  # file doesn't exist yet
                repo.create_file(path, f"Add {path}", content, branch=branch_name)
        
        # Create PR
        pr = repo.create_pull(
            title=title,
            body=body,
            head=branch_name,
            base="main"
        )
        return f"✅ PR created successfully: {pr.html_url}"
        
    except Exception as e:
        return f"❌ Error creating PR: {str(e)}"