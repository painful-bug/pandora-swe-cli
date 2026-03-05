import sys
from src.agent import create_coding_agent
from src.ui import (
    console,
    print_banner,
    handle_slash_command,
    run_agent_streaming,
    create_session,
    generate_thread_id,
)


def main():
    try:
        agent, checkpointer = create_coding_agent()
    except Exception as e:
        console.print(f"[error]Failed to initialize agent: {e}[/error]")
        sys.exit(1)

    print_banner()
    session = create_session()
    thread_id = generate_thread_id()
    config = {"configurable": {"thread_id": thread_id}}

    console.print(f"  [dim]Session: {thread_id[:8]}...[/dim]\n")

    last_input = ""

    while True:
        try:
            user_input = session.prompt("❯ ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            should_exit, should_retry = handle_slash_command(user_input, last_input)
            if should_exit:
                break
            if should_retry and last_input:
                user_input = last_input
            else:
                continue

        try:
            run_agent_streaming(agent, config, user_input)
            last_input = user_input
        except KeyboardInterrupt:
            console.print("\n[warning]Interrupted. Type /exit to quit.[/warning]")
        except Exception as e:
            last_input = user_input  # Save for /retry
            err_str = str(e).lower()
            if "connection" in err_str or "api_key" in err_str or "auth" in err_str or "401" in err_str:
                console.print(f"\n[error]Connection/auth error: {e}[/error]")
                console.print("[dim]Check your API key in .env — or switch providers:[/dim]")
                console.print("[dim]  LLM_PROVIDER=ollama_cloud  (cloud, needs OLLAMA_CLOUD_API_KEY)[/dim]")
                console.print("[dim]  LLM_PROVIDER=openrouter    (needs OPENROUTER_API_KEY)[/dim]")
                console.print("[dim]  LLM_PROVIDER=cerebras      (needs CEREBRAS_API_KEY)[/dim]")
                console.print("[dim]  LLM_PROVIDER=ollama        (local, no key needed)[/dim]")
            else:
                console.print(f"\n[error]Agent error: {e}[/error]")
                console.print("[dim]Type /retry to try again.[/dim]")


if __name__ == "__main__":
    main()
