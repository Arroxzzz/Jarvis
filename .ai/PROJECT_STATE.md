# PROJECT_STATE — JARVIS MARK LI — PLANO CONSOLIDADO PÓS-AUDITORIA (2026-09-02)

## STATUS ATUAL — BLOQUEADOR ATIVO
Jarvis não inicia sessão de voz (UI carrega, sem resposta a comandos).
Suspeita: `LIVE_MODEL_FALLBACKS` (main.py) desatualizado/depreciado pela
Google, ou `_discover_live_models()` retornando vazio silenciosamente.
AÇÃO IMEDIATA: adicionar log explícito de falha de descoberta em
`_resolve_live_model`/`_discover_live_models` antes de qualquer outra fase.
Não prosseguir para Fase 1 sem o boot funcionando.

## VEREDITO DA AUDITORIA EXTERNA (referência — não redescutir sem novo motivo)
- Arquitetura: 4/10 — `main.py` deus-objeto, duplicação entre
  computer_settings.py/computer_control.py/desktop.py.
- Segurança: 3/10 — sandbox de desktop.py é decorativo (pyautogui injetado
  = RCE de fato), dashboard usa AES-CBC sem MAC + SHA256 sem PBKDF2,
  user_data() sem allowlist de campos.
- Manutenibilidade: 4/10 — zero testes, zero logging estruturado.
- Estabilidade: 3/10 — PONTO 0 especificado mas CONFIRMADO NÃO IMPLEMENTADO
  no código atual (sem asyncio.Lock, sem _safe_send_content em main.py).
- Performance: 6/10 — boa cobertura de _bounded/timeout na maioria das tools.

## PLANO DE EXECUÇÃO SEQUENCIAL (ordem definitiva — não reordenar sem novo motivo)

### FASE 0 — Estabilização de Boot (BLOQUEANTE — fazer primeiro)
- `main.py::_resolve_live_model` / `_discover_live_models`: logar falha de
  descoberta explicitamente na UI (`self.ui.write_log`), não só no console.
- Validar catálogo atual de `LIVE_MODEL_FALLBACKS` contra
  `client.models.list()` real — pendência de teste manual do Senhor Paulo.
- Critério de aceite: `[JARVIS] Connected.` aparece no console e Jarvis
  responde a "tá aí?".

### FASE 1 — PONTO 0: Lock de Serialização do `session`
Especificação técnica completa mantida abaixo (não implementada ainda).
- `main.py::JarvisLive.__init__`: `self._session_lock = asyncio.Lock()`.
- Novo método `_safe_send_content(parts, turn_complete=True)` +
  `_safe_send_tool_response(fn_responses)`, ambos com
  `async with self._session_lock`.
- `send_realtime_input` FICA FORA do lock (áudio contínuo não compete
  com turnos — ver justificativa na especificação original abaixo).
- Migrar TODAS as chamadas diretas em `main.py`:
  `speak`, `plugin_say`, `_on_text_command`, `_execute_tool` (shutdown),
  `_receive_audio` (injeção visão + tool_response + cancel_phrase),
  `_send_startup_briefing`, `_send_boot_greeting`, `_run_system_monitor`,
  `_run_background_monitor`, `_run_proactive_mode`,
  `_process_dashboard_commands`.
- Critério de aceite: ESC durante tool ativa, texto digitado durante fala,
  saudação de boot — sem erro 1007, testado com Senhor Paulo.

### FASE 2 — Correção de Estados Órfãos (efeito colateral do Ponto 0)
- `main.py::_execute_tool` (branch `screen_process`): `try/finally`
  garantindo reset de `_vision_busy` mesmo com `CancelledError`.
- `actions/browser_control.py::_SessionRegistry`: lock em
  `note_native_url`/`pop_native_url` (race entre tool calls paralelas).

### FASE 3 — Segurança Crítica (pré-requisito para uso sem supervisão)
- `dashboard/server.py`: AES-256-CBC → AES-GCM (integridade real).
  Derivação SHA256(pin+salt) → PBKDF2 (lib já em crypto-js.min.js).
- `actions/desktop.py::_build_sandbox`: remover `pyautogui` do sandbox de
  código gerado por IA (hoje é RCE de fato via automação de teclado).
  Restringir `shutil.copy2/copytree` a allowlist de destino.
- `actions/computer_control.py::user_data`: allowlist de campos permitidos
  (hoje qualquer chave de `identity` é exfiltrável para qualquer formulário
  via preenchimento automático).

### FASE 4 — Dívida Técnica (main.py monolítico)
- Quebrar `main.py` em `core/live_session.py` (protocolo),
  `core/tool_dispatcher.py` (dict handler substituindo if/elif gigante),
  `core/background_tasks.py` (monitores/proativo/watchdog).
- `core/plugin_loader.py::PluginRegistry.run`: adicionar timeout
  (`asyncio.wait_for`) — único caminho de tool hoje sem `_bounded`.

### FASE 5 — Performance
- `ui.py::MainWindow`: cobrir "janela coberta mas não minimizada" (hoje só
  `isMinimized()` pausa render — janela em segundo plano sem minimizar não).
- `memory/config_manager.py`: write atômico (temp+rename) — evita
  corrupção de JSON sob escrita concorrente (UI + dashboard).

---

## ⭐ ESPECIFICAÇÃO TÉCNICA DETALHADA DO PONTO 0 (referência de implementação)

### Problema exato
`google.genai.live.AsyncSession` não é seguro para chamadas concorrentes de
`send_client_content()`/`send_tool_response()`/`send_realtime_input()`.
Chamado sem exclusão mútua de: `_send_realtime`, `_receive_audio`, `speak`,
`_on_text_command`, `_send_startup_briefing`, `_send_boot_greeting`,
`_run_system_monitor`, `_run_background_monitor`, `_run_proactive_mode`,
`_process_dashboard_commands`. Colisão temporal → `1007 Request contains
an invalid argument` → derruba o WebSocket inteiro.

### Solução
```python
self._session_lock = asyncio.Lock()

async def _safe_send_content(self, parts: list, turn_complete: bool = True) -> None:
    if not self.session: return
    async with self._session_lock:
        await self.session.send_client_content(
            turns={"parts": parts}, turn_complete=turn_complete
        )
```
Método análogo para `send_tool_response`. `send_realtime_input` fora do
lock (alta frequência ~64ms, não deve esperar por tool call longa).

### Ordem de implementação
1. Lock + métodos seguros.
2. Migrar `speak()`, `interrupt()` (via `_pending_cancel_phrase`),
   `_on_text_command()`.
3. Migrar background tasks (monitor/proativo/dashboard/briefing/boot).
4. Migrar fluxo de tool_response em `_receive_audio()`.
5. Testar: ESC durante tool ativa, texto digitado durante fala, boot do
   zero (saudação).

---

## Decisões já fechadas — NÃO reabrir sem novo motivo concreto
- Model ID Live: manter descoberta dinâmica + cache (`config["live_model_id_cache"]`).
  NÃO fixar hardcoded — já causou a Sprint 4 quebrar.
- Logs: sanitização (print→logging) fica DEPOIS da Fase 3 (segurança),
  não antes — prioridade invertida vs. plano anterior por decisão da
  auditoria externa (risco de exposição > ruído operacional).
- Seleção de device de áudio: sem hot-swap em runtime — só no boot.

## Regras de Ouro (inalteradas)
- PT-BR estrito, tratamento "Senhor" (nunca "sir"/"efendim").
- CPU/GPU mínimo durante jogos.
- Edições cirúrgicas (antes/depois), nunca arquivo completo.
- Erro 1007/1008 NUNCA é prova de API key inválida — diagnosticar `err_str`.
- Após Fase 1: NENHUM acesso a `session.send_client_content`/
  `send_tool_response` fora dos métodos seguros.