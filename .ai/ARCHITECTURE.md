# JARVIS MARK LI — ARQUITETURA ATUAL

## Estado real do sistema

- Interface: PyQt6 + QWebEngineView, com a GUI em thread principal e a sessão em thread asyncio separada.
- Voz: Gemini Live como canal principal, com fallback controlado e sem LLM local.
- Memória: política em 4 estados e gravação local em Obsidian/Markdown em `D:\Memoria_Jarvis`.
- Contexto: busca segura por arquivos e projeto ativo, com rótulos amigáveis para o usuário.
- Segurança: rejeição de segredos, confirmação para ações sensíveis, modo de revisão sem autoexecução e políticas de opt-in para plugins de terceiros.
- UX operacional: a política de arquivos foi ajustada para confirmar apenas exclusão; ações não destrutivas não bloqueiam o fluxo, e a abertura de pasta informa corretamente se o Explorer foi realmente acionado.
- Mentoria: leitura diagnostica do projeto e patch sugerido, sem alteração automática.
- Plugins: `memory/config_manager.py` usa opt-in por padrão; plugins desconhecidos ficam desligados até habilitação via Plugin Manager, sem ativação silenciosa.

## Fronteiras ativas

- Canal de áudio com Gemini Live opera diretamente sem intermediários ou filtros de destinatário descartados. Watchdog de reconexão (`_turn_watchdog`) tem bug conhecido (H5): o contador de tentativas nunca atinge o limite que forçaria reconexão completa.
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

- `main.py`: orquestração do fluxo principal e integração de memória/contexto; delega o runtime de tasks ao tracker.
- `core/background_tasks.py`: contador/lock de tasks em background e deduplicação/entrega de resultados no painel.
- `core/knowledge_vault.py`: notas Markdown com WikiLinks automáticos, backlinks e busca contextual ponderada.
- `core/context_index.py`: índice SQLite/FTS5 dos roots locais e dos arquivos Markdown do vault Obsidian.
- `core/memory_policy.py`: política de gravação e classificação das lembranças.
- `core/context_resolver.py`: resolução local de arquivos e contexto do projeto.
- `core/knowledge_vault.py`: leitura e escrita no vault local.
- `actions/dev_agent.py`: revisão, mentoria e diagnóstico guiado sem aplicar alterações.
- `memory/config_manager.py`: estado de plugins persistido em `api_keys.json` e regra default deny para módulos desconhecidos.

## Estado operacional

A linha de produto atual está estável e validada para uso real dentro do escopo seguro; as Fases 3, 4 e 5 foram concluídas sem alterar o caminho de áudio, e qualquer expansão futura deve ser guiada por feedback prático e não por promessa de autonomia ampla.

## Atualização — Fase 7 (estabilização)

- `core/wake_word_gate.py`: novo módulo, gate de wake word local (openWakeWord, "hey_jarvis"). Buffer circular de áudio + janela de graça pós-resposta. Plugado em main.py::_listen_audio (entrada) e _play_audio/_receive_audio (fechamento).
- `core/llm_client.py`: `PAID_MODELS` (GLM-5.3-Flash, DeepSeek V4.1 Flash) e `PREMIUM_MODEL` (Claude Sonnet 5) adicionados. `FREE_MODELS`/`get_openrouter_model` removidos. Cadeia de fallback de texto: Groq → OpenRouter pago. Sonnet 5 só é chamado dentro de `_deep_reasoning_tool` (core/tool_registry.py), nunca no fallback automático.
- `core/knowledge_vault.py`: `build_boot_digest()` novo — alimenta `_build_config()` em main.py com as notas mais recentes/relevantes do vault no início de cada sessão.
- `core/tool_registry.py::dispatch_tool`: ferramentas síncronas agora rodam via `loop.run_in_executor`, nunca mais bloqueiam o loop de áudio.
- Removidos: `actions/game_updater.py`, `plugins/pushup_counter.py`.
- Canal de voz (Gemini Live) permanece isolado e intocado por essas mudanças — continua no tier gratuito do Google por decisão de custo; toda a camada de ferramentas/texto agora é majoritariamente paga (OpenRouter) com Groq grátis como primeira tentativa.