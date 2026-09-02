# CURRENT_TASK — Sprint 4 ENCERRADA / Sprint 5 EM PLANEJAMENTO

## Sprint 4 — Resultado dos Testes Práticos
**Status:** [ENCERRADA — 1 pendência aberta]

1. Boot & Saudação Proativa — ✓ SUCESSO
2. Fuso Horário BRT (zoneinfo) — ✓ SUCESSO
3. Cancelamento ESC do dev_agent — ⚠️ PARCIAL
   Backend interrompe corretamente (threading.Event cooperativo), mas falta
   feedback verbal imediato. AÇÃO: `main.py::interrupt()` deve disparar
   `self.speak()` com frase de personalidade ao cancelar, ANTES de aguardar
   a tool finalizar.
4. Latência do Live API — ❌ GARGALO CRÍTICO CONFIRMADO
   `gemini-2.5-flash-native-audio-preview-12-2025` apresentando 5-40s de
   latência + áudio picotado. CORREÇÃO DE ROTA (ver PROJECT_STATE.md):
   `gemini-1.5-flash` é TECNICAMENTE INVIÁVEL (não suporta Live API, série
   1.5 desligada). Migração real: `gemini-3.1-flash-live-preview` (modelo
   Live recomendado atual, substitui a linha 2.5 native-audio em
   descontinuação).
5. Clipboard listener — DECISÃO: remoção total (não apenas desativação por
   config). Ver justificativa em PROJECT_STATE.md.

## Sprint 5 — Roteamento por Especialidade (PLANEJADA)
- Expandir `FREE_MODELS` em `core/llm_client.py` com categoria `"search"`
  além de `general`/`code`/`reasoning`.
- Roteamento continua baseado no parâmetro `task_type` já existente na tool
  `deep_reasoning` — SEM classificador LLM adicional (evita round-trip extra
  de latência).
- Avaliar fetch dinâmico de `openrouter.ai/api/v1/models` (filtro
  `pricing.prompt==0`) com cache TTL, para não repetir o problema de modelo
  descontinuado sem aviso (mesma causa-raiz do item 4 desta sprint).

**Critério de aceite Sprint 5:**
- ESC gera resposta falada em <1s após cancelamento
- Sessão Live estável com latência 1-3s consistente
- Clipboard 100% removido do código (zero referências residuais)
- `FREE_MODELS["code"]` validado contra catálogo gratuito atual do OpenRouter