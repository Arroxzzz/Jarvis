# PROJECT_STATE — JARVIS MARK LI — PLANO CONSOLIDADO PÓS-AUDITORIA (2026-09-02)

## STATUS ATUAL — BOOT E PONTO 0 CONCLUÍDOS
Boot confirmado em teste real: sessão Live estável, latência de voz ótima e
`gemini-2.5-flash-native-audio-latest` funcionando.
Tool call de `file_controller` executada durante sessão ativa sem erro 1007,
confirmando a eficácia do lock de serialização do `session`.

## VEREDITO DA AUDITORIA EXTERNA (referência — não redescutir sem novo motivo)
- Arquitetura: 4/10 — `main.py` deus-objeto, duplicação entre
  computer_settings.py/computer_control.py/desktop.py.
- Segurança: 3/10 — sandbox de desktop.py é decorativo (pyautogui injetado
  = RCE de fato), dashboard usa AES-CBC sem MAC + SHA256 sem PBKDF2,
  user_data() sem allowlist de campos.
- Manutenibilidade: 4/10 — zero testes, zero logging estruturado.
- Estabilidade: atualizada após validação real — Ponto 0 implementado e
  confirmado sem erro 1007 durante tool call ativa.
- Performance: 6/10 — boa cobertura de _bounded/timeout na maioria das tools.

## PLANO DE EXECUÇÃO SEQUENCIAL (ordem definitiva — não reordenar sem novo motivo)

### FASE 0 — Estabilização de Boot (CONCLUÍDA)
- Confirmada em teste real a estabilidade do boot e da sessão Live.
- Confirmada latência de voz ótima.
- Modelo validado em execução: `gemini-2.5-flash-native-audio-latest`.
- Critério de aceite atendido: sessão conectada e funcional.

### FASE 1 — PONTO 0: Lock de Serialização do `session` (CONCLUÍDA)
- `asyncio.Lock` e helpers seguros implementados em `main.py`.
- Chamadas de conteúdo e `tool_response` migradas para os helpers
  serializados; `send_realtime_input` permanece fora do lock.
- Teste real confirmado: `file_controller` executou durante sessão ativa
  sem erro 1007.
- Critério de aceite principal atendido: não houve colisão de
  `send_client_content`.

## ACHADOS PÓS-FASE 1 — INVESTIGAR NA FASE 2
- **Prioridade máxima — watchdog:** `_turn_watchdog` disparou
  `Turn travado >15s` logo após o `tool_response` de `file_controller`.
  O `turn_done_event` não foi definido organicamente e precisou da
  intervenção do watchdog. Investigar se é efeito colateral de
  `_safe_send_tool_response` (Ponto 0) ou comportamento pré-existente.
- **Prioridade máxima — shutdown inesperado:** `shutdown_jarvis` foi chamado
  logo em seguida, sem comando explícito visível na transcrição do usuário.
  Pode ser falso positivo do modelo interpretando o silêncio pós-watchdog
  como intenção de encerrar a sessão. Reproduzir de forma controlada.
- **Baixa prioridade — resumo de sessão:** `_save_session_summary` em
  `main.py` falha com 503 sem fallback. Diferentemente de outras chamadas
  Gemini do projeto, não usa `gemini_call_resilient` em
  `core/llm_client.py`. Registrar para a Fase 2 ou 4.

### FASE 2 — Correção de Estados Órfãos e Diagnóstico Pós-Ponto 0
- **Prioridade MÁXIMA:** reproduzir e diagnosticar o disparo de
  `Turn travado >15s` após `file_controller` e o `shutdown_jarvis` inesperado.
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