import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path.cwd()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama_cloud")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-coder:7b")

# Local Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Ollama Cloud
OLLAMA_CLOUD_BASE_URL = os.getenv("OLLAMA_CLOUD_BASE_URL", "https://api.ollama.com")
OLLAMA_CLOUD_API_KEY = os.getenv("OLLAMA_CLOUD_API_KEY", "")

# OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Cerebras AI
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"

LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "10"))

PROVIDER_MAP = {
    "groq": "groq",
    "anthropic": "anthropic",
    "google_genai": "google_genai",
    "ollama": "ollama",
    "ollama_cloud": "ollama",      # same ChatOllama, different endpoint
    "openrouter": "openai",        # OpenAI-compatible API
    "cerebras": "openai",          # OpenAI-compatible API
}

DANGEROUS_PATTERNS = [
    "rm -rf", "rm -r /", "mkfs", "dd if=", "chmod 777",
    "> /dev/sd", "format c:", "shutdown", "reboot",
    ":(){ :|:& };:", "wget | sh", "curl | sh",
]

HITL_TOOLS = {
    "execute": {
        "allowed_decisions": ["approve", "edit", "reject"],
    },
}


def get_model_string() -> str:
    if LLM_PROVIDER == "ollama":
        return f"ollama:{OLLAMA_MODEL}"
    if LLM_PROVIDER == "ollama_cloud":
        return f"ollama:{LLM_MODEL}"
    return f"{PROVIDER_MAP.get(LLM_PROVIDER, LLM_PROVIDER)}:{LLM_MODEL}"


def get_model_kwargs() -> dict:
    kwargs = {}
    if LLM_PROVIDER == "ollama":
        kwargs["base_url"] = OLLAMA_BASE_URL
    elif LLM_PROVIDER == "ollama_cloud":
        kwargs["base_url"] = OLLAMA_CLOUD_BASE_URL
        if OLLAMA_CLOUD_API_KEY:
            kwargs["client_kwargs"] = {
                "headers": {
                    "Authorization": f"Bearer {OLLAMA_CLOUD_API_KEY}",
                }
            }
    elif LLM_PROVIDER == "openrouter":
        kwargs["base_url"] = OPENROUTER_BASE_URL
        if OPENROUTER_API_KEY:
            kwargs["api_key"] = OPENROUTER_API_KEY
    elif LLM_PROVIDER == "cerebras":
        kwargs["base_url"] = CEREBRAS_BASE_URL
        if CEREBRAS_API_KEY:
            kwargs["api_key"] = CEREBRAS_API_KEY
    return kwargs
