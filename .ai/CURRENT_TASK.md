# CURRENT_TASK — FASE 2 — DIAGNÓSTICO PÓS-PONTO 0

# STATUS CONFIRMADO
- **Fase 0 — Estabilização de Boot: CONCLUÍDA.** Teste real confirmou boot
   estável, latência de voz ótima e `gemini-2.5-flash-native-audio-latest`
   funcionando.
- **Fase 1 — Ponto 0: CONCLUÍDA.** `file_controller` executou em sessão ativa
   sem erro 1007.
- Fases 0 e 1 não devem ser reabertas sem novo motivo concreto.

## Contexto
Auditoria técnica externa completa realizada (2026-09-02). Plano consolidado
em 5 fases está em `.ai/PROJECT_STATE.md`. Este arquivo aponta a ação imediata
de diagnóstico da Fase 2.

## PRÓXIMA AÇÃO IMEDIATA — Reproduzir achados pós-Fase 1
Pedir ao Senhor Paulo para repetir o cenário com comando de voz seguido de
tool call de arquivo, mantendo o log completo do terminal. Confirmar se:

1. `_turn_watchdog` dispara `Turn travado >15s` logo após o `tool_response`.
2. `shutdown_jarvis` é chamado sem comando explícito do usuário.

O objetivo é distinguir efeito colateral de `_safe_send_tool_response` de
comportamento pré-existente e confirmar se o shutdown é uma interpretação
indevida do modelo após o watchdog.

## Próximas fases — ordem já definida em PROJECT_STATE.md
1. FASE 2 — Diagnóstico máximo do watchdog e do `shutdown_jarvis` inesperado;
   depois correção de estados órfãos (`_vision_busy`, browser_control
   session registry).
2. FASE 3 — Segurança crítica: AES-GCM no dashboard, remover pyautogui do
   sandbox de desktop.py, allowlist em user_data().
3. FASE 4 — Quebrar main.py monolítico + timeout em plugin_loader.run().
4. FASE 5 — Performance (HudCanvas cobertura de visibilidade, write
   atômico de config).

## Decisões já fechadas nesta sprint — NÃO reabrir sem novo motivo concreto
- Model ID Live: manter descoberta dinâmica + cache. NÃO fixar hardcoded.
- Sanitização de logs: reordenada para DEPOIS da Fase 3 (segurança tem
  prioridade sobre ruído operacional, por recomendação da auditoria).
- Seleção de device de áudio: sem hot-swap em runtime na v1.

## Critério de aceite da Fase 2
- Reprodução controlada com log completo do terminal.
- Causa do `Turn travado >15s` após `file_controller` identificada.