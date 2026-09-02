# ARCHITECTURE — JARVIS MARK LI

## Stack
- UI: PyQt6 (`ui.py`) — HudCanvas (QPainter, QTimer 16ms), MetricBar, LogWidget,
  overlays (Setup/Customize/PluginManager/RemoteKey)
- Voz: Gemini Live API (`google.genai`, model
  `gemini-2.5-flash-native-audio-preview-12-2025`). STT/TTS locais removidos (módulos legado).
- LLM local opcional: `core/llm_client.py` — Ollama (`/api/chat`) ou
  OpenAI-compatible (LM Studio etc, `/v1/chat/completions`). **OpenRouter integrado**
  (base_url `https://openrouter.ai/api/v1`, modelos `:free`).
- **Hardware Sensors:** `core/hw_sensors.py` — centraliza GPU/temp com zero subprocess
  - GPU: pynvml → ctypes nvml.dll (Windows) / libnvidia-ml.so.1 (Linux) / .dylib (macOS)
  - Temperatura: psutil sensors → wmi (Windows)
  - Importado por `ui.py::_SysMetrics` e `actions/system_monitor.py`
- Plugins: `core/plugin_loader.py` — scan de `plugins/*.py` (ignora `_*`),
  valida `PLUGIN` dict + `run()`, isola exceptions, dispatch via `main.py::_execute_tool`.
- Memória: `memory/memory_manager.py` (long_term.json: identity/preferences/
  projects/relationships/wishes/notes/sessions/monitors).
- Dashboard remoto: `dashboard/server.py` (FastAPI, AES-256-CBC, QR pairing,
  WS bidirecional, upload de arquivos).
- Automação desktop: `actions/computer_control.py`, `computer_settings.py`,
  `browser_control.py` (Playwright, perfis reais do usuário).

## Fluxo de Tool Call
## Fluxo de Tool Call (Assincrono Seguro — SPRINT 3)

✅ **IMPLEMENTAÇÃO FINAL:**
- Múltiplas function calls executam em paralelo via `asyncio.gather(*self._active_tool_tasks)`
- Cada call envolvido em `_bounded(loop, fn, timeout, label)` → `asyncio.wait_for(..., timeout)`
- Timeouts individuais por tool (20s `open_app`, 90s `code_helper`, 30s `browser_control`, etc)
- Orçamento total ~80s máximo para cascata de 3 modelos em `deep_reasoning`
- `interrupt()` cancela **todas as tarefas ativas** via `t.cancel()` em `self._active_tool_tasks`
- Timeout → mensagem erro amigável em PT-BR, **não trava sessão Live**
- Zero deadlock em `_vision_busy` (cooldown 4s + reset em erro)

**Padrão seguro (SEMPRE):**
```python
result = await self._bounded(loop, fn, TIMEOUT_SECONDS, "tool_name")
```

## Config
`config/api_keys.json`: `gemini_api_key`, `os_system`, `assistant_name`,
`user_name`, `ui_color`, `morning_brief_enabled`, `plugins_enabled{}`,
`llm_provider`/`llm_url`/`llm_model` (para core/llm_client.py).

## Gaps de Performance (jogos)
- `HudCanvas._tmr` (16ms) e `_SysMetrics._loop` (1.5s) rodam sempre,
  independente de estado da janela — sem `changeEvent`/tray hook.