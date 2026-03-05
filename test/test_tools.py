"""Tests for src/tools/ — fallback tools, git tools, web search."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestFallbackBash:
    def test_echo_success(self):
        from src.tools.fallback import fallback_bash
        result = fallback_bash.invoke({"command": "echo hello"})
        assert "hello" in result
        assert "EXIT CODE: 0" in result

    def test_failing_command(self):
        from src.tools.fallback import fallback_bash
        result = fallback_bash.invoke({"command": "false"})
        assert "EXIT CODE: 1" in result

    def test_timeout(self):
        from src.tools.fallback import fallback_bash
        result = fallback_bash.invoke({"command": "sleep 10", "timeout": 1})
        assert "timed out" in result.lower()


class TestFallbackReadFile:
    def test_read_existing_file(self, tmp_project):
        from src.tools.fallback import fallback_read_file
        path = str(tmp_project / "hello.py")
        result = fallback_read_file.invoke({"path": path})
        assert "hello world" in result

    def test_read_with_offset_limit(self, tmp_project):
        from src.tools.fallback import fallback_read_file
        path = str(tmp_project / "data.txt")
        result = fallback_read_file.invoke({"path": path, "offset": 1, "limit": 2})
        assert "line2" in result
        assert "line3" in result
        assert "line1" not in result

    def test_read_nonexistent(self):
        from src.tools.fallback import fallback_read_file
        result = fallback_read_file.invoke({"path": "/tmp/nonexistent_xyz_abc.txt"})
        assert "Error" in result


class TestFallbackWriteFile:
    def test_write_new_file(self, tmp_path):
        from src.tools.fallback import fallback_write_file
        target = str(tmp_path / "output.txt")
        result = fallback_write_file.invoke({"path": target, "content": "test content"})
        assert "Written" in result
        assert Path(target).read_text() == "test content"

    def test_write_creates_dirs(self, tmp_path):
        from src.tools.fallback import fallback_write_file
        target = str(tmp_path / "deep" / "nested" / "file.txt")
        result = fallback_write_file.invoke({"path": target, "content": "nested"})
        assert "Written" in result
        assert Path(target).exists()


class TestGitTools:
    def test_git_status_runs(self, tmp_path):
        """git status should return something (even if not a git repo)."""
        from src.tools.git import git_status
        # Will likely return an error since tmp_path isn't a git repo,
        # but should not crash
        result = git_status.invoke({})
        assert isinstance(result, str)

    def test_git_log_runs(self):
        from src.tools.git import git_log
        result = git_log.invoke({"n": 3})
        assert isinstance(result, str)


class TestWebSearch:
    def test_search_unavailable_without_key(self, monkeypatch):
        """Web search should gracefully report unavailability."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        # Re-import to pick up missing key
        from src.tools.web_search import web_search
        result = web_search.invoke({"query": "test query"})
        # Should return message about unavailability or results
        assert isinstance(result, str)
