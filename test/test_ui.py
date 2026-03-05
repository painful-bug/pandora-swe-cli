"""Tests for src/ui.py — tool info extraction, event processing, slash commands."""

import pytest
from unittest.mock import MagicMock, patch
from io import StringIO


class TestExtractToolInfo:
    def test_from_value_dict(self):
        from src.ui import _extract_tool_info

        interrupt = MagicMock()
        interrupt.value = {"tool": "read_file", "args": {"path": "/tmp/test.py"}}
        agent = MagicMock()
        config = {}

        name, args = _extract_tool_info(interrupt, agent, config)
        assert name == "read_file"
        assert args == {"path": "/tmp/test.py"}

    def test_from_value_name_key(self):
        from src.ui import _extract_tool_info

        interrupt = MagicMock()
        interrupt.value = {"name": "execute", "input": {"command": "ls"}}
        agent = MagicMock()
        config = {}

        name, args = _extract_tool_info(interrupt, agent, config)
        assert name == "execute"
        assert args == {"command": "ls"}

    def test_from_value_object(self):
        from src.ui import _extract_tool_info

        val = MagicMock()
        val.name = "write_file"
        val.args = {"path": "/tmp/out.txt", "content": "hello"}
        interrupt = MagicMock()
        interrupt.value = val
        agent = MagicMock()
        config = {}

        name, args = _extract_tool_info(interrupt, agent, config)
        assert name == "write_file"

    def test_fallback_to_agent_state(self):
        from src.ui import _extract_tool_info

        interrupt = MagicMock()
        interrupt.value = None
        agent = MagicMock()
        config = {"configurable": {"thread_id": "t1"}}

        # Simulate agent state with pending tool call
        msg = MagicMock()
        msg.tool_calls = [{"name": "edit_file", "args": {"path": "x.py"}}]
        state = MagicMock()
        state.values = {"messages": [msg]}
        agent.get_state.return_value = state

        name, args = _extract_tool_info(interrupt, agent, config)
        assert name == "edit_file"
        assert args == {"path": "x.py"}

    def test_returns_unknown_on_failure(self):
        from src.ui import _extract_tool_info

        interrupt = MagicMock()
        interrupt.value = None
        agent = MagicMock()
        agent.get_state.side_effect = Exception("no state")
        config = {}

        name, args = _extract_tool_info(interrupt, agent, config)
        assert name == "unknown"
        assert args == {}


class TestSlashCommands:
    def test_exit(self):
        from src.ui import handle_slash_command
        should_exit, should_retry = handle_slash_command("/exit")
        assert should_exit is True
        assert should_retry is False

    def test_unknown_command(self):
        from src.ui import handle_slash_command
        should_exit, should_retry = handle_slash_command("/foobar")
        assert should_exit is False
        assert should_retry is False

    def test_retry_with_last_input(self):
        from src.ui import handle_slash_command
        should_exit, should_retry = handle_slash_command("/retry", "fix the bug")
        assert should_exit is False
        assert should_retry is True

    def test_retry_without_last_input(self):
        from src.ui import handle_slash_command
        should_exit, should_retry = handle_slash_command("/retry", "")
        assert should_exit is False
        assert should_retry is False

    def test_help(self):
        from src.ui import handle_slash_command
        should_exit, should_retry = handle_slash_command("/help")
        assert should_exit is False

    def test_clear(self):
        from src.ui import handle_slash_command
        should_exit, should_retry = handle_slash_command("/clear")
        assert should_exit is False

    def test_status(self):
        from src.ui import handle_slash_command
        should_exit, should_retry = handle_slash_command("/status")
        assert should_exit is False


class TestHitlApproval:
    def test_auto_approve_non_execute(self):
        from src.ui import prompt_hitl_approval
        decision, edited = prompt_hitl_approval("task", {"description": "delegate"})
        assert decision == "approve"
        assert edited is None

    def test_auto_approve_safe_execute(self):
        from src.ui import prompt_hitl_approval
        decision, edited = prompt_hitl_approval("execute", {"command": "ls -la"})
        assert decision == "approve"
        assert edited is None

    @patch("src.ui.console.input", return_value="n")
    def test_prompt_on_dangerous_execute(self, _mock_input):
        from src.ui import prompt_hitl_approval
        decision, edited = prompt_hitl_approval("execute", {"command": "rm -rf /tmp/demo"})
        assert decision == "reject"
        assert edited is None


class TestProcessNode:
    def test_renders_tool_calls(self):
        from src.ui import _process_node_event

        msg = MagicMock()
        msg.tool_calls = [{"name": "read_file", "args": {"path": "test.py"}}]
        msg.content = ""
        msg.type = "ai"

        node_data = {"messages": [msg]}
        # Should not crash
        _process_node_event("agent", node_data, {"subagent": None, "namespace": ()})

    def test_renders_ai_content(self):
        from src.ui import _process_node_event

        msg = MagicMock()
        msg.tool_calls = []
        msg.content = "Here is the fix for your bug."
        msg.type = "ai"

        node_data = {"messages": [msg]}
        # Should not crash
        _process_node_event("agent", node_data, {"subagent": None, "namespace": ()})

    def test_renders_tool_result(self):
        from src.ui import _process_node_event

        msg = MagicMock()
        msg.tool_calls = []
        msg.content = "line1\nline2\nline3\nline4\nline5"
        msg.type = "tool"

        node_data = {"messages": [msg]}
        # Should not crash — tool results are truncated
        _process_node_event("tools", node_data, {"subagent": None, "namespace": ()})

    def test_handles_none_messages(self):
        from src.ui import _process_node_event
        # Empty messages list
        _process_node_event("agent", {"messages": []}, {"subagent": None, "namespace": ()})
        # No messages key
        _process_node_event("agent", {}, {"subagent": None, "namespace": ()})


class TestHelpers:
    def test_extract_agent_name_from_str(self):
        from src.ui import _extract_agent_name_from_str
        assert _extract_agent_name_from_str("(('abc', 'code-explorer'),)") == "code-explorer"
        assert _extract_agent_name_from_str("something-else") == "subagent"

    def test_generate_thread_id(self):
        from src.ui import generate_thread_id
        tid = generate_thread_id()
        assert len(tid) == 36  # UUID format
        assert "-" in tid
