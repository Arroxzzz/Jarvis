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

# SPRINTS CONCLUÍDAS

## Sprint 3 — Arquitetura Assíncrona Segura [CONCLUÍDA - 2026-09-02]

### ✓ Tarefa 1 — Fallback Gemini Live → OpenRouter
- ✓ Tool `deep_reasoning` com timeout 25s/modelo, budget 80s total
- ✓ OpenRouter com `force_provider` em `call_llm_text()`
- ✓ Fallback automático entre modelos :free
- ✓ Bug fix: `_receive_audio` não trava (timeout via `asyncio.wait_for()`)

### ✓ Tarefa 2 — Remoção Módulos Mortos  
- ✓ Deletados: `core/stt.py`, `core/tts.py`, `core/hotkeys.py`
- ✓ Limpeza `core/llm_client.py` e `actions/screen_processor.py`
- ✓ Zero referências stale (validação grep)

### ✓ Tarefa 3 — Centralização Hardware Sensors
- ✓ Novo `core/hw_sensors.py` (GPU/temp, zero subprocess)
- ✓ Importado por `ui.py` e `actions/system_monitor.py`

### ✓ Tarefa 4 — Correções Finais
- ✓ Pylance errors resolvidos (`ensure_ollama_running`, `_nvml_gpu_windows`)
- ✓ Shadowing `platform` → `plat` em `game_updater.py`
- ✓ AST parse: 39 files válidos, zero Pylance errors

---

# SPRINT 4 — Agendador de Tarefas Recorrentes

## Tarefa 1 — Scheduler Genérico
**Status:** [NÃO INICIADO — PRONTO PARA INICIAR]
**Arquivos:** `actions/recurring_task.py` (novo), `main.py`, `memory/config_manager.py`

**Descrição:**
- Criar `actions/recurring_task.py` generalizando scheduler de `actions/game_updater.py`
  - Suportar: `daily`, `weekly`, `monthly`, `every_X_hours`, `every_X_minutes`
  - Persistir em `config/api_keys.json` → `"recurring_tasks": [...]`
  - Cada tarefa: `{"name": "...", "action": "...", "interval": "...", "next_run": "..."}`
  - Initializar ao boot via `JarvisLive.run()`
- Expor tool: `schedule_task(name, action, interval)` em `TOOL_DECLARATIONS`
- Helpers em `memory/config_manager.py`

**Critério de aceite:**
- Usuário fala: "Agendar verificação de emails todo dia às 9h"
- Usuário fala: "Atualizar jogo todas as quartas-feiras"
- Tarefas persistem entre sessões
- Próxima execução calcula-se corretamente

---

## Sprint 1-2 — Histórico
- Sprint 1: Identidade PT-BR, Hotkey F4, Plugins Limpos [✓ CONCLUÍDA]
- Sprint 2: Deep Reasoning + OpenRouter [✓ CONCLUÍDA]