from github import Github, GithubException
from dotenv import load_dotenv
import os
from pathlib import Path
import time
import subprocess

load_dotenv()
g = Github(os.getenv("GITHUB_TOKEN"))
WORKSPACE = Path("/workspace")


def validate_repo(repo_full_name: str) -> str:
    if not repo_full_name or repo_full_name.count("/") != 1:
        raise ValueError(f"Invalid repo_full_name: {repo_full_name}. Use 'owner/repo'.")
    try:
        g.get_repo(repo_full_name)
    except GithubException:
        raise ValueError(f"Repo not found: {repo_full_name}")
    return repo_full_name


def with_retry(func):
    def wrapper(*args, **kwargs):
        for attempt in range(3):
            try:
                return func(*args, **kwargs)
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2**attempt)
        return None

    return wrapper


@with_retry
def create_pull_request(
    repo_full_name: str, title: str, body: str, branch_name: str
) -> str:
    repo_full_name = validate_repo(repo_full_name)
    repo = g.get_repo(repo_full_name)
    # Simplified: run git status via tool, assume changes staged/committed locally
    status_result = subprocess.run(
        ["git", "status", "--porcelain"], cwd=WORKSPACE, capture_output=True, text=True
    )
    if not status_result.stdout.strip():
        return "No changes to commit."
    # Create branch, commit all, push, create PR (API sim)
    subprocess.run(["git", "checkout", "-b", branch_name], cwd=WORKSPACE, check=True)
    subprocess.run(["git", "add", "."], cwd=WORKSPACE, check=True)
    subprocess.run(["git", "commit", "-m", title], cwd=WORKSPACE, check=True)
    subprocess.run(["git", "push", "origin", branch_name], cwd=WORKSPACE, check=True)
    pr = repo.create_pull(title=title, body=body, head=branch_name, base="main")
    return pr.html_url


@with_retry
def list_issues(repo_full_name: str) -> str:
    repo_full_name = validate_repo(repo_full_name)
    _ = g.get_repo(repo_full_name)
    issues = [issue.html_url for issue in _.get_issues(state="open")]
    return "\n".join(issues)


@with_retry
def read_issue(repo_full_name: str, issue_number: int) -> str:
    repo_full_name = validate_repo(repo_full_name)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(issue_number)
    return f"Title: {issue.title}\nBody: {issue.body or 'No body'}"


@with_retry
def post_comment(repo_full_name: str, issue_number: int, comment: str) -> str:
    repo_full_name = validate_repo(repo_full_name)
    repo = g.get_repo(repo_full_name)
    issue = repo.get_issue(issue_number)
    comment_obj = issue.create_comment(comment)
    return comment_obj.html_url
