# PROJECT_STATE — JARVIS MARK LI — FINAL (2026-09-02)

## Contexto
Projeto restaurado de backup. Usuário: Senhor Paulo. Idioma obrigatório: PT-BR.

## Funcionalidades Operacionais Estáveis
- Gemini Live API (áudio nativo, function calling, session_resumption) com arquitetura assíncrona segura
- Sistema de plugins (auto-discovery em `plugins/`, isolamento de crash)
  - Plugins corretos: `reminder_verbal.py`, `upload_video.py`, `pushup_counter.py` (todos em `plugins/` agora)
- HUD PyQt6 (HudCanvas 60fps, MetricBar, LogWidget)
- Dashboard remoto (FastAPI + AES-256 + QR pairing)
- File processor multi-formato (pdf/docx/csv/audio/video/etc)
- Browser control (Playwright, perfis reais)
- Memory manager (long_term.json)
- **Identidade PT-BR fixa** ("Senhor" incondicional, sem fallback turco/inglês)
- **Hotkey F4 global** (pynput, funciona minimizado/sem foco)
- **Modo Fantasma / Bandeja** (pausa HUD/métricas, restauração via tray)
- **OpenRouter gratuito** (provider com modelos :free por categoria: reasoning/code/general)
- **Arquitetura assíncrona segura** (tool calls paralelas com timeout, cancelamento real, sem deadlock)

## Arquitetura Assíncrona Final (Sprint 3)

### Tool Execution Model
- `main.py::_execute_tool(fc)` agora roda múltiplas function calls em paralelo via `asyncio.gather(*tasks)`
- Cada tool call envolvido em `_bounded(loop, fn, timeout, label)` com `asyncio.wait_for()` timeout individual
- Timeouts configurados por tool: exemplos: 20s `open_app`, 90s `code_helper`, 30s `browser_control`
- Orçamento total rígido protege sessão de voz de travamento

### Cancelamento & Interrupção
- `JarvisLive.interrupt()` cancela **todas as tarefas ativas** via `t.cancel()` em `self._active_tool_tasks`
- Operação real-time; tarefas recebem `asyncio.CancelledError`
- Drenagem de fila de áudio mantida; sessão continua responsiva

### Modules Removed (Sprint 3)
- ✓ Deletados: `core/stt.py`, `core/tts.py`, `core/hotkeys.py` (legados)
- ✓ F4 global agora via pynput em `ui.py`
- ✓ Validação grep: zero referências stale

### Hardware Sensors Unified
- **Novo:** `core/hw_sensors.py` centraliza GPU/temp (zero subprocess)
- GPU: pynvml → ctypes nvml.dll/libnvidia-ml
- Temp: psutil sensors → wmi (Windows)
- Importado por `ui.py` e `actions/system_monitor.py`

## Funcionalidades a Restabelecer
1. **Morning Briefing automático** — implementar toggle retorno automático no dashboard.
2. **Dashboard Web Expandido** — login, painel de controle remoto, sockets bidirecionais.
3. **Otimização Gaming** — perfil de poder com redução de polling em fullscreen.

---

## INCIDENTE SPRINT 2 — RESOLVIDO

## ESTABILIZAÇÃO SPRINT 3 — CONCLUÍDA

### Correções implementadas
- Eliminação de módulos obsoletos: STT, TTS e hotkeys foram removidos do projeto.
- `main.py`: tool calls longas passaram a usar wrapper `_bounded()` com timeout, `asyncio.gather()` para execução paralela e cancelamento real via `interrupt()`.
- `actions/screen_processor.py`: mantido apenas fluxo de captura de imagem; sessão de visão ghost removida.
- `main.py`: deadlock de `_vision_busy` corrigido com reset em erro e proteção por cooldown.
- `actions/game_updater.py`: correção de shadowing de `platform` e limpeza de comportamento duplicado.
- `core/hw_sensors.py`: centralização do monitoramento de hardware para CPU/GPU.
- `core/llm_client.py`: remoção de blocos mortos e manutenção do provider OpenRouter livre.

### Contexto
Durante implementação de `deep_reasoning` (fallback Gemini Live → OpenRouter),
descoberto e corrigido travamento crítico na sessão de voz.

### Bugs Identificados

**Bug 1: deep_reasoning não forçava provider OpenRouter**
- `call_llm_text()` caía no branch Ollama ao ler config local (`get_llm_provider()` → "ollama")
- Tentava `subprocess.Popen(["ollama", "serve"])` ao invés de chamar OpenRouter
- Retries longos (até 120s) esperando Ollama iniciar

**Bug 2 (CRÍTICO): travamento de sessão de voz**
- `main.py::_receive_audio` executava `await self._execute_tool(fc)` **sincronamente** dentro do loop de recepção Gemini Live
- Quando `deep_reasoning` ficava preso em timeout (até 120s × 3 modelos em cascata ≈ 6 min), **nenhuma mensagem de áudio era processada**
- Sessão inteira travava silenciosamente, exigindo restart manual do JARVIS
- Gemini Live não conseguia enviar novas mensagens enquanto tool call pendente

### Correção Aplicada

**core/llm_client.py:**
- `call_llm_text()` ganhou parâmetro `force_provider: str | None`
  - Ignora `llm_provider` do config quando setado explicitamente
  - Permite forçar OpenRouter independente do provedor local ativo (ollama/lmstudio)
- `_auth_headers()` aceita `force_provider` como override de provider
- Garante que modelos :free sejam chamados contra endpoint correto

**main.py::deep_reasoning branch:**
- `timeout=25` por chamada individual (modelo único)
- `force_provider="openrouter"` explícito em cada `call_llm_text()`
- `asyncio.wait_for(..., timeout=80)` envolvendo todo `run_in_executor()`
  - Orçamento total rígido de ~80s no pior caso (cascata de 3 modelos)
  - Mensagem de erro amigável em vez de travamento silencioso
  - Não bloqueia sessão de voz além desse tempo

**config/api_keys.json:**
- `llm_provider`: "openrouter" (now default)
- `llm_url`: "https://openrouter.ai/api/v1"
- `llm_model`: "meta-llama/llama-3.3-70b-instruct:free"
- `openrouter_api_key`: presente e válida

### Status
- ✓ Correção código aplicada
- ⏳ **AGUARDANDO RETESTE** (Senhor Paulo)
  - Confirmar: resposta chega em até ~25-80s
  - Confirmar: JARVIS continua respondendo após timeout/falha
  - Confirmar: nenhum restart necessário (sessão de voz continua)
  - Pendência: validar que `openrouter_api_key` é válida (sem ela, 401 esperado)

## Regras de Ouro
- PT-BR estrito em toda saída falada/escrita do assistente.
- Tratamento exclusivo: "Senhor" (nunca "sir", nunca "efendim").
- CPU/GPU mínimo durante jogos — HUD e métricas pausam ao minimizar.
- Toda entrega de código é cirúrgica (antes/depois), nunca arquivo completo.
- Zero saudações/preâmbulos em respostas técnicas.

---

## SPRINT 4 — Resiliência de API + UX de Boot (CONCLUÍDA)
- Cancelamento cooperativo (threading.Event) para tools em executor — asyncio Task.cancel()
  sozinho NÃO para threads de run_in_executor; todo tool longo futuro deve seguir esse padrão
  se precisar ser interrompível de fato.
- `core/llm_client.py::gemini_call_resilient()` — usar para QUALQUER chamada direta ao
  Gemini que possa sofrer 503 (dev_agent, code_helper, session summary futuramente).
- Timezone: SEMPRE `datetime.now(ZoneInfo("America/Sao_Paulo"))`, nunca `datetime.now()` puro
  em contexto exposto ao usuário — clock do host pode estar em UTC.
