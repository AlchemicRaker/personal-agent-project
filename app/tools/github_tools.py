from github import Github, GithubException
from dotenv import load_dotenv
import os

load_dotenv()
g = Github(os.getenv("GITHUB_TOKEN"))

def create_pull_request(repo_full_name: str, title: str, body: str, branch_name: str, files_to_change: dict):
    """Create branch + commit + PR. files_to_change = {'path': 'new_content', 'path/to/delete': None}"""
    try:
        repo = g.get_repo(repo_full_name)
        # Create branch
        main = repo.get_branch("main")
        ref = repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main.commit.sha)

        # Fix escaped newlines and other artifacts from LLM output
        body = (body
            .replace("\\n", "\n")
            .replace("\\\\n", "\n")
            .replace("\\r", "")
            .replace("\\t", "\t")
            .strip())

        # Update files
        for path, content in files_to_change.items():
            try:
                existing = repo.get_contents(path, ref=branch_name)
                if content is None:
                    # delete
                    repo.delete_file(path, f"Delete {path}", existing.sha, branch=branch_name)
                else:
                    # update
                    repo.update_file(path, f"Update {path}", content, existing.sha, branch=branch_name)
            except GithubException as ge:
                error_msg = str(ge).lower()
                if "not found" in error_msg and content is None:
                    # file not found, nothing to delete
                    continue
                elif "not found" in error_msg:
                    # file not found, create new
                    repo.create_file(path, f"Add {path}", content, branch=branch_name)
                else:
                    raise

        # Create PR
        pr = repo.create_pull(title=title, body=body, head=branch_name, base="main")
        return f"✅ PR created successfully!\n\n**Title:** {title}\n**URL:** {pr.html_url}"
    except Exception as e:
        return f"❌ Failed to create PR: {str(e)}"
