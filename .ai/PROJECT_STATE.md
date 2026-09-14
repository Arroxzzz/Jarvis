## STATUS ATUAL (2026-09-13) — MIGRAÇÃO DE UI CONCLUÍDA, 3 FIXES EM VALIDAÇÃO

### CONCLUÍDO E VALIDADO EM PRODUÇÃO (acumulado)
- Fase 0, Fase 1 (Ponto 0), P0 (watchdog inteligente), P1/P2 (Groq→OpenRouter)
- Fase 3 (segurança: AES-GCM dashboard→removido, sandbox desktop, allowlist)
- P7a (Modo Portátil), P6 (Knowledge Vault + sync Supabase), Efeito Coulson
- Prompt Supremo (personalidade JARVIS validada)
- Auditoria Estrutural completa (A1-A8, M1-M6, B1-B4)
- Contexto de tool injetado de volta ao Gemini (fix "burrice" pós P1/P2)
- open_on_monitor (abrir URL em monitor específico sem pyautogui)
- **MIGRAÇÃO DE UI PARA WEBGL/HTML (QWebEngineView)** — concluída:
  - index.html com shader GLSL customizado (plasma orgânico) integrado via QWebChannel
  - Ponte real: jarvisLog, jarvisSetState, jarvisUpdateTelemetry, jarvisSetMuteState
  - Widgets Qt antigos (HudCanvas, LogWidget, MetricBar) desativados — webview ocupa 100% da janela
  - Upload de arquivo via QFileDialog nativo (path real, não mock de input HTML)
  - Interrupt/Mute funcionais como botões no HTML
  - Background throttling do Chromium desabilitado (QTWEBENGINE_CHROMIUM_FLAGS) —
    FPS do WebGL mantido mesmo com janela minimizada/sem foco, por decisão do
    Senhor Paulo (GPU com folga, prioridade em fidelidade visual sobre economia)

### BUGS ENCONTRADOS E CORRIGIDOS NESTA RODADA (aguardando validação de campo)
- Duplicação de log completo na UI após reconexão de sessão (causa: TaskGroup
  reinicia do zero mas UI não limpava histórico anterior) — FIX: `clear_log()`
  chamado em reconexões reais, distinguindo do boot inicial.
- Erro 1007 novo e específico (`CONTENT_TYPE_AUDIO not supported for this
  model configuration`) após troca de voz para Fenrir — suspeita de
  incompatibilidade entre Fenrir e a config atual (affective_dialog).
  FIX: revertido para `Charon` até nova validação isolada.
- `open_app` sendo usado para abrir PASTAS, causando busca via menu Iniciar
  do Windows (rouba foco, simula tecla, quebra a promessa de "nunca
  sequestrar o mouse/teclado do usuário"). FIX: nova tool `open_folder`
  usando `subprocess.Popen('explorer "path"')` — zero simulação de input,
  abre direto no Explorer.

### PENDENTE DE INVESTIGAÇÃO (não bloqueante)
- Sync Supabase falhando em arquivos com nome acentuado
  (`Memória Jarvis.md` → 400 Bad Request) — suspeita de URL encoding
  quebrado no path do Storage bucket. Não corrigido ainda.
- Responsividade da UI em telas menores (botões desaparecendo) — tentativa
  de fix externo quebrou a UI, revertida. Requer abordagem cuidadosa e
  isolada, não aplicar sugestões de terceiros sem revisão prévia.

### REGRAS DE OURO (acumuladas, reforçadas nesta rodada)
- PT-BR estrito, tratamento "Senhor" (nunca "sir"/"efendim")
- CPU/GPU: prioridade em fidelidade visual da UI sobre economia agressiva,
  por decisão explícita do Senhor Paulo (hardware com folga) — WebGL roda
  sem throttle mesmo em segundo plano
- Nenhuma automação deve simular teclado/mouse quando existe alternativa
  via subprocess/API nativa (regra reforçada pelo caso open_app vs.
  open_folder) — pyautogui é último recurso, não primeira escolha
- Sistema 100% gratuito — zero API paga, zero cartão cadastrado
- Mudanças de UI/layout: sempre revisar diff antes de aplicar, nunca
  aplicar sugestão externa às cegas em código já validado