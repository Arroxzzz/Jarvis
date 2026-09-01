# CURRENT_TASK — Sprint 1

## Tarefa 1 — Blindagem de Identidade + Remoção do Briefing
**Status:** [CONCLUÍDA]
**Arquivos:** `core/prompt.txt`, `main.py`, `memory/config_manager.py`
- ✓ `core/prompt.txt`: substitui bloco `ADDRESS:` (turco/inglês) por regra PT-BR fixa
- ✓ `main.py::_build_config()`: tratamento "Senhor" incondicional
- ✓ `memory/config_manager.py::get_brief_enabled()`: default `False`
- **Resultado:** reset de config não produz "efendim"/"sir"; briefing matinal desativado por padrão

## Tarefa 2 — Hotkey F4 Global (pynput) + Modo Fantasma
**Status:** [CONCLUÍDA]
**Arquivos:** `ui.py`, `requirements.txt`, `main.py`
- ✓ `pynput` adicionado a `requirements.txt`
- ✓ `ui.py`: F4 global via `pynput.keyboard.GlobalHotKeys` em thread daemon
- ✓ `QSystemTrayIcon` implementado com menu (Mostrar/Ocultar, Mutar/Desmutar, Sair)
- ✓ `_pause_rendering()`/`_resume_rendering()`: pausam `HudCanvas._tmr`, `_metric_tmr`, `_metrics` ao minimizar/ocultar
- ✓ `changeEvent()` + `closeEvent()` integrados para tray automático
- **Resultado:** F4 funciona com JARVIS minimizado/sem foco; ocultar para bandeja derruba CPU a ~0%

## Tarefa 3 — Limpeza de Plugins + OpenRouter Gratuito
**Status:** [CONCLUÍDA]
**Arquivos:** `plugins/reminder_verbal.py`, `core/llm_client.py`, `actions/` → `plugins/`
- ✓ `plugins/reminder_verbal.py`: reescrito com indentação corrigida (4 espaços)
- ✓ `actions/upload_video.py` → `plugins/upload_video.py`
- ✓ `actions/pushup_counter.py` → `plugins/pushup_counter.py`
- ✓ `core/llm_client.py`: provider "openrouter" integrado
  - Função `get_openrouter_model(task)` com dicionário `FREE_MODELS` por categoria (reasoning/code/general)
  - Função `_auth_headers()` injeta Bearer token em todas as requisições OpenRouter
  - Defaults: `https://openrouter.ai/api/v1`, modelo `meta-llama/llama-3.3-70b-instruct:free`
  - Suporte streaming e non-streaming para OpenRouter
- **Resultado:** plugin manager não lista plugins como BROKEN; `llm_provider: "openrouter"` funciona com modelos :free

---

# PRÓXIMAS TAREFAS — Sprint 2 (Em progresso)

## Tarefa 1 — Fallback Gemini Live → OpenRouter via tool deep_reasoning
**Status:** [EM VALIDAÇÃO — bug de travamento corrigido, aguardando reteste]
**Arquivos:** `main.py`, `core/llm_client.py`, `config/api_keys.json`
**Implementação:**
- ✓ Tool `deep_reasoning` em `TOOL_DECLARATIONS` (main.py)
- ✓ Suporte OpenRouter com `force_provider` em `call_llm_text()` (core/llm_client.py)
- ✓ Fallback automático entre modelos :free por categoria (reasoning/code/general)
- ✓ Timeout curto (25s/modelo) + budget total (80s) via `asyncio.wait_for()`
- ✓ Config atualizado com `llm_provider: "openrouter"`

**Bugs corrigidos durante desenvolvimento:**
- ❌ Inicialmente: `call_llm_text()` não forçava provider OpenRouter → caía em Ollama local
  - ✓ Corrigido: adicionado parâmetro `force_provider` + lógica de override
- ❌ Crítico: `_receive_audio` travava sessão de voz quando tool call era longo
  - ✓ Corrigido: envolvido executor com `asyncio.wait_for(..., timeout=80)`
  - ✓ Mensagem de erro amigável ao timeout, não bloqueia mais sessão

**Critério de aceite (aguardando Senhor Paulo):**
- Resposta chega em até ~25-80s (não trava)
- JARVIS continua respondendo após timeout/falha da tool
- Nenhum restart necessário
- `openrouter_api_key` confirmado válido


## Tarefa 2 — Agendador de Tarefas Recorrentes
**Status:** [NÃO INICIADO]
**Arquivos:** `actions/recurring_task.py` (novo), `main.py`, `memory/config_manager.py`
**Descrição:**
- Criar `actions/recurring_task.py` generalizando o scheduler já usado em `actions/game_updater.py`
  - Suportar múltiplas recorrências: diária, semanal, mensal, intervalo customizado (horas/minutos)
  - Armazenar schedule em `config/api_keys.json` sob chave `"recurring_tasks": [...]`
  - Cada tarefa: `{"name": "...", "action": "...", "interval": "...", "next_run": "..."}`
- Expor como tool no `TOOL_DECLARATIONS`: `schedule_task(name, action, interval)`
- Inicializar scheduler ao boot via `JarvisLive.run()`, carregar tarefas de config
- **Critério de aceite:** Usuário consegue agendar "Verificar emails todo dia às 9h", 
  "Atualizar jogo todas as quartas-feiras", etc; tarefas persistem entre sessões