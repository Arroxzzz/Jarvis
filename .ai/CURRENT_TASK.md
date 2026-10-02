## Fase 7 — Estabilização de Voz, Ferramentas e Custo (concluída)

- [x] Registro histórico do watchdog: a correção inicial moveu o reset do contador para a conclusão do turno; a implementação atual usa timeout de 20 segundos para reconectar uma resposta pendente.
- [x] Ferramentas síncronas travavam o áudio inteiro — dispatch_tool agora roda em ThreadPoolExecutor
- [x] open_app trocado de simulação de teclado (pyautogui) pra os.startfile nativo
- [x] Modelo morto groq/compound-mini removido; circuit breaker não bloqueia mais o provider inteiro por erro 404
- [x] Bug de "zumbi" na reconexão corrigido (resumption_handle resetado em erro real)
- [x] Código morto removido: actions/game_updater.py, plugins/pushup_counter.py
- [x] Ferramenta open_file criada em actions/file_controller.py (capacidade que faltava)
- [x] dev_agent.py e computer_control.py::_screen_find rerroteados pro sistema de fallback (paravam de consumir cota real do Gemini à toa)
- [x] Exceção silenciosa no pipeline do microfone agora loga o erro real (_log_gated_chunk_error)
- [x] core/prompt.txt: regra anti-enrolação (não recita plano duas vezes) e anti-tabela (resume em vez de narrar tabela inteira)
- [x] Memória do Obsidian reconectada ao boot da sessão (build_boot_digest em knowledge_vault.py)
- [x] Wake word implementado com openWakeWord — core/wake_word_gate.py (buffer rolante 8s, palavra em qualquer posição da frase, janela de graça de 12s, threading corrigido, timing de fechamento corrigido)
- [x] Roteamento de LLM pago implementado: Groq (grátis, primeira tentativa) → GLM-5.3-Flash/DeepSeek V4.1 Flash (pago, OpenRouter) → Claude Sonnet 5 isolado só em deep_reasoning
- [x] OpenRouter free removido de core/llm_client.py (redundante com o degrau pago)

## Fase 8 — Auditoria Geral (em andamento)

- [x] Conferência objetiva dos três documentos contra os módulos diretamente relacionados, sem leitura linha a linha do projeto
- [x] Confirmar que H5 não descreve mais o watchdog atual: `_turn_watchdog` reconecta quando uma resposta pendente passa de 20 segundos sem atividade
- [ ] Investigar a qualidade do reconhecimento de fala de ponta a ponta; `_join_transcript` corrige a junção de fragmentos nos logs, mas a instrumentação temporária `[Transcript]` ainda existe em `main.py`
- [ ] Investigar se o turno de ~100s visto uma vez após reconexão ainda ocorre (pode já ter sido resolvido pelo fix do zumbi de resumption)
- [ ] Decidir se testa Vertex AI Express Mode (voz grátis por 90 dias) numa conta Google virgem
- [ ] Buscar mais dead code / duplicação além do que já foi limpo na Fase 7
- [ ] Concluir a validação do wake word em três dias de uso real; a configuração local atual o habilita com modelo ONNX próprio

## Registro histórico — estado final da linha de produto

### Roadmap aprovado — fases 0 a 5

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

### Estado de execução registrado à época
- [x] Fases 0, 1 e 2 concluídas e validadas.
- [x] Projeto usa `tool_registry` em vez de `if name == ...` no `main.py`.
- [x] Projeto usa `memory/context_index.db` (SQLite) para buscas rápidas de contexto local.
- [x] Suíte relevante confirmada em verde: `78 passed in 2.75s`.

**Próxima etapa definida naquele registro: operação real controlada e refinamento final**

Naquele momento, essa fase aguardava o comando do Senhor, sem mexer no loop de voz nem na linha então estável.

### Fase 3 — Sinal Verde (Write Guard)
- [x] `core/write_guard.py` criado com `is_write_allowed()`, `request_confirmation()` e log em `memory/audit_log.jsonl`
- [x] `file_controller.py` usa o guard central para delete/move/rename/write
- [x] `computer_settings.py` usa o guard para restart/shutdown
- [x] `game_updater.py` foi removido posteriormente; não há mais integração a proteger nesse módulo
- [ ] Verificar se `code_helper.py` e `computer_control.py` passam pelo guard em todos os pontos irreversíveis
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

### Fase 6 — Destinatário (DESCARTADA / REMOVIDA EM DEFINITIVO)
- [x] Filtro de endereçamento artificial (`core/addressee.py`, `_addr_*` no `main.py`, config `addressee_mode` e testes) completamente REMOVIDO por decisão do Senhor. O filtro causava atrasos de turno, mutava respostas legítimas e induzia estados fantasmas de surdez no microfone.
- [x] Fase 3 — tools: `core/tool_registry.py::dispatch_tool` corrigido para logar e retornar erro detalhado em vez de engolir exceções; `open_app` e schema em `core/tool_declarations.py` atualizados com suporte ao parâmetro `monitor` (posicionamento via `_move_to_monitor`).
- [x] Estado registrado ao fim da Fase 6: captura de áudio/microfone (`underrun` no sounddevice) seguia como frente de diagnóstico; o watchdog H5 foi resolvido posteriormente e não é uma pendência atual.

#### Achados novos da Fase 6 (fora do escopo original)

- **H5 — bug no watchdog** (`main.py::_turn_watchdog`): na Fase 6, o contador de tentativas parecia impedir a reconexão completa. Achado histórico, superado pela implementação atual que reconecta após 20 segundos sem resposta.
- **H6 — suspeita de microfone preso**: num travamento do S1, `heard=''` por ~1m40s, sugerindo captura fechada (`_is_speaking` preso em `True`) durante a queda. Não confirmado — cruzar com a métrica `speaking` (já instrumentada) no próximo travamento real.
- **Qualidade de transcrição (achado novo)**: a transcrição de entrada do Gemini erra com frequência mesmo com fala clara — ex. real: "Jarvis, que horas são?" → "Já rve, que horas são?"; "Quanto é 17 x 23" → "Quando quer 17 x 23". HIPÓTESE NÃO CONFIRMADA: falta de tratamento de áudio (ruído/ganho) em `main.py::_listen_audio`, que envia PCM cru ao Gemini sem pré-processamento local. Pode afetar o classificador (quando "Jarvis" não é pego pela regex) e a execução de tools. Não investigado — candidato a virar prioridade própria.

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

## Estado registrado após a linha de produto inicial (histórico)

- A base do JARVIS está funcional e segura dentro do escopo validado.
- O caminho principal de voz continua intacto; o loop de áudio não foi alterado por estas camadas.
- A memória local usa Obsidian/Markdown e guarda registros elegíveis com origem, contexto e confiança; o caminho deixou de ser fixo e passou a ser configurável por `vault_path`.
- O contexto do computador usa busca limitada e rótulos amigáveis, sem expor caminhos absolutos para o usuário.
- O `dev_agent` atua em revisão e mentoria guiada, sem aplicar alterações automáticas sem aprovação.
- O sistema respeita as regras de segurança: confirmação para ações sensíveis, rejeição de segredos, bloqueio de gravações casuais e opt-in por padrão para plugins externos.
- O carregamento de plugins foi fechado em segurança: módulos novos ou desconhecidos não são ativados sem consentimento explícito do usuário.

## Próximos passos definidos naquele registro

- [x] Usar a linha de produto atual em operação real de rotina, sem expandir escopo.
- [x] Recolher feedback de uso real em alguns turnos controlados para ajustar UX e mensagens.
- [x] Só depois decidir se abre a próxima camada: otimização de casa, sincronização adicional ou refinamento final de presença.
- [x] Validar em uso real o comportamento de abertura de pastas e de criação/movimentação de arquivos em tarefas do dia a dia antes de abrir a próxima etapa de refinamento do assistente.
- [x] Iniciar a Fase 2 — Context Index (SQLite) com busca contextual e fallback incremental.
- [x] Concluir a Fase 3 — Write Guard e a Fase 4 — Limpeza do Task Runtime.
- [x] Concluir a Fase 5 — Obsidian Vivo (WikiLinks).

### Estado operacional registrado à época

A linha validada naquele momento era a linha segura: voz contínua, memória local, contexto contextualizado, diagnóstico guiado e plugin opt-in. O avanço recomendado à época era uso real controlado, não expansão de autonomia.

## Restrições finais

- PT-BR estrito e trato "Senhor".
- Nenhum LLM local; GPU reservada para jogos.
- Ninguém altera código de produção sem aprovação explícita.
- Nenhuma automação destrutiva sem confirmação local.
- A experiência deve parecer inteligente, mas sempre dentro do escopo seguro e mensurável.

## Encerramento registrado à época

O registro da época considerava a linha de produto pronta para uso seguro e validado; isso não substitui as pendências da Fase 8 listadas no início deste arquivo.

## Histórico — execução do plano de auditoria e melhorias posteriores
- [x] Fase 1: remoção de actions/coulson_listener.py, tools/encrypt_notification.py e plugins/upload_video.py
- [x] Fase 2: max_tokens por tipo, vazio/length = falha, .bak antes de sobrescrever, web_search com DDG primeiro, flight_finder resiliente e sem tfs
- [x] Fase 2B: hotfix (diagnóstico e esforço de raciocínio, breaker por modelo, dev_agent topológico/retry/abort/allowlist, web_search cru sem modo price, resolução de arquivo)
- [x] Fase 3: gate de confirmação por voz ("confirmo") para send_message, delete, restart, shutdown
- [x] Fase 4: watchdog "aguardando resposta" (_awaiting_response) e correção do close_gate do wake word
- [x] Fase 4B: wake word desligado por padrão após o modelo hey_jarvis não detectar "Jarvis" com fonética PT-BR; esse estado foi superado pela calibração e ativação do modelo próprio descritas na validação operacional abaixo.
- [x] Fase 5: cofre 600k iterações (crypto_vault.py + boot_stage0.py, requer recifrar api_keys.enc/project.enc manualmente), vault Obsidian configurável via "vault_path" (antes fixo em D:\Memoria_Jarvis), get_home_dir() em code_helper/flight_finder/context_resolver, reindex duplicado removido do boot, DESTRUCTIVE_ACTIONS morta removida, gate de confirmação por voz estendido a shutdown_jarvis, código morto removido de web_search.py
- [x] Fase 5B: busca no vault roteada corretamente (knowledge_note em vez de find_context via prompt.txt/tool_declarations) e find_context passa a cobrir o vault também no fallback de varredura (_default_roots)
- [x] Fase 5C: save_memory (modo "sugerido") passa pelo portão de confirmação por voz; knowledge_note/search_notes agora busca também pelo título da nota, não só pelo conteúdo
- [x] Correção Fase 5C: save_memory deixou de exigir "confirmo" falado (era overreach — memória é local/reversível, diferente de ações externas). Corrigido na raiz: parâmetro user_confirmed no schema da tool, que o modelo marca true quando o usuário pede explicitamente para lembrar/salvar/registrar.
- [x] Fase 6: dev_agent roda em segundo plano (retorna na hora, anuncia via speak() ao terminar), background_status e cancel_background_task novos, interrupt() agora cancela tarefas em background de verdade (self._tasks.cancel_all_running())
- [x] Fase 6B: persona executiva (PROTOCOLO DE FALA + exemplos) no prompt.txt; humanize_for_speech em core/paths.py aplicado em speak() e nos retornos de code_helper/flight_finder/file_processor; resumo curto do build; sem fala duplicada (dev_agent silencioso antes, "Em andamento" depois; cancelado não anuncia conclusão)
- [x] Fase 7: proatividade local opt-in (regras de uso contínuo + hora; get_idle_seconds/is_foreground_fullscreen nativos; 1 aviso/hora, cada regra 1x/dia; proactive_mode por voz; alertas de sistema e notícias mudos em tela cheia; auditoria em audit_log.jsonl)
- [x] Fase 6C: log do painel sem duplicar/partir (_split_log); transcrição sem espaços falsos (_join_transcript) e portão de confirmação tolerante a palavra partida; saudação de boot em 1ª pessoa sem citar o nome; regra "nunca diga o próprio nome" no prompt; diagnóstico TEMPORÁRIO [Transcript] em _receive_audio (remover após descobrir a causa da frase duplicada em turnos com ferramenta)

## Validação operacional do wake word (subtarefa pendente)
- [x] 8A: wake word configurável (wake_word_model, wake_word_threshold, wake_word_grace_sec, wake_word_buffer_sec, wake_word_vad), estado visível no painel, tools/wake_eval.py, "confirma" aceito no portão de voz
- [x] 8B: gravar amostras (pos / pos_hey / neg / ambient), medir o hey_jarvis atual, decidir entre ajustar limiar ou treinar modelo próprio e treinar
- [x] 8C: modelo próprio `models/wake/jarvis.onnx` configurado e wake word habilitado na configuração local verificada
- [ ] 8D: validar 3 dias de uso real (pendente; não há evidência registrada de conclusão)
- Modelo: models/wake/jarvis.onnx (treinado em D:\WakeTrain com o nibor1896/custom-wakeword-trainer, commit 7cadc33; 25.000 passos em CPU, 8 min 33 s; ACAV usado). Limiar 0.5.
- Prova independente (wake_samples, 30 clipes "Jarvis", 30 de fala normal, 10 min de ambiente): acerto 83%, 1 falso em 30 falas normais, 0 falsos/hora no ambiente. Aceito pelo Senhor até segunda ordem.
- Critério da 8D: ≤ 2 acordadas falsas em 3 dias e < 1 falha a cada 10 chamadas; senão, retreinar (gravar mais positivos lentos/baixos, sem apagar nada em D:\WakeTrain\trainer\data).