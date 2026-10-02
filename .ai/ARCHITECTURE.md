# JARVIS MARK LI — ARQUITETURA ATUAL

## Estado real do sistema

- Interface atual: UI WebEngine hospedada em PyQt6, com a GUI em thread principal e a sessão em thread asyncio separada. Os builders/widgets Qt legados foram removidos.
- Voz: Gemini Live como canal principal. Para tools e texto, a cadeia padrão é Groq → OpenRouter; Claude Sonnet 5 fica restrito a `deep_reasoning`. Não há LLM local na configuração de produto.
- Memória: política em 4 estados; fatos estruturados, sessões, projetos, pessoas e notas locais ficam em Markdown no vault configurado por `vault_path`. Estado volátil de runtime fica em `memory/runtime_state.json`.
- Contexto: busca segura por arquivos e projeto ativo, com rótulos amigáveis para o usuário.
- Segurança: rejeição de segredos, confirmação para ações sensíveis, modo de revisão sem autoexecução e políticas de opt-in para plugins de terceiros.
- Wake word: `core/wake_word_gate.py` usa openWakeWord e aceita modelo configurável. O código vem desligado por padrão; a configuração local verificada liga `models/wake/jarvis.onnx`. A validação operacional por três dias ainda está pendente.
- Proatividade: `actions/proactive.py` implementa avisos locais por tempo de uso/horário, com ativação explícita; está desligada na configuração local atual.
- Removidos: boot/empacotamento portátil e criptografia de cofre; sincronização Supabase; briefing automático de startup; builders/widgets Qt legados; actions `weather_report`, `send_message`, `flight_finder` e `youtube_video`.
- UX operacional: a política de arquivos foi ajustada para confirmar apenas exclusão; ações não destrutivas não bloqueiam o fluxo, e a abertura de pasta informa corretamente se o Explorer foi realmente acionado.
- Mentoria: leitura diagnostica do projeto e patch sugerido, sem alteração automática.
- Plugins: `memory/config_manager.py` usa opt-in por padrão; plugins desconhecidos ficam desligados até habilitação via Plugin Manager, sem ativação silenciosa.

## Fronteiras ativas

- Canal de áudio com Gemini Live opera diretamente sem filtros de destinatário. `_turn_watchdog` reconecta quando há resposta pendente sem atividade por mais de 20 segundos; o relato histórico do bug H5 foi superado por essa implementação.
- O caminho principal de áudio é direto e não possui mordaças artificiais.
- As decisões de memória e contexto saem do fluxo principal de voz com confirmação e escopo controlado.
- A camada de produção atual é a linha segura: assistente pessoal + contexto + memória + diagnóstico guiado + plugins opt-in.
- O schema do Live session permanece imutável após `LiveConnectConfig`; liga/desliga de plugins afeta o próximo build do schema e não reconfigura a sessão ativa.

## Limite do escopo atual

- Não há autonomia destrutiva.
- Não há autoalteração irrestrita do código.
- Não há promessa de AGI ou SLA de provedores gratuitos.
- A evolução futura deve seguir blocos pequenos, com testes e aprovação explícita.

## Estrutura principal

- `main.py`: orquestração do fluxo principal, áudio, tools, visão e reconexão; delega loops e lifecycle da sessão a módulos dedicados. Está com 1.264 linhas no checkout verificado nesta atualização.
- `core/async_tool_runner.py`: execução limitada de tools, com wrappers de timeout.
- `core/background_tasks.py`: contador/lock de tasks em background e deduplicação/entrega de resultados no painel.
- `core/session_loops.py`: loops de monitoramento, reindexação contextual, proatividade e watchdog.
- `core/session_lifecycle.py`: saudação de boot e persistência do resumo da sessão.
- `core/platform_bootstrap.py`: inicialização de encoding de streams e patch de subprocesso no Windows; deve ser importado antes dos módulos de runtime.
- `core/transcript_utils.py`: limpeza e junção de transcrições, gate de fala e predicado temporal do watchdog.
- `core/live_model_resolver.py`: descoberta, validação e seleção/rotação dos modelos Live.
- `core/session_prompt.py`: composição da instrução de sistema para uma sessão Live.
- `core/reconnect_policy.py`: predicados de classificação de erros usados pela state machine mantida em `main.py`.
- `core/knowledge_vault.py`: notas Markdown no caminho configurado por `vault_path`, com WikiLinks automáticos, backlinks, resumo de boot e busca contextual.
- `core/memory_store.py`: fatos estruturados (`Identidade.md`, `Preferencias.md`, `Desejos.md`), notas de projetos/pessoas e log `Sessoes.md`, usando o vault.
- `core/runtime_state.py`: estado local volátil de monitores e tópicos, separado da memória pessoal.
- `core/context_index.py`: índice SQLite/FTS5 dos roots locais e dos arquivos Markdown do vault Obsidian.
- `core/tool_registry.py` e `core/tool_declarations.py`: registro/dispatch das tools principais, incluindo retornos estruturados e timeout opcional por tool.
- `core/llm_client.py`: chamadas de texto, limites por tipo de tarefa, métricas e fallback Groq → OpenRouter; Claude Sonnet 5 fica reservado para `deep_reasoning`.
- `core/wake_word_gate.py`: buffer de áudio e gate openWakeWord configurável.
- `actions/proactive.py` e `core/hw_sensors.py`: proatividade local opt-in e consultas leves de inatividade/tela cheia.
- `core/memory_policy.py`: política de gravação e classificação das lembranças.
- `core/context_resolver.py`: resolução local de arquivos e contexto do projeto.
- `actions/dev_agent.py`: revisão, mentoria e diagnóstico guiado sem aplicar alterações.
- `memory/config_manager.py`: estado de plugins persistido em `api_keys.json` e regra default deny para módulos desconhecidos.
- `ui.py` hospeda a UI WebEngine e os overlays ativos; os builders/widgets da UI Qt legada não fazem parte do runtime atual.

## Estado operacional

A linha de produto atual está estável e validada para uso real dentro do escopo seguro; as Fases 3, 4 e 5 foram concluídas sem alterar o caminho de áudio, e qualquer expansão futura deve ser guiada por feedback prático e não por promessa de autonomia ampla.

## Atualização — Fase 7 (estabilização e estado atual)

- `core/wake_word_gate.py`: gate local openWakeWord com buffer circular, janela de graça pós-resposta e modelo configurável. O default no código é `hey_jarvis` desligado; a configuração local verificada habilita `models/wake/jarvis.onnx`. Ainda falta concluir a validação de três dias em uso real.
- `core/llm_client.py`: `PAID_MODELS` (GLM-5.3-Flash, DeepSeek V4.1 Flash) e `PREMIUM_MODEL` (Claude Sonnet 5) adicionados. `FREE_MODELS`/`get_openrouter_model` removidos. Cadeia de fallback de texto: Groq → OpenRouter pago. Sonnet 5 só é chamado dentro de `_deep_reasoning_tool` (core/tool_registry.py), nunca no fallback automático.
- `core/knowledge_vault.py`: `build_boot_digest()` novo — alimenta `_build_config()` em main.py com as notas mais recentes/relevantes do vault no início de cada sessão.
- `core/tool_registry.py::dispatch_tool`: ferramentas síncronas agora rodam via `loop.run_in_executor`, nunca mais bloqueiam o loop de áudio.
- Removidos: `actions/game_updater.py`, `plugins/pushup_counter.py`.
- Canal de voz (Gemini Live) permanece isolado e intocado por essas mudanças — continua no tier gratuito do Google por decisão de custo; toda a camada de ferramentas/texto agora é majoritariamente paga (OpenRouter) com Groq grátis como primeira tentativa.