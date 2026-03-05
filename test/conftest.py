"""Shared fixtures for the coding agent test suite."""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_env(monkeypatch):
    """Provide a clean env for config tests — clears all LLM-related vars."""
    vars_to_clear = [
        "LLM_PROVIDER", "LLM_MODEL",
        "OLLAMA_BASE_URL", "OLLAMA_MODEL",
        "OLLAMA_CLOUD_BASE_URL", "OLLAMA_CLOUD_API_KEY",
        "OPENROUTER_API_KEY",
        "GROQ_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
        "LANGSMITH_TRACING", "MAX_RETRIES",
        "TAVILY_API_KEY",
    ]
    for var in vars_to_clear:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory with sample files."""
    (tmp_path / "hello.py").write_text("print('hello world')\n")
    (tmp_path / "data.txt").write_text("line1\nline2\nline3\nline4\nline5\n")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.py").write_text("# nested\n")
    return tmp_path


@pytest.fixture
def mock_agent():
    """Mock LangGraph compiled agent for UI tests."""
    agent = MagicMock()
    agent.stream.return_value = iter([])
    state = MagicMock()
    state.values = {"messages": []}
    agent.get_state.return_value = state
    return agent


@pytest.fixture
def mock_config():
    """Standard config dict for agent invocations."""
    return {"configurable": {"thread_id": "test-thread-001"}}
