# Pandora SWE CLI

A Claude Code-like terminal SWE agent built with [LangChain DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview).

## Features

- **Three-phase agentic loop**: Gather Context → Take Action → Verify Results
- **Specialist subagents**: code-explorer, code-architect, code-reviewer
- **Built-in tools**: File operations, shell execution, search, git — all from DeepAgents framework
- **Human-in-the-loop**: Approval required for destructive operations (shell, file writes)
- **Multi-provider LLM**: Ollama Cloud (default), Groq, OpenRouter, Cerebras, local Ollama, Anthropic, Google Gemini — swap with one env var
- **LangSmith tracing**: Optional observability for all agent actions
- **Beautiful terminal UI**: Rich-powered REPL with streaming, tool call display, and inline approvals

## Setup

### 1. Install dependencies

```bash
pip install -e .

# Optional: web search support
pip install -e ".[search]"
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run

```bash
python -m src
# or
coding-agent
```

## LLM Provider Configuration

Edit `.env` to switch providers:

| Provider | `LLM_PROVIDER` | `LLM_MODEL` | Key Required |
|----------|----------------|-------------|-------------|
| **Ollama Cloud** (default) | `ollama_cloud` | `qwen2.5-coder:7b` | `OLLAMA_CLOUD_API_KEY` |
| Groq | `groq` | `llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| OpenRouter | `openrouter` | `google/gemini-2.0-flash-001` | `OPENROUTER_API_KEY` |
| Ollama (local) | `ollama` | `llama3.2` | None |
| Anthropic | `anthropic` | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |
| Google Gemini | `google_genai` | `gemini-2.5-flash-lite` | `GOOGLE_API_KEY` |

## Architecture

```
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
```

## REPL Commands

| Command | Description |
|---------|-------------|
| `/clear` | Clear screen |
| `/status` | Show current config |
| `/model` | Show current LLM provider |
| `/retry` | Retry last failed input |
| `/help` | Show all commands |
| `/exit` | Exit the agent |

## Project Structure

```
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
```

## Testing

```bash
pip install -e ".[dev]"
pytest test/ -v
```


this is the README.md of my repo.. add a section here for inviting other developers to contribute and also mention appropriately that this is a work in progress project