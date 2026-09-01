# ARCHITECTURE — JARVIS MARK LI

## Stack
- UI: PyQt6 (`ui.py`) — HudCanvas (QPainter, QTimer 16ms), MetricBar, LogWidget,
  overlays (Setup/Customize/PluginManager/RemoteKey)
- Voz: Gemini Live API (`google.genai`, model
  `gemini-2.5-flash-native-audio-preview-12-2025`), STT/TTS locais em `core/stt.py`,`core/tts.py`
  (Whisper/Vosk, EdgeTTS/Kokoro/ElevenLabs) — usados fora do fluxo Live quando aplicável.
- LLM local opcional: `core/llm_client.py` — Ollama (`/api/chat`) ou
  OpenAI-compatible (LM Studio etc, `/v1/chat/completions`). **OpenRouter: a implementar**
  (mesmo padrão OpenAI-compatible, base_url `https://openrouter.ai/api/v1`,
  modelos `:free`).
- Plugins: `core/plugin_loader.py` — scan de `plugins/*.py` (ignora `_*`),
  valida `PLUGIN` dict + `run()`, isola exceptions, dispatch via `main.py::_execute_tool`.
- Memória: `memory/memory_manager.py` (long_term.json: identity/preferences/
  projects/relationships/wishes/notes/sessions/monitors).
- Dashboard remoto: `dashboard/server.py` (FastAPI, AES-256-CBC, QR pairing,
  WS bidirecional, upload de arquivos).
- Automação desktop: `actions/computer_control.py`, `computer_settings.py`,
  `browser_control.py` (Playwright, perfis reais do usuário).

## Fluxo de Tool Call
`main.py::JarvisLive._execute_tool(fc)` → dispatch por `fc.name` → core tools
(hardcoded elif) ou `self._plugin_registry.run(name, ...)` (plugins/).

⚠️ **ATENÇÃO — Travamento Potencial:**
main.py::_receive_audio executa tool calls de forma **SÍNCRONA** dentro do loop
de recepção da sessão Gemini Live (`await self._execute_tool(fc)`). Qualquer
tool com chamada de rede externa (ex: deep_reasoning/OpenRouter, web_search,
file_processor remoto) **DEVE ter timeout curto + budget total** via
`asyncio.wait_for()`. Caso contrário, trava toda a sessão de voz até restart
manual. 

**Padrão de implementação seguro:**
```python
try:
    r = await asyncio.wait_for(
        loop.run_in_executor(None, _blocking_call),
        timeout=BUDGET_SECONDS  # ex: 80 para cascata de 3 modelos × 25s
    )
except asyncio.TimeoutError:
    result = "[Tool] Operação demorou demais; cancelada, Senhor."
```

**Alternativa futura:** mover tool calls de longa duração para fire-and-forget
com resposta assíncrona (padrão já usado em `upload_video.py` via
`player.request_say()`), em vez de bloquear o turno atual da sessão de voz.

## Config
`config/api_keys.json`: `gemini_api_key`, `os_system`, `assistant_name`,
`user_name`, `ui_color`, `morning_brief_enabled`, `plugins_enabled{}`,
`llm_provider`/`llm_url`/`llm_model` (para core/llm_client.py).

## Gaps de Performance (jogos)
- `HudCanvas._tmr` (16ms) e `_SysMetrics._loop` (1.5s) rodam sempre,
  independente de estado da janela — sem `changeEvent`/tray hook.