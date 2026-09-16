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
from datetime import datetime, timezone
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
    "llm_provider": "ollama",   # "ollama" | "openai" | "openrouter" | "groq"
}

# Modelos 100% gratuitos no OpenRouter, por categoria de tarefa.
# Ordem = prioridade de fallback (primeiro indisponível/rate-limited → tenta o próximo).
# NOTA: validar disponibilidade real em openrouter.ai/models?max_price=0
# antes do deploy — catálogo :free do OpenRouter muda com frequência.
# Atualizado 2026-09 — catálogo :free do OpenRouter rotaciona slugs
# constantemente. "openrouter/free" é o roteador oficial da OpenRouter.
FREE_MODELS: dict[str, list[str]] = {
    "reasoning": ["openrouter/free", "deepseek/deepseek-r1:free"],
    "code":      ["openrouter/free", "qwen/qwen-2.5-coder-32b-instruct:free"],
    "vision":    ["openrouter/free"],
    "search":    ["openrouter/free"],
    "general":   ["openrouter/free"],
}

def get_openrouter_model(task: str = "general") -> str:
    """Retorna o modelo :free preferencial para a categoria; 'general' como padrão seguro."""
    return FREE_MODELS.get(task, FREE_MODELS["general"])[0]

def _has_key(provider: str) -> bool:
    """Pre-flight check — evita chamada de rede quando falta a chave."""
    if provider not in ("groq", "openrouter"):
        return True
    key_name = "groq_api_key" if provider == "groq" else "openrouter_api_key"
    return bool(_load_config().get(key_name, "").strip())

def get_llm_provider() -> str:
    """Returns 'ollama', 'openai' (LM Studio/LocalAI/Jan), 'openrouter' ou 'groq'."""
    raw = _load_config().get("llm_provider", "ollama").strip().lower()
    if raw in ("openrouter", "groq"):
        return raw
    return "openai" if raw in ("openai", "lmstudio", "localai", "jan", "llamacpp") else "ollama"

_PROVIDER_URLS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "groq":       "https://api.groq.com/openai/v1",
}

def _auth_headers(force_provider: str | None = None) -> dict:
    """Authorization header — necessário para OpenRouter/Groq, ausente para servidores locais."""
    provider = force_provider or get_llm_provider()
    if provider not in ("openrouter", "groq"):
        return {}
    key_name = "openrouter_api_key" if provider == "openrouter" else "groq_api_key"
    key = _load_config().get(key_name, "").strip()
    return {"Authorization": f"Bearer {key}"} if key else {}


# Atualizado 2026-09 — modelos confirmados no catálogo público atual.
GROQ_MODELS: dict[str, list[str]] = {
    "reasoning": ["openai/gpt-oss-120b", "groq/compound-mini"],
    "code":      ["openai/gpt-oss-120b", "openai/gpt-oss-20b"],
    "vision":    [],
    "search":    ["groq/compound-mini", "openai/gpt-oss-20b"],
    "general":   ["openai/gpt-oss-20b", "openai/gpt-oss-120b"],
}


def _load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}



def get_llm_settings() -> tuple[str, str]:
    """Returns (base_url, model_name)."""
    cfg      = _load_config()
    provider = get_llm_provider()
    if provider in _PROVIDER_URLS:
        url   = cfg.get("llm_url",   "https://openrouter.ai/api/v1").rstrip("/")
        if provider == "groq":
            url = _PROVIDER_URLS["groq"]
            model = cfg.get("llm_model", GROQ_MODELS["general"][0])
        else:
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

    if provider in ("openai", "openrouter", "groq"):
        if force_provider in ("openrouter", "groq") and not _has_key(force_provider):
            raise RuntimeError(f"{force_provider}: chave ausente em config/api_keys.json — pulando.")
        if force_provider in ("openrouter", "groq"):
            url = _PROVIDER_URLS[force_provider]
            default_model = model or (get_openrouter_model("general") if force_provider == "openrouter"
                                       else GROQ_MODELS["general"][0])
        else:
            url, default_model = get_llm_settings()
        m = model or default_model
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        started = time.monotonic()
        try:
            resp = requests.post(
                f"{url}/chat/completions",
                json={"model": m, "messages": messages, "stream": False, "max_tokens": 800},
                headers=_auth_headers(force_provider), timeout=timeout,
            )
            resp.raise_for_status()
            print(
                f"[METRIC] provider_end provider={force_provider or provider} "
                f"model={m} ms={round((time.monotonic() - started) * 1000)} status=ok"
            )
            return (resp.json()["choices"][0]["message"].get("content") or "").strip()
        except Exception as e:
            print(
                f"[METRIC] provider_end provider={force_provider or provider} "
                f"model={m} ms={round((time.monotonic() - started) * 1000)} status=error"
            )
            status_code = None
            retry_after = None
            try:
                status_code = e.response.status_code
            except Exception:
                status_code = None
            try:
                retry_after = e.response.headers.get("Retry-After")
            except Exception:
                retry_after = None
            if status_code is not None or retry_after is not None or _is_transient(e):
                raise ProviderRequestError(
                    force_provider or provider,
                    f"{force_provider or provider} call failed: {e}",
                    status_code=status_code,
                    retry_after=_parse_retry_after(retry_after),
                ) from e
            raise RuntimeError(f"{force_provider or provider} call failed: {e}")

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
_PROVIDER_STATE: dict[str, dict[str, float | str | int]] = {}


class ProviderRequestError(RuntimeError):
    def __init__(self, provider: str, message: str, status_code: int | None = None, retry_after: int | float | None = None):
        self.provider = provider
        self.status_code = status_code
        self.retry_after = retry_after
        super().__init__(message)


def _parse_retry_after(value: str | int | float | None) -> float:
    if value is None:
        return 0.0
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        pass
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())
    except ValueError:
        pass
    try:
        dt = datetime.strptime(str(value), "%a, %d %b %Y %H:%M:%S GMT")
        return max(0.0, (dt.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds())
    except ValueError:
        return 0.0


def _register_provider_failure(provider: str, exc: Exception) -> None:
    retry_after = int(getattr(exc, "retry_after", 0) or 0)
    if retry_after <= 0 and getattr(exc, "status_code", None) == 429:
        retry_after = 5
    state = _PROVIDER_STATE.setdefault(provider, {"blocked_until": 0.0, "failures": 0})
    if retry_after > 0:
        state["blocked_until"] = max(float(state.get("blocked_until", 0.0)), time.monotonic() + retry_after)
    else:
        state["blocked_until"] = max(float(state.get("blocked_until", 0.0)), time.monotonic() + 2.0)
    state["failures"] = int(state.get("failures", 0)) + 1


def _provider_is_open(provider: str) -> bool:
    state = _PROVIDER_STATE.get(provider)
    if not state:
        return True
    return float(state.get("blocked_until", 0.0)) <= time.monotonic()


def _provider_next_retry(provider: str) -> float:
    state = _PROVIDER_STATE.get(provider)
    if not state:
        return 0.0
    return max(0.0, float(state.get("blocked_until", 0.0)) - time.monotonic())


def _is_transient(exc: Exception) -> bool:
    msg = str(exc)
    return any(k in msg for k in _TRANSIENT_ERR)


def resilient_text_call(prompt: str, system: str | None = None,
                        task_type: str = "general", timeout: int = 20) -> str:
    """Camada única de texto: Groq gratuito e depois OpenRouter gratuito."""
    if task_type not in GROQ_MODELS:
        task_type = "general"

    for provider, models in (("groq", GROQ_MODELS.get(task_type, [])), ("openrouter", FREE_MODELS.get(task_type, FREE_MODELS["general"]))):
        if not _provider_is_open(provider):
            wait = _provider_next_retry(provider)
            print(f"[LLM] {provider} em cooldown por {wait:.1f}s — pulando para próximo provedor.")
            continue

        for model in models:
            try:
                return call_llm_text(prompt, system=system, model=model,
                                     timeout=timeout, force_provider=provider)
            except ProviderRequestError as e:
                print(f"[LLM] {provider} {model} falhou: {e} — tentando próximo")
                _register_provider_failure(provider, e)
                if not _provider_is_open(provider):
                    break
            except Exception as e:
                print(f"[LLM] {provider} {model} falhou: {e} — tentando próximo")

    return "Não foi possível obter resposta — todos os provedores gratuitos falharam, Senhor."


def resilient_vision_call(prompt: str, image_bytes: bytes, mime_type: str = "image/png",
                          timeout: int = 25) -> str:
    """Vision multimodal via Groq e OpenRouter no formato OpenAI content-parts."""
    import base64

    b64_img = base64.b64encode(image_bytes).decode("utf-8")
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}},
        ],
    }]

    for provider, models in (("groq", GROQ_MODELS.get("vision", [])),
                             ("openrouter", FREE_MODELS["vision"])):
        url = _PROVIDER_URLS[provider]
        for model in models:
            try:
                resp = requests.post(
                    f"{url}/chat/completions",
                    json={"model": model, "messages": messages, "stream": False, "max_tokens": 900},
                    headers=_auth_headers(provider), timeout=timeout,
                )
                resp.raise_for_status()
                text = (resp.json()["choices"][0]["message"].get("content") or "").strip()
                if text:
                    return text
            except Exception as e:
                print(f"[LLM] Vision {provider}/{model} falhou: {e}")

    return "Não foi possível analisar a imagem — todos os provedores gratuitos falharam, Senhor."


def gemini_call_resilient(prompt: str, system: str | None = None,
                          model: str = "", task_type: str = "general") -> str:
    return resilient_text_call(prompt, system=system, task_type=task_type)

