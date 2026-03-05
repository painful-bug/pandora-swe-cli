import subprocess
from pathlib import Path
from langchain.tools import tool
from src.config import PROJECT_ROOT


@tool
def fallback_bash(command: str, timeout: int = 30) -> str:
    """Fallback shell command execution. Use only if the built-in execute tool is unavailable."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        output += f"\nEXIT CODE: {result.returncode}"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s"


@tool
def fallback_read_file(path: str, offset: int = 0, limit: int = 200) -> str:
    """Fallback file reader. Use only if the built-in read_file tool is unavailable."""
    try:
        target = Path(path)
        if not target.is_absolute():
            target = PROJECT_ROOT / target
        content = target.read_text(encoding="utf-8")
        lines = content.splitlines()
        selected = lines[offset:offset + limit]
        result = f"[Lines {offset+1}-{offset+len(selected)} of {len(lines)}]\n"
        result += "\n".join(selected)
        return result
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def fallback_write_file(path: str, content: str) -> str:
    """Fallback file writer. Use only if the built-in write_file tool is unavailable."""
    try:
        target = Path(path)
        if not target.is_absolute():
            target = PROJECT_ROOT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Written {len(content)} bytes to {target}"
    except Exception as e:
        return f"Error writing file: {e}"


fallback_tools = [fallback_bash, fallback_read_file, fallback_write_file]
