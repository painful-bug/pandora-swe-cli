# AGENTS.md — Coding Agent Memory

This file is loaded at the start of each agent session to provide project context.

## Project Overview

This is a terminal-based coding agent built with LangChain DeepAgents. It assists with codebase understanding, modification, and development tasks through a three-phase agentic loop.

## Conventions

- Python 3.11+
- Use type hints consistently
- Minimal comments — code should be self-documenting
- Keep modules focused and small
- System prompts live in `prompts/` as markdown files
- Custom tools go in `src/tools/`

## Key Architecture Decisions

- **Framework-first**: Use DeepAgents built-in middleware and backends wherever possible
- **CompositeBackend**: LocalShellBackend (default) + StateBackend (/workspace/) + StoreBackend (/memories/)
- **HITL**: All shell execution and file writes require user approval
- **Subagents**: Delegate deep analysis, architecture, and review to specialists
- **Groq default**: Fast inference via Groq, swappable to Ollama/Anthropic/Gemini in .env
