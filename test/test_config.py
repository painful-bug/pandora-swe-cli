"""Tests for src/config.py — provider mapping, model strings, kwargs."""

import os
import importlib
import pytest


def _reload_config(monkeypatch, **env_vars):
    """Helper to reload config module with specific env vars."""
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
    import src.config as cfg
    importlib.reload(cfg)
    return cfg


class TestDefaults:
    def test_default_provider(self, mock_env):
        cfg = _reload_config(mock_env)
        assert cfg.LLM_PROVIDER == "ollama_cloud"

    def test_default_model(self, mock_env):
        cfg = _reload_config(mock_env)
        assert cfg.LLM_MODEL == "qwen2.5-coder:7b"

    def test_default_max_retries(self, mock_env):
        cfg = _reload_config(mock_env)
        assert cfg.MAX_RETRIES == 10

    def test_custom_max_retries(self, mock_env):
        cfg = _reload_config(mock_env, MAX_RETRIES="5")
        assert cfg.MAX_RETRIES == 5


class TestModelString:
    def test_groq(self, mock_env):
        cfg = _reload_config(mock_env, LLM_PROVIDER="groq", LLM_MODEL="llama-3.3-70b")
        assert cfg.get_model_string() == "groq:llama-3.3-70b"

    def test_ollama_local(self, mock_env):
        cfg = _reload_config(mock_env, LLM_PROVIDER="ollama", OLLAMA_MODEL="llama3.2")
        assert cfg.get_model_string() == "ollama:llama3.2"

    def test_ollama_cloud(self, mock_env):
        cfg = _reload_config(mock_env, LLM_PROVIDER="ollama_cloud", LLM_MODEL="qwen2.5:7b")
        assert cfg.get_model_string() == "ollama:qwen2.5:7b"

    def test_openrouter(self, mock_env):
        cfg = _reload_config(mock_env, LLM_PROVIDER="openrouter", LLM_MODEL="google/gemini-2.0-flash")
        assert cfg.get_model_string() == "openai:google/gemini-2.0-flash"

    def test_anthropic(self, mock_env):
        cfg = _reload_config(mock_env, LLM_PROVIDER="anthropic", LLM_MODEL="claude-sonnet-4-6")
        assert cfg.get_model_string() == "anthropic:claude-sonnet-4-6"

    def test_google_genai(self, mock_env):
        cfg = _reload_config(mock_env, LLM_PROVIDER="google_genai", LLM_MODEL="gemini-2.5-flash")
        assert cfg.get_model_string() == "google_genai:gemini-2.5-flash"


class TestModelKwargs:
    def test_groq_empty(self, mock_env):
        cfg = _reload_config(mock_env, LLM_PROVIDER="groq")
        assert cfg.get_model_kwargs() == {}

    def test_ollama_local_base_url(self, mock_env):
        cfg = _reload_config(mock_env, LLM_PROVIDER="ollama", OLLAMA_BASE_URL="http://localhost:11434")
        kwargs = cfg.get_model_kwargs()
        assert kwargs["base_url"] == "http://localhost:11434"

    def test_ollama_cloud_with_key(self, mock_env):
        cfg = _reload_config(
            mock_env,
            LLM_PROVIDER="ollama_cloud",
            OLLAMA_CLOUD_BASE_URL="https://api.ollama.com",
            OLLAMA_CLOUD_API_KEY="test-key-123",
        )
        kwargs = cfg.get_model_kwargs()
        assert kwargs["base_url"] == "https://api.ollama.com"
        assert "Authorization" in kwargs["client_kwargs"]["headers"]
        assert "Bearer test-key-123" in kwargs["client_kwargs"]["headers"]["Authorization"]

    def test_ollama_cloud_no_key(self, mock_env):
        cfg = _reload_config(mock_env, LLM_PROVIDER="ollama_cloud")
        kwargs = cfg.get_model_kwargs()
        assert kwargs["base_url"] == "https://api.ollama.com"
        assert "client_kwargs" not in kwargs

    def test_openrouter_with_key(self, mock_env):
        cfg = _reload_config(mock_env, LLM_PROVIDER="openrouter", OPENROUTER_API_KEY="sk-or-test")
        kwargs = cfg.get_model_kwargs()
        assert kwargs["base_url"] == "https://openrouter.ai/api/v1"
        assert kwargs["api_key"] == "sk-or-test"

    def test_openrouter_no_key(self, mock_env):
        cfg = _reload_config(mock_env, LLM_PROVIDER="openrouter")
        kwargs = cfg.get_model_kwargs()
        assert kwargs["base_url"] == "https://openrouter.ai/api/v1"
        assert "api_key" not in kwargs


class TestProviderMap:
    def test_all_providers_present(self, mock_env):
        cfg = _reload_config(mock_env)
        expected = {"groq", "anthropic", "google_genai", "ollama", "ollama_cloud", "openrouter"}
        assert expected == set(cfg.PROVIDER_MAP.keys())

    def test_openrouter_maps_to_openai(self, mock_env):
        cfg = _reload_config(mock_env)
        assert cfg.PROVIDER_MAP["openrouter"] == "openai"

    def test_ollama_cloud_maps_to_ollama(self, mock_env):
        cfg = _reload_config(mock_env)
        assert cfg.PROVIDER_MAP["ollama_cloud"] == "ollama"


class TestDangerousPatterns:
    def test_patterns_populated(self, mock_env):
        cfg = _reload_config(mock_env)
        assert len(cfg.DANGEROUS_PATTERNS) > 0
        assert "rm -rf" in cfg.DANGEROUS_PATTERNS
