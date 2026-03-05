from langchain.tools import tool
from rich.console import Console
from rich.prompt import Prompt

console = Console()


@tool
def ask_user_question(question: str, options: str = "") -> str:
    """Ask the user a question to gather requirements or clarify ambiguity.
    Provide options as a comma-separated string for multiple choice, or leave empty for free-form input."""
    console.print(f"\n[bold cyan]🤔 Agent Question:[/bold cyan]")
    console.print(f"  {question}")

    if options:
        choices = [o.strip() for o in options.split(",")]
        for i, choice in enumerate(choices, 1):
            console.print(f"  [dim]{i}.[/dim] {choice}")
        answer = Prompt.ask("\n[bold]Your answer[/bold]")
    else:
        answer = Prompt.ask("\n[bold]Your answer[/bold]")

    return answer
