"""
Terminal REPL UI — Claude Code CLI-like interface.

Features:
  - Compact one-line tool call display
  - Agent handoff indicators (→ / ←)
  - Auto-scrolling, scrollable rich console output
  - Spinner during LLM thinking
  - HITL approval inline
  - Error resilience with retry + error feedback
"""

import uuid
import time
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.status import Status
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from pathlib import Path

from src.config import LLM_PROVIDER, LLM_MODEL, PROJECT_ROOT, MAX_RETRIES

HISTORY_FILE = Path.home() / ".coding_agent_history"

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "tool": "bold magenta",
    "dim": "dim white",
    "handoff": "bold cyan",
    "result": "green",
    "retry": "bold yellow",
})

console = Console(theme=custom_theme, force_terminal=True)

# ── Display helpers ─────────────────────────────────────────────


def print_banner():
    banner_text = Text()
    banner_text.append("  ╔═══════════════════════════════════════╗\n", style="bold cyan")
    banner_text.append("  ║        ", style="bold cyan")
    banner_text.append("⚡ Coding Agent", style="bold white")
    banner_text.append("                 ║\n", style="bold cyan")
    banner_text.append("  ║        ", style="bold cyan")
    banner_text.append("powered by DeepAgents", style="dim")
    banner_text.append("         ║\n", style="bold cyan")
    banner_text.append("  ╚═══════════════════════════════════════╝", style="bold cyan")
    console.print(banner_text)
    console.print(f"  [dim]Provider:[/dim] [bold]{LLM_PROVIDER}[/bold]  [dim]Model:[/dim] [bold]{LLM_MODEL}[/bold]")
    console.print(f"  [dim]Project:[/dim]  [bold]{PROJECT_ROOT.name}[/bold]")
    console.print(f"  [dim]Commands:[/dim] /help  /clear  /status  /model  /retry  /exit\n")


def print_tool_call(name: str, args: dict, indent: int = 0):
    """Compact one-line tool call — mimics Claude Code style."""
    prefix = "  " * (indent + 1)
    parts = []
    for k, v in args.items():
        v_str = repr(v) if isinstance(v, str) else str(v)
        if len(v_str) > 60:
            v_str = v_str[:57] + "..."
        parts.append(f'{k}={v_str}')
    args_str = " ".join(parts)
    console.print(f"{prefix}[tool]⚙ {name}[/tool] {args_str}", highlight=False)


def print_tool_result(result: str, indent: int = 0):
    """Show tool result, truncated to first 3 lines with overflow count."""
    prefix = "  " * (indent + 1)
    if not result or not result.strip():
        console.print(f"{prefix}[result]✓[/result] [dim](no output)[/dim]")
        return
    lines = result.strip().splitlines()
    if len(lines) <= 3:
        for line in lines:
            console.print(f"{prefix}  [dim]{line}[/dim]")
    else:
        for line in lines[:3]:
            console.print(f"{prefix}  [dim]{line}[/dim]")
        console.print(f"{prefix}  [dim](+{len(lines) - 3} more lines)[/dim]")


def print_agent_response(content: str):
    if content and content.strip():
        console.print()
        console.print(Markdown(content))
        console.print()


def print_handoff(agent_name: str, direction: str = "to"):
    """Show subagent handoff indicator."""
    if direction == "to":
        console.print(f"\n  [handoff]→ {agent_name}[/handoff]")
    else:
        console.print(f"  [handoff]← {agent_name}[/handoff]\n")


def print_retry(attempt: int, max_retries: int, error: str):
    """Show retry indicator."""
    console.print(f"  [retry]⟳ Retry {attempt}/{max_retries}:[/retry] [dim]{error}[/dim]")


# ── HITL approval ───────────────────────────────────────────────


def prompt_hitl_approval(tool_name: str, tool_args: dict) -> tuple[str, dict | None]:
    """Compact inline HITL approval prompt with auto-approval for non-dangerous commands."""
    from src.config import DANGEROUS_PATTERNS

    # Auto-approve everything except dangerous shell commands.
    if tool_name != "execute":
        return "approve", None

    if not isinstance(tool_args, dict):
        tool_args = {}

    command = str(tool_args.get("command", ""))
    is_dangerous = any(pat in command.lower() for pat in DANGEROUS_PATTERNS)
    if not is_dangerous:
        return "approve", None

    # Show args concisely
    args_preview = ", ".join(f"{k}={repr(v)[:40]}" for k, v in tool_args.items())
    console.print(Panel(
        f"[warning]Tool:[/warning] [bold]{tool_name}[/bold]({args_preview})",
        title="[bold yellow]⚠ Approval Required[/bold yellow]",
        border_style="yellow",
        padding=(0, 1),
    ))
    console.print("  [bold][Y][/bold]es  [bold][N][/bold]o  [bold][E][/bold]dit")

    while True:
        choice = console.input("  [bold]> [/bold]").strip().lower()
        if choice in ("y", "yes", ""):
            return "approve", None
        elif choice in ("n", "no"):
            return "reject", None
        elif choice in ("e", "edit"):
            console.print("  [dim]Enter modified args as key=value (one per line, empty to finish):[/dim]")
            edits = {}
            while True:
                line = console.input("    ").strip()
                if not line:
                    break
                if "=" in line:
                    k, v = line.split("=", 1)
                    edits[k.strip()] = v.strip()
            modified = {**tool_args, **edits}
            return "approve", modified
        else:
            console.print("  [error]Invalid choice. Enter Y, N, or E.[/error]")


# ── Slash commands ──────────────────────────────────────────────


def handle_slash_command(command: str, last_input: str = "") -> tuple[bool, bool]:
    """Handle slash commands. Returns (should_exit, should_retry)."""
    cmd = command.strip().lower()
    if cmd == "/exit":
        console.print("[dim]Goodbye![/dim]")
        return True, False
    elif cmd == "/clear":
        console.clear()
        print_banner()
    elif cmd == "/status":
        console.print(f"  [info]Provider:[/info] {LLM_PROVIDER}")
        console.print(f"  [info]Model:[/info]    {LLM_MODEL}")
        console.print(f"  [info]Project:[/info]  {PROJECT_ROOT}")
        console.print(f"  [info]Retries:[/info]  {MAX_RETRIES}")
    elif cmd == "/model":
        console.print(f"  [info]Current:[/info] {LLM_PROVIDER}:{LLM_MODEL}")
        console.print("  [dim]Change by editing LLM_PROVIDER and LLM_MODEL in .env[/dim]")
    elif cmd == "/retry":
        if last_input:
            return False, True
        else:
            console.print("  [dim]Nothing to retry.[/dim]")
    elif cmd == "/help":
        console.print("  [bold]Available commands:[/bold]")
        console.print("  [info]/clear[/info]   Clear screen")
        console.print("  [info]/status[/info]  Show current config")
        console.print("  [info]/model[/info]   Show current LLM provider/model")
        console.print("  [info]/retry[/info]   Retry last failed input")
        console.print("  [info]/help[/info]    Show this help")
        console.print("  [info]/exit[/info]    Exit the agent")
    else:
        console.print(f"  [error]Unknown command: {command}[/error]")
    return False, False


# ── Agent streaming with HITL + retry ───────────────────────────


def run_agent_streaming(agent, config: dict, user_input: str):
    """Run agent with error resilience: retry up to MAX_RETRIES with
    error feedback injection so the LLM can adapt its approach."""
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if attempt == 1 or last_error is None:
                input_val = {"messages": [{"role": "user", "content": user_input}]}
            else:
                # Inject error feedback so the LLM tries a different approach
                error_feedback = (
                    f"The previous attempt failed with error: {last_error}. "
                    f"Please try a different approach to accomplish the task."
                )
                input_val = {"messages": [{"role": "user", "content": error_feedback}]}

            with Status("[dim]Thinking...[/dim]", console=console, spinner="dots"):
                # Start stream — spinner disappears on first output
                events = list(_collect_initial_events(agent, config, input_val))

            # Process all collected events
            for event_type, event_data in events:
                if event_type == "hitl":
                    intr, agent_ref, config_ref = event_data
                    _handle_interrupt(intr, agent_ref, config_ref)
                elif event_type == "node":
                    node_name, node_data, metadata = event_data
                    _process_node_event(node_name, node_data, metadata)

            return  # Success — exit retry loop

        except KeyboardInterrupt:
            raise  # Let caller handle Ctrl-C
        except Exception as e:
            last_error = str(e)
            if attempt < MAX_RETRIES:
                # Classify: fatal errors don't retry
                err_lower = last_error.lower()
                if any(kw in err_lower for kw in ("api_key", "auth", "401", "403", "invalid")):
                    raise  # Fatal — don't retry
                print_retry(attempt, MAX_RETRIES, last_error)
                time.sleep(min(attempt * 0.5, 3))  # gentle backoff
            else:
                raise  # All retries exhausted


def _collect_initial_events(agent, config, input_val):
    """Stream agent events and yield them for processing.
    Uses stream_subgraphs=True to capture subagent handoffs."""
    from langgraph.types import Command

    active_subagent = None

    for event in agent.stream(
        input_val,
        config=config,
        stream_mode="updates",
        subgraphs=True,
    ):
        # With subgraphs=True, events are (namespace_tuple, event_dict)
        if isinstance(event, tuple) and len(event) == 2:
            namespace, evt = event
        else:
            namespace, evt = (), event

        if not isinstance(evt, dict):
            continue

        # Detect subagent from namespace
        current_agent = None
        if namespace:
            # namespace is a tuple of (graph_id, node_name, ...) pairs
            # The subagent name is typically in the namespace
            ns_str = str(namespace)
            current_agent = ns_str

        # Print handoff indicators
        if current_agent and current_agent != active_subagent:
            if active_subagent:
                print_handoff(active_subagent, direction="from")
            # Extract a readable agent name from namespace
            agent_label = _extract_agent_name(namespace)
            print_handoff(agent_label, direction="to")
            active_subagent = current_agent
        elif not current_agent and active_subagent:
            agent_label = _extract_agent_name_from_str(active_subagent)
            print_handoff(agent_label, direction="from")
            active_subagent = None

        if not isinstance(evt, dict):
            continue

        for node_name, node_data in evt.items():
            if node_name == "__interrupt__":
                for intr in (node_data if isinstance(node_data, list) else [node_data]):
                    yield ("hitl", (intr, agent, config))
            elif node_data is not None:
                metadata = {"namespace": namespace, "subagent": active_subagent}
                yield ("node", (node_name, node_data, metadata))

    # Close any open subagent
    if active_subagent:
        agent_label = _extract_agent_name_from_str(active_subagent)
        print_handoff(agent_label, direction="from")


def _handle_interrupt(interrupt, agent, config):
    """Handle a single HITL interrupt: extract info, prompt, resume."""
    from langgraph.types import Command

    val = getattr(interrupt, "value", {})
    
    # Safely extract action_requests whether val is dict or object
    action_requests = None
    if isinstance(val, dict):
        action_requests = val.get("action_requests")
    elif hasattr(val, "action_requests"):
        action_requests = getattr(val, "action_requests")

    if action_requests is not None:
        actions = action_requests if isinstance(action_requests, list) else [action_requests]
        decisions = []
        for action in actions:
            # handle dict or object items inside action_requests
            tool_name = action.get("name", "unknown") if isinstance(action, dict) else getattr(action, "name", "unknown")
            tool_args = action.get("args", {}) if isinstance(action, dict) else getattr(action, "args", {})
            if not isinstance(tool_args, dict):
                tool_args = {}

            decision, edited_args = prompt_hitl_approval(tool_name, tool_args)
            if decision == "approve":
                if edited_args:
                    decisions.append({
                        "type": "edit",
                        "edited_action": {"name": tool_name, "args": edited_args}
                    })
                else:
                    decisions.append({"type": "approve"})
            else:
                decisions.append({"type": "reject"})
        resume_val = {"decisions": decisions}
    else:
        # Fallback for non-DeepAgents interrupts
        tool_name, tool_args = _extract_tool_info(interrupt, agent, config)
        decision, edited_args = prompt_hitl_approval(tool_name, tool_args)
        if decision == "approve":
            resume_val = edited_args if edited_args else True
        else:
            resume_val = False

    # Resume and process any further events (including nested interrupts)
    for event in agent.stream(
        Command(resume=resume_val),
        config=config,
        stream_mode="updates",
        subgraphs=True,
    ):
        if isinstance(event, tuple) and len(event) == 2:
            namespace, evt = event
        else:
            namespace, evt = (), event

        if not isinstance(evt, dict):
            continue

        for node_name, node_data in evt.items():
            if node_name == "__interrupt__":
                for intr in (node_data if isinstance(node_data, list) else [node_data]):
                    _handle_interrupt(intr, agent, config)
            elif node_data is not None:
                metadata = {"namespace": namespace, "subagent": None}
                _process_node_event(node_name, node_data, metadata)


def _extract_tool_info(interrupt, agent, config) -> tuple[str, dict]:
    """Extract tool name and args from a LangGraph Interrupt object."""
    tool_name = "unknown"
    tool_args = {}

    # Try interrupt.value (may be a dict or an object with attributes)
    val = getattr(interrupt, "value", None)
    if isinstance(val, dict):
        tool_name = val.get("tool", val.get("name", tool_name))
        tool_args = val.get("args", val.get("input", tool_args))
    elif val is not None and hasattr(val, "name"):
        tool_name = getattr(val, "name", tool_name)
        tool_args = getattr(val, "args", tool_args)
    if not isinstance(tool_args, dict):
        tool_args = {}

    # Fallback: read pending tool calls from agent state
    if tool_name == "unknown":
        try:
            state = agent.get_state(config)
            for msg in reversed(state.values.get("messages", [])):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tc = msg.tool_calls[0]
                    tool_name = tc.get("name", tool_name)
                    tool_args = tc.get("args", tool_args)
                    if not isinstance(tool_args, dict):
                        tool_args = {}
                    break
        except Exception:
            pass

    return tool_name, tool_args


def _process_node_event(node_name: str, node_data: dict, metadata: dict):
    """Process a single node's output — compact tool calls and AI responses."""
    indent = 1 if metadata.get("subagent") else 0

    messages = node_data.get("messages", [])
    if not isinstance(messages, list):
        messages = [messages]

    for msg in messages:
        # Tool calls (AI requesting tool use)
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                print_tool_call(
                    tc.get("name", "?"),
                    tc.get("args", {}),
                    indent=indent,
                )

        # Tool results
        if hasattr(msg, "type") and msg.type == "tool":
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                print_tool_result(content, indent=indent)

        # AI text responses
        if hasattr(msg, "content") and msg.content:
            if hasattr(msg, "type") and msg.type == "ai":
                # Skip if content is just tool_calls with no text
                if not (hasattr(msg, "tool_calls") and msg.tool_calls and not msg.content.strip()):
                    print_agent_response(msg.content)


def _extract_agent_name(namespace) -> str:
    """Extract a readable agent name from a LangGraph namespace tuple."""
    if not namespace:
        return "subagent"
    # namespace is typically like (('graph_id', 'node_name'), ...)
    # Try to find a meaningful name
    for part in namespace:
        if isinstance(part, (list, tuple)) and len(part) >= 2:
            name = str(part[1])
            if name and name not in ("__start__", "__end__"):
                return name
        elif isinstance(part, str):
            if part not in ("__start__", "__end__"):
                return part
    return "subagent"


def _extract_agent_name_from_str(ns_str: str) -> str:
    """Extract readable name from a stringified namespace."""
    # Try to find agent name patterns like 'code-explorer'
    for name in ("code-explorer", "code-architect", "code-reviewer"):
        if name in ns_str:
            return name
    return "subagent"


# ── Session helpers ─────────────────────────────────────────────


def create_session() -> PromptSession:
    return PromptSession(history=FileHistory(str(HISTORY_FILE)))


def generate_thread_id() -> str:
    return str(uuid.uuid4())
