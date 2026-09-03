# CURRENT_TASK — FASE 0 EM ANDAMENTO — BLOQUEADOR DE BOOT

## Contexto
Auditoria técnica externa completa realizada (2026-09-02). Plano consolidado
em 5 fases está em `.ai/PROJECT_STATE.md`. Este arquivo aponta só a AÇÃO
IMEDIATA — ler PROJECT_STATE.md inteiro antes de qualquer código.

## PRÓXIMA AÇÃO IMEDIATA — Jarvis não inicia sessão de voz
Sintoma relatado: UI carrega normalmente, mas nenhuma resposta a comandos
("Jarvis, tá aí?" → silêncio). Isso é ANTERIOR ao bug do Ponto 0 (que só
se manifesta sob concorrência ativa) — aqui a sessão Live provavelmente
nunca conecta.

### Passos de diagnóstico (fazer antes de qualquer patch)
1. Pedir ao Senhor Paulo o log do CONSOLE (não da UI) no momento do boot.
   Procurar por: `[JARVIS] Connecting...`, seguido de erro ou de
   `[JARVIS] Connected.`.
2. Se não aparecer nem `Connecting...`: problema é anterior —
   `_validate_gemini_key()` falhando silenciosamente ou API key ausente.
3. Se aparecer erro com `1007`/`1008`/`not found for API version`: modelo
   Live indisponível — `LIVE_MODEL_FALLBACKS` (main.py) desatualizado.
4. Teste isolado sugerido:
   ```
   python -c "from google import genai; c=genai.Client(api_key='KEY'); print([m.name for m in c.models.list() if 'live' in m.name.lower()])"
   ```
   Lista vazia = problema de API/região/key, não de código.

### Correção a aplicar (Fase 0 do plano consolidado)
- `main.py::_resolve_live_model` / `_discover_live_models`: adicionar log
  explícito de falha na UI (`self.ui.write_log`), hoje só vai pro console
  e pode passar despercebido.
- Se confirmado catálogo desatualizado: atualizar `LIVE_MODEL_FALLBACKS`
  com IDs válidos retornados por `models.list()`.

**NÃO prosseguir para o Ponto 0 (Fase 1) enquanto o boot não estiver
confirmado funcionando com log real do Senhor Paulo.**

## Depois do boot confirmado — ordem já definida em PROJECT_STATE.md
1. FASE 1 — Ponto 0: lock de serialização do `session` (especificação
   completa em PROJECT_STATE.md). Resolve ESC/texto/1007.
2. FASE 2 — Correção de estados órfãos (_vision_busy, browser_control
   session registry).
3. FASE 3 — Segurança crítica: AES-GCM no dashboard, remover pyautogui do
   sandbox de desktop.py, allowlist em user_data().
4. FASE 4 — Quebrar main.py monolítico + timeout em plugin_loader.run().
5. FASE 5 — Performance (HudCanvas cobertura de visibilidade, write
   atômico de config).

## Decisões já fechadas nesta sprint — NÃO reabrir sem novo motivo concreto
- Model ID Live: manter descoberta dinâmica + cache. NÃO fixar hardcoded.
- Sanitização de logs: reordenada para DEPOIS da Fase 3 (segurança tem
  prioridade sobre ruído operacional, por recomendação da auditoria).
- Seleção de device de áudio: sem hot-swap em runtime na v1.

## Critério de aceite desta tarefa (Fase 0)
- Console mostra `[JARVIS] Connected.` sem erro.
- Jarvis responde a comando de voz/texto simples ("tá aí?").
- Causa raiz do silêncio documentada em PROJECT_STATE.md para não se repetir.