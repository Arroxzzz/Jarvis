# PROJECT_STATE — JARVIS MARK LI — HISTÓRICO CONSOLIDADO E ROADMAP (atualizado)

## STATUS ATUAL (2026-09-05) — P1/P2 validados, refinamentos em andamento

### Confirmado funcionando em produção
- Groq (gpt-oss-120b/20b) + OpenRouter (openrouter/free) — zero erro de
  URL/modelo desde a correção de endpoint duplicado e catálogo atualizado.
- Fala imediata durante pesquisa/código ("pesquisando...", "criando o
  código, te aviso quando terminar") — UX aprovada pelo Senhor Paulo.
- screen_process, save_memory, proatividade (ex: aviso ao abrir jogo) —
  funcionando organicamente.

### Bugs encontrados e corrigidos nesta rodada
- Watchdog disparava falso-positivo durante execução de tool em
  background (padrão ack-imediato+fala-depois do P1/P2 criou gap de
  áudio >15s entre os dois turnos). FIX: contador `_bg_tasks_pending`
  congela o watchdog enquanto qualquer tool (síncrona ou em background)
  está ativa.
- Reconexão forçada pelo watchdog descartava contexto da sessão por
  completo ("esqueceu" jogo recém-criado) — `session_resumption` estava
  configurado mas o handle nunca era capturado/reenviado. FIX: captura
  de `response.session_resumption_update` e reuso no `_build_config`.
- JARVIS falando de si mesmo em 3ª pessoa ("JARVIS confirmou..."). FIX:
  regra explícita em core/prompt.txt.

### Pendente de teste real (Senhor Paulo)
- Validar que reconexão forçada não causa mais amnésia.
- Validar que watchdog não dispara mais durante web_search/code_helper.

### Ainda não iniciado
- P3 — Segurança (AES-GCM dashboard, sandbox desktop.py, allowlist
  user_data) — diffs já entregues em sessão anterior, aplicação pendente.
- P6 — Memória em nuvem (Supabase).
- P7 — Modo portátil (pen drive).
- Investigação aberta, não bloqueante: corte de fala do usuário no meio
  de frase por VAD server-side — ajustável via RealtimeInputConfig se
  necessário no futuro, adiado a pedido do Senhor Paulo.
- Pendência externa ao código: vídeo de "trava de microfone" mencionado
  pelo Senhor Paulo em sessão anterior — reenvio solicitado, sem contexto
  registrado neste histórico ainda.

## LINHA DO TEMPO CONSOLIDADA

### FASE 0 — Estabilização de Boot ✅ CONCLUÍDA (validada em campo)
- Descoberta dinâmica de modelo Live com cache, ranking priorizando
  "native-audio" sobre "live-preview"/"translate"/"transcribe".
- Log explícito de falha de descoberta na UI.

### FASE 1 — PONTO 0: Lock de Serialização do session ✅ CONCLUÍDA (validada em campo)
- `asyncio.Lock` + `_safe_send_content`/`_safe_send_tool_response` em main.py.
- Zero erro 1007 confirmado sob estresse real (ESC múltiplo, tool calls
  concorrentes, quota estourada).
- Classificação de erro corrigida para ler dentro de ExceptionGroup
  (bug que impedia troca de modelo em falha dentro do TaskGroup).

### P0 — Watchdog Inteligente + Resumo Resiliente ✅ CONCLUÍDA (validada em campo)
- `_turn_watchdog`: aviso na UI + contador de 5 disparos + reconexão
  forçada em travamento persistente (não mais loop infinito de reset).
- `_save_session_summary` migrado para camada resiliente (sem depender
  só de Gemini direto).

### P1/P2 — Migração de Resiliência de Texto (Gemini isolado para voz) ✅ IMPLEMENTADA
REGRA DE OURO NOVA: Gemini é usado EXCLUSIVAMENTE por
`main.py::JarvisLive` (voz ao vivo). Nenhuma tool/action chama Gemini
para texto ou visão.
- `core/llm_client.py`: nova camada `resilient_text_call`/
  `resilient_vision_call`. Cadeia: **Groq free (primário) → OpenRouter
  free (fallback)**. `gemini_call_resilient` mantido como alias de
  compatibilidade, mesma cadeia por baixo.
- `GROQ_MODELS` dict por categoria (reasoning/code/vision/search/general).
- Migrados: `web_search.py`, `code_helper.py` (texto + screen_debug
  vision), `file_processor.py`, `desktop.py`, `youtube_video.py`,
  `flight_finder.py`, `computer_settings.py`, `upload_video.py`.
- `dev_agent.py` já usava `gemini_call_resilient` — herda automaticamente.
- **EXCEÇÃO DOCUMENTADA:** `file_processor.py::_process_audio::transcribe`
  ainda usa Gemini multimodal de áudio — sem equivalente gratuito
  direto em Groq/OpenRouter. Decisão pendente (Whisper local ou manter
  exceção).
- Config necessária: `groq_api_key` em `config/api_keys.json`
  (console.groq.com, gratuito).

## GAPS CONHECIDOS E NÃO IMPLEMENTADOS (por ordem de dependência)

### P3 — Segurança Crítica (PENDENTE — maior risco em aberto)
- AES-256-CBC → AES-GCM em dashboard/server.py.
- SHA256 puro → PBKDF2 na derivação de chave do dashboard.
- Remover `pyautogui` do sandbox de `actions/desktop.py::_build_sandbox`.
- Allowlist de campos em `actions/computer_control.py::user_data`.

### P4 — Silero VAD (PENDENTE, baixo risco de execução mas alto risco de regressão)
- Filtro de silêncio local antes de enviar áudio ao Gemini Live.
- Só entrar depois de P3 fechada — mexe no pipeline de áudio já estável.

### P5 — Ollama: ARQUIVADO por decisão do Senhor Paulo (competiria com jogos).

### P6 — Memória em Nuvem (Supabase) — NOVO, NÃO INICIADO
- Motivação: `memory/long_term.json` local não sobrevive a formatação/
  troca de máquina; hoje truncado em MEMORY_MAX_CHARS=2200 (resumo, não
  histórico ilimitado).
- Plano: tabela `memory_entries` (categoria, chave, valor, updated_at,
  user_id) no Supabase Postgres (free tier), substituindo backend de
  `memory/memory_manager.py` mantendo a mesma API pública
  (load_memory/save_memory/update_memory) — trocar só a camada de I/O.
- Pré-requisito: P3 concluída antes de subir dados para nuvem.

### P7 — Modo Portátil (Pen Drive) — NOVO, NÃO INICIADO
- Objetivo: rodar JARVIS de pen drive em PC anfitrião (ex: faculdade)
  sem deixar rastro no PC anfitrião ao final da sessão.
- Bloqueador atual: uso de `Path.home()` espalhado em várias actions
  (reminder.py, screenshot em computer_control.py, etc.) grava fora do
  pen drive por padrão — precisa de "modo portátil" com paths
  redirecionados para o pen drive.
- Memória de sessão portátil só sobrevive à perda física do pen drive
  se sincronizada com P6 (Supabase). Sem isso, perda é definitiva.
- Dependência: P6 concluída antes de iniciar esta fase.

### Modularização de main.py e Performance — adiado, sem nova ação definida
(ver seção antiga de FASE 4/5 no histórico do projeto — não descartado,
só sem prioridade atual frente a P3/P6/P7).

## SEGURANÇA DE CÓDIGO-FONTE E CHAVES (decisão fechada)
- `config/api_keys.json` no `.gitignore` — nunca vai para repositório
  nem deve ser copiado para pen drive em texto puro.
- Código-fonte: repositório Git privado remoto é o backup primário
  (não pen drive/HD local isolado). Pen drive é backup físico
  secundário + veículo do modo portátil (P7).
- Migração de ambiente: chave de API deve ser digitada manualmente no
  boot (SetupOverlay já existe) ou recuperada de cofre remoto — nunca
  embutida em artefato portátil.

## Regras de Ouro (acumuladas, inalteradas)
- PT-BR estrito, tratamento "Senhor" (nunca "sir"/"efendim").
- CPU/GPU mínimo durante jogos.
- Edições cirúrgicas (antes/depois), nunca arquivo completo.
- Erro 1007/1008 nunca é prova de API key inválida.
- Gemini EXCLUSIVO para voz ao vivo — nenhuma tool deve chamá-lo.
- Sistema 100% gratuito — nenhuma API paga, nenhum cartão cadastrado.
