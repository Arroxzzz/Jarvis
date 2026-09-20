# CURRENT_TASK — ESTADO FINAL DA LINHA DE PRODUTO

## Roadmap aprovado — fases 0 a 5

### Fase 0 — Rede de Segurança
- [x] `git tag v1-monolith-baseline`
- [x] `python -m pytest tests/ -v` validado com 76 testes verdes
- [x] `.ai/BASELINE_MANUAL.md` criado com os 7 fluxos manuais com resultado anotado
- [x] Commit `chore: baseline pre-refactor` concluído

### Fase 1 — Tool Registry
- [x] `core/tool_registry.py` criado com `ToolSpec`, `_REGISTRY`, `@register_tool`, `get_declarations()` e `dispatch()`
- [x] `open_app`, `weather_report` migrados para registro por decorator
- [x] `browser_control`, `file_controller`, `open_on_monitor`, `send_message`, `reminder`, `youtube_video` migrados
- [x] `computer_settings`, `desktop_control`, `code_helper`, `dev_agent`, `web_search`, `file_processor`, `computer_control`, `game_updater`, `flight_finder`, `system_status`, `deep_reasoning`, `manage_monitor` migrados
- [x] Casos especiais mantidos fora do registry: `find_context`, `save_memory`, `knowledge_note`, `sync_memory`, `shutdown_jarvis`, `screen_process`, `close_camera`
- [x] `_execute_tool_impl` reduzido para casos especiais + fallback do registry
- [x] `TOOL_DECLARATIONS` derivado de `tool_registry.get_declarations()` com mescla dos casos especiais
- [x] 7 fluxos da Fase 0 revalidados

### Fase 2 — Context Index (SQLite)
- [x] `core/context_index.py` criado com SQLite + FTS5, `rebuild_index()`, `query()`
- [x] `core/context_resolver.py` usa `context_index.query()` com fallback para `rglob` quando o banco estiver vazio
- [x] Indexação inicial em background no boot sem bloquear o Live connect
- [x] Reindexação agendada a cada 15 minutos
- [x] 7 fluxos da Fase 0 revalidados + latência do fluxo "ache o relatório final" registrada antes/depois

### Estado de execução final
- [x] Fases 0, 1 e 2 concluídas e validadas.
- [x] Projeto usa `tool_registry` em vez de `if name == ...` no `main.py`.
- [x] Projeto usa `memory/context_index.db` (SQLite) para buscas rápidas de contexto local.
- [x] Suíte relevante confirmada em verde: `78 passed in 2.75s`.

**PRÓXIMA ETAPA: operação real controlada e refinamento final**

Essa fase aguarda o comando do Senhor para continuar, sem mexer no loop de voz nem na linha estável atual.

### Fase 3 — Sinal Verde (Write Guard)
- [x] `core/write_guard.py` criado com `is_write_allowed()`, `require_confirmation()` e log em `memory/audit_log.jsonl`
- [x] `file_controller.py` usa o guard central para delete/move/rename/write
- [x] `computer_settings.py` usa o guard para restart/shutdown
- [ ] `game_updater.py`, `code_helper.py` e `computer_control.py` passam pelo guard em pontos irreversíveis
- [x] 7 fluxos da Fase 0 revalidados; os pontos irreversíveis restantes foram mapeados para decisão posterior

### Fase 4 — Limpeza do Task Runtime
- [x] `core/background_tasks.py` criada com `BackgroundTaskTracker`
- [x] Estado e métodos de background task/painel movidos do `main.py`
- [x] `JarvisLive` usa `self._tasks = BackgroundTaskTracker()`
- [x] Watchdog usa `self._tasks.pending_count()`
- [x] 7 fluxos da Fase 0 revalidados; suíte principal: 78 testes verdes

### Fase 5 — Obsidian Vivo (WikiLinks)
- [x] `write_note()` extrai entidades candidatas por regex e converte a primeira ocorrência em `[[WikiLink]]`
- [x] `backlinks(note_name) -> list[str]` implementado por busca reversa case-insensitive
- [x] `context_index.py` indexa também `.md` do vault Obsidian
- [x] `search_context()` considera backlinks como sinal extra de relevância
- [x] 7 fluxos da Fase 0 revalidados; suíte completa: 78 testes verdes

### Fase 6 — Destinatário (Jarvis dos cinemas)
- [x] S0 instrumentação (`memory/metrics.log`)
- [x] S1 baseline (o Jarvis responde a tudo; sessão instável)
- [x] S2 proactive audio nativo — FALHOU (respondeu a 100% das falas não dirigidas)
- [x] S3 medição: transcrição chega antes do áudio (heard_late=0), folga ~1 s
- [x] Fase 2a classificador `core/addressee.py` (isolado, com testes)
- [ ] Fase 2b ligar ao Jarvis (segurar o áudio, descartar, HUD, log explícito)
- [ ] Fase 2c teste em lotes
- [ ] Fase 1 descartada (só valia se o S2 passasse) · Fase 3 tools · Fase 4 instabilidade por logs

## Concluído

- [x] Tela branca e recuperação da UI após minimizar/restaurar.
- [x] Telemetria removida do HUD, JavaScript e backend.
- [x] Sinais Qt validados para WebEngine.
- [x] Microfone/VAD restaurados e estáveis.
- [x] Painel HTML para pesquisas e resultados longos.
- [x] `deep_reasoning` restrito a casos genuinamente complexos.
- [x] Timeout de visão e reconexão controlada.
- [x] Instrumentação não sensível de turnos, áudio, tools e providers.
- [x] Baseline real validado com métricas p50/p95/máximo.
- [x] Roteamento determinístico, timeouts e fallbacks de provider.
- [x] Reincidência de contexto em background controlada.
- [x] Confirmações locais para ações destrutivas.
- [x] Ajuste final da política de arquivos: somente exclusão exige confirmação; ações não destrutivas seguem o fluxo normal.
- [x] Correção de `open_folder`: não pede confirmação desnecessária e não informa falso sucesso quando o Explorer falha.
- [x] Memória local com política de 4 estados: automatic, suggested, explicit e ignore.
- [x] Contexto local de arquivo e projeto ativo em busca segura.
- [x] Revisão/mentoria segura do projeto sem autoalteração.
- [x] Integração final da memória no fluxo textual com confirmação de itens sugeridos.
- [x] Suíte relevante verde: 76 testes passaram em 2.91s.
- [x] Plugins externos e desconhecidos protegidos por opt-in por padrão.
- [x] Log de boot atualizado para reportar apenas plugins ativos e desligados.

## Estado atual do sistema

- A base do JARVIS está funcional e segura dentro do escopo validado.
- O caminho principal de voz continua intacto; o loop de áudio não foi alterado por estas camadas.
- A memória local usa Obsidian/Markdown em `D:\Memoria_Jarvis` e guarda registros elegíveis com origem, contexto e confiança.
- O contexto do computador usa busca limitada e rótulos amigáveis, sem expor caminhos absolutos para o usuário.
- O `dev_agent` atua em revisão e mentoria guiada, sem aplicar alterações automáticas sem aprovação.
- O sistema respeita as regras de segurança: confirmação para ações sensíveis, rejeição de segredos, bloqueio de gravações casuais e opt-in por padrão para plugins externos.
- O carregamento de plugins foi fechado em segurança: módulos novos ou desconhecidos não são ativados sem consentimento explícito do usuário.

## Próximo passo recomendado

- [x] Usar a linha de produto atual em operação real de rotina, sem expandir escopo.
- [x] Recolher feedback de uso real em alguns turnos controlados para ajustar UX e mensagens.
- [x] Só depois decidir se abre a próxima camada: otimização de casa, sincronização adicional ou refinamento final de presença.
- [x] Validar em uso real o comportamento de abertura de pastas e de criação/movimentação de arquivos em tarefas do dia a dia antes de abrir a próxima etapa de refinamento do assistente.
- [x] Iniciar a Fase 2 — Context Index (SQLite) com busca contextual e fallback incremental.
- [x] Concluir a Fase 3 — Write Guard e a Fase 4 — Limpeza do Task Runtime.
- [x] Concluir a Fase 5 — Obsidian Vivo (WikiLinks).

### Estado operacional atual

A linha que está em produção hoje é a linha segura e validada: voz contínua, memória local, contexto contextualizado, diagnóstico guiado e plugin opt-in. O próximo avanço relevante é uso real controlado, não expansão de autonomia nem acréscimo de escopo.

## Restrições finais

- PT-BR estrito e trato "Senhor".
- Nenhum LLM local; GPU reservada para jogos.
- Ninguém altera código de produção sem aprovação explícita.
- Nenhuma automação destrutiva sem confirmação local.
- A experiência deve parecer inteligente, mas sempre dentro do escopo seguro e mensurável.

## Encerramento da fase atual

A linha de produto atual está pronta para uso seguro e validado. O próximo avanço deve ser apenas refinamento de uso real, não criação de novas promessas de autonomia.