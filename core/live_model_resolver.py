from __future__ import annotations

import asyncio

from google import genai


def _discover_live_models(api_key: str) -> list[str]:
    """Discover models that support the Gemini Live API."""
    found: list[str] = []
    try:
        client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
        for model in client.models.list():
            name = getattr(model, "name", "") or ""
            actions = (
                getattr(model, "supported_actions", None)
                or getattr(model, "supported_generation_methods", None)
                or []
            )
            actions_str = " ".join(str(action) for action in actions).lower()
            if "bidigeneratecontent" not in actions_str:
                continue
            lower_name = name.lower()
            if "translate" in lower_name or "transcribe" in lower_name:
                continue
            found.append(name)

        found.sort(
            key=lambda name: (
                0 if "native-audio" in name.lower() else 1,
                0 if "live" in name.lower() else 1,
                "exp" in name.lower(),
                name,
            )
        )
        if found:
            print(f"[JARVIS] 🔍 Live models descobertos: {found}")
    except Exception as exc:
        print(f"[JARVIS] ⚠️ Descoberta de modelos Live falhou: {exc}")
    return found


def _validate_gemini_key(api_key: str) -> bool:
    """Retorna False somente para erros conhecidos de chave inválida."""
    try:
        client = genai.Client(api_key=api_key)
        client.models.generate_content(model="gemini-2.0-flash", contents="ping")
        return True
    except Exception as exc:
        message = str(exc)
        if "API key not valid" in message or "API_KEY_INVALID" in message:
            return False
        return True


class LiveModelResolver:
    def __init__(self, ui, get_config, fallbacks: list[str], cache_key: str):
        self.ui = ui
        self._get_config = get_config
        self._fallbacks = fallbacks
        self._cache_key = cache_key
        self.candidates: list[str] = []
        self.idx = 0

    async def resolve(self, api_key: str) -> None:
        cached = self._get_config().get(self._cache_key)
        discovered = await asyncio.to_thread(_discover_live_models, api_key)
        if not discovered:
            self.ui.write_log(
                "SYS: ⚠️ Nenhum modelo Live descoberto via API — usando "
                "cache/fallback estático. Se a conexão falhar, verifique "
                "a API key e disponibilidade do modelo Live no console."
            )

        candidates: list[str] = []
        if cached:
            candidates.append(cached)
        for model in (*discovered, *self._fallbacks):
            if model not in candidates:
                candidates.append(model)

        self.candidates = candidates
        self.idx = 0
        message = (
            f"Live model em uso: {candidates[0]}  "
            f"(+{len(candidates) - 1} fallback(s))"
        )
        print(f"[JARVIS] 🎯 {message}")
        self.ui.write_log(f"SYS: {message}")

    def current(self) -> str:
        if not self.candidates:
            return self._fallbacks[0]
        return self.candidates[self.idx % len(self.candidates)]

    def advance(self) -> None:
        """Rotate to the next candidate after a model rejection."""
        if len(self.candidates) > 1:
            self.idx = (self.idx + 1) % len(self.candidates)
        self.ui.write_log(
            f"SYS: Tentando model id alternativo: {self.current()}"
        )
