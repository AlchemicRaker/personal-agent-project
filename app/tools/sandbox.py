import docker
import uuid
from dotenv import load_dotenv

load_dotenv()

def run_in_sandbox(code: str, timeout: int = 30) -> dict:
    """Run Python code in isolated Docker container."""
    container_name = f"sandbox-{uuid.uuid4().hex[:8]}"
    
    try:
        # Lazy client creation - only happens when the tool is actually used
        client = docker.from_env(timeout=10)
        
        cmd = f"""
import sys
exec('''{code}''')
"""
        container = client.containers.run(
            "software-engineer-sandbox",
            command=["python", "-c", cmd],
            name=container_name,
            remove=True,
            mem_limit="512m",
            cpu_shares=512,
            network_disabled=True,
            stdout=True,
            stderr=True,
            tty=True,
            detach=False,
            timeout=timeout
        )
        output = container.decode("utf-8") if isinstance(container, bytes) else str(container)
        return {"success": True, "output": output.strip(), "error": None}
        
    except Exception as e:
        error_msg = str(e)
        if "FileNotFoundError" in error_msg or "No such file or directory" in error_msg:
            error_msg = "Docker daemon not reachable. Make sure Docker Desktop is running and the socket setting is enabled."
        return {"success": False, "output": None, "error": error_msg}