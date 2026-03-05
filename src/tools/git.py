import subprocess
from langchain.tools import tool
from src.config import PROJECT_ROOT


def _run_git(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr:
            output += f"\nSTDERR: {result.stderr.strip()}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: git command timed out"
    except FileNotFoundError:
        return "Error: git is not installed"


@tool
def git_status() -> str:
    """Get the current git status showing changed, staged, and untracked files."""
    return _run_git(["status", "--short"])


@tool
def git_diff(staged: bool = False) -> str:
    """Show git diff of changes. Set staged=True to see staged changes only."""
    args = ["diff"]
    if staged:
        args.append("--cached")
    return _run_git(args)


@tool
def git_log(n: int = 10) -> str:
    """Show recent git commit history. Returns the last n commits."""
    return _run_git(["log", f"-{n}", "--oneline", "--graph"])


@tool
def git_commit(message: str) -> str:
    """Stage all changes and create a git commit with the given message."""
    stage_result = _run_git(["add", "-A"])
    if "Error" in stage_result:
        return stage_result
    return _run_git(["commit", "-m", message])


git_tools = [git_status, git_diff, git_log, git_commit]
