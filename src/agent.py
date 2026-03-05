from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langchain.agents.middleware import ToolCallLimitMiddleware, ModelCallLimitMiddleware

from src.config import get_model_string, get_model_kwargs, HITL_TOOLS
from src.prompts import load_prompt
from src.backend import create_composite_backend
from src.tools.ask_user import ask_user_question
from src.tools.git import git_tools
from src.tools.web_search import get_search_tools


def build_subagents() -> list[dict]:
    return [
        {
            "name": "code-explorer",
            "description": (
                "Deeply analyzes existing codebase features by tracing execution paths, "
                "mapping architecture layers, understanding patterns, and documenting dependencies."
            ),
            "system_prompt": load_prompt("code-explorer"),
        },
        {
            "name": "code-architect",
            "description": (
                "Designs feature architectures by analyzing existing codebase patterns and conventions, "
                "then providing comprehensive implementation blueprints with specific files to create/modify."
            ),
            "system_prompt": load_prompt("code-architect"),
        },
        {
            "name": "code-reviewer",
            "description": (
                "Reviews code for bugs, logic errors, security vulnerabilities, and code quality issues, "
                "using confidence-based filtering to report only high-priority issues."
            ),
            "system_prompt": load_prompt("code-reviewer"),
        },
    ]


def create_coding_agent():
    model_string = get_model_string()
    model_kwargs = get_model_kwargs()

    model = init_chat_model(model_string, **model_kwargs)

    custom_tools = [ask_user_question] + git_tools + get_search_tools()

    checkpointer = MemorySaver()
    store = InMemoryStore()

    from src.config import PROJECT_ROOT
    base_prompt = load_prompt("main-agent")
    system_prompt = f"{base_prompt}\n\nCurrent Working Directory: {PROJECT_ROOT}\n"

    agent = create_deep_agent(
        model=model,
        name="main-agent",
        system_prompt=system_prompt,
        tools=custom_tools,
        subagents=build_subagents(),
        backend=create_composite_backend,
        interrupt_on=HITL_TOOLS,
        memory=["/AGENTS.md"],
        checkpointer=checkpointer,
        store=store,
        middleware=[
            # ToolCallLimitMiddleware(thread_limit=20, run_limit=10),
            # ModelCallLimitMiddleware(
            #     thread_limit=10,
            #     run_limit=25,
            #     exit_behavior="end",
            # ),
        ]
    )

    return agent, checkpointer
