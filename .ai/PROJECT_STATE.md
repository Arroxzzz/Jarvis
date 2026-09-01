# PROJECT_STATE — JARVIS MARK LI

## Contexto
Projeto restaurado de backup. Usuário: Senhor Paulo. Idioma obrigatório: PT-BR.

## Funcionalidades Operacionais
- Gemini Live API (áudio nativo, function calling, session_resumption)
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

## Funcionalidades a Restabelecer
1. **Remover Morning Briefing automático** — `_send_startup_briefing` desativado
   por padrão; implementar toggle de retorno automático no dashboard.
2. **Robustez de Audio** — guard contra dupla resposta VAD (Gemini) + interrupção
   melhorada; timeout de audio + reconexão automática de sessão.
3. **Dashboard Web Expandido** — login, painel de controle remoto, sockets
   bidirecionais para sincronizar estado HUD.
4. **Otimização Gaming** — perfil de poder com redução de polling quando
   em fullscreen; explorar GPU pooling (CUDA/ROCm) se disponível.

---

## INCIDENTE SPRINT 2 — RESOLVIDO

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