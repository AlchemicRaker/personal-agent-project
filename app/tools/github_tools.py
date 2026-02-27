from github import Github, GithubException
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize GitHub client with validation
token = os.getenv("GITHUB_TOKEN")
if not token:
    raise ValueError("GITHUB_TOKEN environment variable is not set")

try:
    g = Github(token)
    logger.info("GitHub client initialized successfully")
except GithubException as ge:
    logger.error(f"GitHub authentication failed: {ge}")
    raise ValueError(f"GitHub authentication failed: {ge.data.get('message', str(ge))}")
except Exception as e:
    logger.error(f"Unexpected error initializing GitHub client: {e}")
    raise ValueError(f"Failed to initialize GitHub client: {str(e)}")

def validate_repo_name(repo_full_name: str) -> bool:
    """Validate repo_full_name format (owner/repo)."""
    if not repo_full_name or '/' not in repo_full_name or repo_full_name.count('/') != 1:
        return False
    return True

def list_repo_files(repo_full_name: str, branch: str = "main"):
    """List files in a repo."""
    if not validate_repo_name(repo_full_name):
        logger.warning(f"Invalid repo_full_name: {repo_full_name}")
        return "Error: Invalid repository name format (expected owner/repo)"
    
    try:
        repo = g.get_repo(repo_full_name)
        contents = repo.get_contents("", ref=branch)
        files = [c.path for c in contents if not c.path.endswith(".git")]
        logger.info(f"Listed {len(files)} files in {repo_full_name}:{branch}")
        return files
    except GithubException as ge:
        logger.warning(f"GitHub error in list_repo_files({repo_full_name}): {ge}")
        return f"GitHub error: {ge.data.get('message', str(ge))}"
    except Exception as e:
        logger.error(f"Unexpected error in list_repo_files({repo_full_name}): {e}")
        return f"Error: {str(e)}"

def read_file(repo_full_name: str, file_path: str, branch: str = "main"):
    """Read file content."""
    if not validate_repo_name(repo_full_name):
        logger.warning(f"Invalid repo_full_name: {repo_full_name}")
        return "Error: Invalid repository name format (expected owner/repo)"
    if not file_path:
        logger.warning("Empty file_path provided")
        return "Error: file_path cannot be empty"
    
    try:
        repo = g.get_repo(repo_full_name)
        file_content = repo.get_contents(file_path, ref=branch)
        content = file_content.decoded_content.decode("utf-8")
        logger.info(f"Read file {file_path} from {repo_full_name}:{branch}")
        return content
    except GithubException as ge:
        logger.warning(f"GitHub error in read_file({repo_full_name}/{file_path}): {ge}")
        return f"GitHub error: {ge.data.get('message', str(ge))}"
    except Exception as e:
        logger.error(f"Unexpected error in read_file({repo_full_name}/{file_path}): {e}")
        return f"Error: {str(e)}"

def create_pr(repo_full_name: str, title: str, body: str, branch_name: str, files_to_change: dict):
    """Create branch + commit + PR. files_to_change = {'path': 'new_content', 'path/to/delete': None}"""
    if not validate_repo_name(repo_full_name):
        logger.warning(f"Invalid repo_full_name: {repo_full_name}")
        return "Error: Invalid repository name format (expected owner/repo)"
    if not isinstance(files_to_change, dict):
        logger.warning("files_to_change must be a dict")
        return "Error: files_to_change must be a dictionary"
    if not title or not branch_name:
        logger.warning("title or branch_name missing")
        return "Error: title and branch_name are required"
    
    try:
        repo = g.get_repo(repo_full_name)
        # Create branch
        main = repo.get_branch("main")
        ref = repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main.commit.sha)
        
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
                    logger.info(f"File {path} not found for deletion, skipping")
                    continue
                elif "not found" in error_msg:
                    # file not found, create new
                    repo.create_file(path, f"Add {path}", content, branch=branch_name)
                else:
                    logger.warning(f"Error handling file {path}: {ge}")
                    raise
        
        # Create PR
        pr = repo.create_pull(title=title, body=body, head=branch_name, base="main")
        logger.info(f"PR created successfully: {pr.html_url}")
        return f"PR created: {pr.html_url}"
    except GithubException as ge:
        logger.warning(f"GitHub error in create_pr({repo_full_name}): {ge}")
        return f"GitHub error: {ge.data.get('message', str(ge))}"
    except Exception as e:
        logger.error(f"Unexpected error in create_pr({repo_full_name}): {e}")
        return f"Error creating PR: {str(e)}"