"""Tests for src/agent.py — agent creation and subagent configuration."""

import pytest
from unittest.mock import patch, MagicMock


class TestBuildSubagents:
    def test_count(self):
        from src.agent import build_subagents
        subagents = build_subagents()
        assert len(subagents) == 3

    def test_names(self):
        from src.agent import build_subagents
        subagents = build_subagents()
        names = {s["name"] for s in subagents}
        assert names == {"code-explorer", "code-architect", "code-reviewer"}

    def test_all_have_descriptions(self):
        from src.agent import build_subagents
        for sa in build_subagents():
            assert "description" in sa
            assert len(sa["description"]) > 20

    def test_all_have_system_prompts(self):
        from src.agent import build_subagents
        for sa in build_subagents():
            assert "system_prompt" in sa
            assert len(sa["system_prompt"]) > 50


class TestCreateCodingAgent:
    @patch("src.agent.create_deep_agent")
    @patch("src.agent.init_chat_model")
    def test_creates_agent_with_model(self, mock_init, mock_create):
        mock_model = MagicMock()
        mock_init.return_value = mock_model
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent

        from src.agent import create_coding_agent
        agent, checkpointer = create_coding_agent()

        mock_init.assert_called_once()
        mock_create.assert_called_once()
        assert agent == mock_agent

    @patch("src.agent.create_deep_agent")
    @patch("src.agent.init_chat_model")
    def test_passes_subagents(self, mock_init, mock_create):
        mock_init.return_value = MagicMock()
        mock_create.return_value = MagicMock()

        from src.agent import create_coding_agent
        create_coding_agent()

        call_kwargs = mock_create.call_args
        subagents = call_kwargs.kwargs.get("subagents", [])
        assert len(subagents) == 3

    @patch("src.agent.create_deep_agent")
    @patch("src.agent.init_chat_model")
    def test_has_name(self, mock_init, mock_create):
        mock_init.return_value = MagicMock()
        mock_create.return_value = MagicMock()

        from src.agent import create_coding_agent
        create_coding_agent()

        call_kwargs = mock_create.call_args
        assert call_kwargs.kwargs.get("name") == "main-agent"

    @patch("src.agent.create_deep_agent")
    @patch("src.agent.init_chat_model")
    def test_has_hitl_config(self, mock_init, mock_create):
        mock_init.return_value = MagicMock()
        mock_create.return_value = MagicMock()

        from src.agent import create_coding_agent
        create_coding_agent()

        call_kwargs = mock_create.call_args
        interrupt_on = call_kwargs.kwargs.get("interrupt_on", {})
        assert "execute" in interrupt_on
        assert isinstance(interrupt_on["execute"], dict)
        assert interrupt_on["execute"]["allowed_decisions"] == ["approve", "edit", "reject"]
