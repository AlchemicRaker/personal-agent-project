from github import Github, GithubException
from dotenv import load_dotenv
import os

load_dotenv()
g = Github(os.getenv("GITHUB_TOKEN"))

def list_repo_files(repo_full_name: str, branch: str = "main"):
    """List files in a repo."""
    try:
        repo = g.get_repo(repo_full_name)
        contents = repo.get_contents("", ref=branch)
        return [c.path for c in contents if not c.path.endswith(".git")]
    except Exception as e:
        return f"Error: {str(e)}"

def read_file(repo_full_name: str, file_path: str, branch: str = "main"):
    """Read file content."""
    try:
        repo = g.get_repo(repo_full_name)
        file = repo.get_contents(file_path, ref=branch)
        return file.decoded_content.decode("utf-8")
    except Exception as e:
        return f"Error: {str(e)}"

def create_pr(repo_full_name: str, title: str, body: str, branch_name: str, files_to_change: dict):
    """Create branch + commit + PR. files_to_change = {'path': 'new_content'}"""
    try:
        repo = g.get_repo(repo_full_name)
        # Create branch
        main = repo.get_branch("main")
        ref = repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main.commit.sha)
        
        # Update files
        for path, content in files_to_change.items():
            try:
                file = repo.get_contents(path, ref=branch_name)
                repo.update_file(path, f"Update {path}", content, file.sha, branch=branch_name)
            except GithubException:  # file doesn't exist
                repo.create_file(path, f"Add {path}", content, branch=branch_name)
        
        # Create PR
        pr = repo.create_pull(title=title, body=body, head=branch_name, base="main")
        return f"PR created: {pr.html_url}"
    except Exception as e:
        return f"Error creating PR: {str(e)}"