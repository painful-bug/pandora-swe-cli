"""Tests for src/prompts.py — prompt loading and frontmatter stripping."""

import pytest
from pathlib import Path


class TestLoadPrompt:
    def test_load_existing_prompt(self):
        from src.prompts import load_prompt
        content = load_prompt("main-agent")
        assert content
        assert len(content) > 50  # Meaningful content exists

    def test_load_all_prompts(self):
        from src.prompts import load_prompt
        prompts = ["main-agent", "code-explorer", "code-architect", "code-reviewer", "subagent"]
        for name in prompts:
            content = load_prompt(name)
            assert content, f"Prompt '{name}' should not be empty"

    def test_load_missing_prompt(self):
        from src.prompts import load_prompt
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent-prompt-xyz")

    def test_frontmatter_stripped(self):
        from src.prompts import load_prompt, PROMPTS_DIR
        # Check if any prompt file has frontmatter
        for md_file in PROMPTS_DIR.glob("*.md"):
            raw = md_file.read_text(encoding="utf-8")
            loaded = load_prompt(md_file.stem)
            # Frontmatter starts with '---', loaded content should not
            if raw.startswith("---"):
                assert not loaded.startswith("---"), f"{md_file.name} frontmatter not stripped"

    def test_content_preserved(self):
        from src.prompts import load_prompt
        content = load_prompt("main-agent")
        # Should contain meaningful instructions, not just whitespace
        assert len(content.split()) > 10
