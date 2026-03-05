Pandora SWE CLI

A Claude Code-like terminal SWE agent built with LangChain DeepAgents.

Project Status: This project is currently a work in progress (WIP). The architecture and features are evolving rapidly. Expect breaking changes while core capabilities are being stabilized.

Features

Three-phase agentic loop: Gather Context → Take Action → Verify Results

Specialist subagents: code-explorer, code-architect, code-reviewer

Built-in tools: File operations, shell execution, search, git — all from DeepAgents framework

Human-in-the-loop: Approval required for destructive operations (shell, file writes)

Multi-provider LLM: Ollama Cloud (default), Groq, OpenRouter, Cerebras, local Ollama, Anthropic, Google Gemini — swap with one env var

LangSmith tracing: Optional observability for all agent actions

Beautiful terminal UI: Rich-powered REPL with streaming, tool call display, and inline approvals

Setup

1. Install dependencies

pip install -e .

# Optional: web search support
pip install -e ".[search]"

2. Configure environment

cp .env.example .env
# Edit .env with your API keys

3. Run

python -m src
# or
coding-agent

LLM Provider Configuration

Edit .env to switch providers:

Provider

LLM_PROVIDER

LLM_MODEL

Key Required

Ollama Cloud (default)

ollama_cloud

qwen2.5-coder:7b

OLLAMA_CLOUD_API_KEY

Groq

groq

llama-3.3-70b-versatile

GROQ_API_KEY

OpenRouter

openrouter

google/gemini-2.0-flash-001

OPENROUTER_API_KEY

Ollama (local)

ollama

llama3.2

None

Anthropic

anthropic

claude-sonnet-4-6

ANTHROPIC_API_KEY

Google Gemini

google_genai

gemini-2.5-flash-lite

GOOGLE_API_KEY

Architecture

User ──▶ Terminal REPL ──▶ Main Agent (create_deep_agent)
                              │
                              ├── Built-in Middleware
                              │   ├── TodoListMiddleware
                              │   ├── FilesystemMiddleware
                              │   ├── SubAgentMiddleware
                              │   ├── SummarizationMiddleware
                              │   └── HumanInTheLoopMiddleware
                              │
                              ├── CompositeBackend
                              │   ├── LocalShellBackend (project dir)
                              │   ├── StateBackend (/workspace/)
                              │   └── StoreBackend (/memories/)
                              │
                              └── Specialist Subagents
                                  ├── code-explorer
                                  ├── code-architect
                                  └── code-reviewer

REPL Commands

Command

Description

/clear

Clear screen

/status

Show current config

/model

Show current LLM provider

/retry

Retry last failed input

/help

Show all commands

/exit

Exit the agent

Project Structure

coding_agent/
├── pyproject.toml          # Dependencies & project config
├── .env.example            # Environment template
├── AGENTS.md               # Agent memory file
├── prompts/                # System prompts (loaded at runtime)
│   ├── main-agent.md
│   ├── subagent.md
│   ├── code-explorer.md
│   ├── code-architect.md
│   └── code-reviewer.md
└── src/
    ├── main.py             # CLI entry point
    ├── agent.py            # Agent assembly
    ├── backend.py          # CompositeBackend config
    ├── config.py           # Configuration
    ├── prompts.py          # Prompt loader
    ├── ui.py               # Terminal REPL
    └── tools/
        ├── ask_user.py     # User interaction
        ├── git.py          # Git wrappers
        ├── web_search.py   # Web search (optional)
        └── fallback.py     # Fallback tools

Contributing

Contributions are welcome. Since this project is still evolving, contributions that improve architecture, reliability, and developer ergonomics are especially valuable.

Areas where help is particularly useful:

Improving agent reasoning workflows

Adding new developer tools or integrations

Enhancing terminal UX

Expanding test coverage

Improving documentation

How to Contribute

Fork the repository

Create a feature branch

git checkout -b feature/your-feature-name

Make your changes

Run tests

pytest test/ -v

Submit a Pull Request describing the motivation and changes

Contribution Guidelines

Keep pull requests focused and small

Follow the existing project structure

Write tests for new functionality where possible

Ensure the CLI remains lightweight and responsive

If you want to discuss larger architectural changes, open an issue first so the direction can be aligned before implementation.

Testing

pip install -e ".[dev]"
pytest test/ -v

