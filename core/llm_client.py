"""
Local LLM client for MARK XL.

Supports two backends — selected via  "llm_provider"  in config/api_keys.json:

  "llm_provider": "ollama"   (default)
        Uses Ollama's native /api/chat endpoint.
        Download: https://ollama.com
        Default port: 11434

  "llm_provider": "openai"
        Uses any OpenAI-compatible server: LM Studio, Jan, LocalAI,
        llama.cpp server, vLLM, etc.
        LM Studio download: https://lmstudio.ai   (default port: 1234)
        Set  "llm_url": "http://localhost:1234"  in config.
        Note: tool-calling support depends on the model; use a model that
        supports function/tool calls (e.g. Qwen2.5, Llama-3.1, Mistral).
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Generator

import requests

# Matches a sentence boundary: [.!?] followed by whitespace, or a blank line.
# Avoids splitting on decimals (3.5) because those have no space after the dot.
_SENT_END = re.compile(r'(?<=[.!?])\s+|(?<=\n)\s*\n')

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR    = get_base_dir()
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

_DEFAULTS = {
    "llm_url":      "http://localhost:11434",
    "llm_model":    "llama3.2",
    "llm_provider": "ollama",   # "ollama" | "openai" | "openrouter"
}

# Modelos 100% gratuitos no OpenRouter, por categoria de tarefa.
# Ordem = prioridade de fallback (primeiro indisponível/rate-limited → tenta o próximo).
FREE_MODELS: dict[str, list[str]] = {
    "reasoning": [
        "deepseek/deepseek-r1:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct:free",
    ],
    "code": [
        "qwen/qwen-2.5-coder-32b-instruct:free",
        "deepseek/deepseek-chat:free",
        "meta-llama/llama-3.3-70b-instruct:free",
    ],
    "general": [
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-chat:free",
    ],
}

def get_openrouter_model(task: str = "general") -> str:
    """Retorna o modelo :free preferencial para a categoria; 'general' como padrão seguro."""
    return FREE_MODELS.get(task, FREE_MODELS["general"])[0]

def get_llm_provider() -> str:
    """Returns 'ollama', 'openai' (LM Studio/LocalAI/Jan) ou 'openrouter'."""
    raw = _load_config().get("llm_provider", "ollama").strip().lower()
    if raw == "openrouter":
        return "openrouter"
    return "openai" if raw in ("openai", "lmstudio", "localai", "jan", "llamacpp") else "ollama"

def _auth_headers(force_provider: str | None = None) -> dict:
    """Authorization header — necessário para OpenRouter, ausente para servidores locais."""
    provider = force_provider or get_llm_provider()
    if provider != "openrouter":
        return {}
    key = _load_config().get("openrouter_api_key", "").strip()
    return {"Authorization": f"Bearer {key}"} if key else {}


def _load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}



def get_llm_settings() -> tuple[str, str]:
    """Returns (base_url, model_name)."""
    cfg      = _load_config()
    provider = get_llm_provider()
    if provider == "openrouter":
        url   = cfg.get("llm_url",   "https://openrouter.ai/api/v1").rstrip("/")
        model = cfg.get("llm_model", get_openrouter_model("general"))
    else:
        url   = cfg.get("llm_url",   _DEFAULTS["llm_url"]).rstrip("/")
        model = cfg.get("llm_model", _DEFAULTS["llm_model"])
    return url, model


def call_llm_text(
    prompt:         str,
    system:         str | None = None,
    model:          str | None = None,
    timeout:        int = 120,
    force_provider: str | None = None,
) -> str:
    """
    Simple text-only generation (no tools).
    Used by planner, executor, error_handler, code_helper, dev_agent, deep_reasoning.

    force_provider: ignora config/api_keys.json::llm_provider e usa este provider
    diretamente. Necessário para deep_reasoning — que SEMPRE precisa do OpenRouter,
    independente de qual provider local (ollama/lmstudio) está configurado como padrão.
    """
    provider = force_provider or get_llm_provider()

    if provider in ("openai", "openrouter"):
        if force_provider == "openrouter":
            url = "https://openrouter.ai/api/v1"
            default_model = model or get_openrouter_model("general")
        else:
            url, default_model = get_llm_settings()
        m = model or default_model
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            resp = requests.post(
                f"{url}/v1/chat/completions",
                json={"model": m, "messages": messages, "stream": False, "max_tokens": 800},
                headers=_auth_headers(force_provider), timeout=timeout,
            )
            resp.raise_for_status()
            return (resp.json()["choices"][0]["message"].get("content") or "").strip()
        except Exception as e:
            raise RuntimeError(f"OpenRouter/OpenAI-compatible call failed: {e}")

    url, default_model = get_llm_settings()
    endpoint = f"{url}/api/chat"
    m        = model or default_model

    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {"model": m, "messages": messages, "stream": False, "keep_alive": -1, "options": {"num_predict": 600}}

    try:
        resp = requests.post(endpoint, json=payload, timeout=timeout)
        resp.raise_for_status()
        return (resp.json().get("message", {}).get("content") or "").strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot connect to Ollama at {url}. "
            "Make sure Ollama is installed and run: ollama serve"
        )
    except Exception as e:
        raise RuntimeError(f"LLM text call failed: {e}")


_TRANSIENT_ERR = ("503", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "429", "DEADLINE_EXCEEDED")

def _is_transient(exc: Exception) -> bool:
    msg = str(exc)
    return any(k in msg for k in _TRANSIENT_ERR)


def gemini_call_resilient(prompt: str, system: str | None = None,
                          model: str = "gemini-flash-latest",
                          task_type: str = "general") -> str:
    """
    Chama Gemini direto; em erro transiente (503/429/RESOURCE_EXHAUSTED) faz
    1 retry curto e, se persistir, cai automaticamente para OpenRouter :free.
    NUNCA propaga exceção — sempre retorna string (mesmo em falha total).
    """
    from google import genai
    import json as _json, time as _t

    try:
        cfg = _json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        api_key = cfg.get("gemini_api_key", "")
    except Exception:
        api_key = ""

    contents = f"{system}\n\n{prompt}" if system else prompt

    for attempt in range(2):
        try:
            client = genai.Client(api_key=api_key)
            r = client.models.generate_content(model=model, contents=contents)
            return (r.text or "").strip()
        except Exception as e:
            if _is_transient(e) and attempt == 0:
                print(f"[LLM] Gemini transiente ({e}) — retry em 1.5s")
                _t.sleep(1.5)
                continue
            print(f"[LLM] Gemini falhou ({e}) — fallback OpenRouter")
            break

    for fb_model in FREE_MODELS.get(task_type, FREE_MODELS["general"]):
        try:
            return call_llm_text(prompt, system=system, model=fb_model,
                                  timeout=20, force_provider="openrouter")
        except Exception as e:
            print(f"[LLM] Fallback {fb_model} falhou: {e}")
            continue

    return "Não foi possível obter resposta — todos os provedores falharam, Senhor."

