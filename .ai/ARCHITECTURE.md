# JARVIS — Arquitetura do checkout atual

## Inicialização e runtime

1. `main.py` inicializa o runtime, carrega configuração/prompt e prepara a
   sessão Live.
2. `ui.py` cria a janela PyQt6 e carrega `ui_web/index.html` no
   `QWebEngineView`; a comunicação entre Python e a página usa Qt/WebChannel.
3. `main()` mantém a interface na thread principal e executa `JarvisLive` em
   thread própria com `asyncio`.
4. `JarvisLive` conecta Gemini Live, coordena captura/envio do microfone,
   recepção/reprodução do áudio, transcrições e tools. Rotinas de watchdog,
   monitoramento, reindexação e proatividade são iniciadas pelo runtime.
5. Tools declaradas são despachadas por `core/tool_registry.py`, exceto
   `screen_process` e `close_camera`, que têm caminhos específicos no runtime.

## Módulos e responsabilidades

- `main.py` — composição da sessão Live, ciclo de áudio, câmera/tela,
  reconexão, encaminhamento de tools, integração com UI e serviços.
- `ui.py`, `ui_web/index.html` — janela Qt, WebEngine/WebChannel, interface e
  apresentação de estados/conteúdo.
- `core/platform_bootstrap.py`, `core/runtime_config.py`,
  `core/runtime_constants.py`, `core/paths.py` — inicialização específica da
  plataforma, configuração, constantes e caminhos.
- `core/live_model_resolver.py`, `core/session_prompt.py`,
  `core/reconnect_policy.py`, `core/transcript_utils.py` — seleção do modelo
  Live, composição de instrução, classificação de falhas e helpers de
  transcrição/watchdog.
- `core/tool_declarations.py`, `core/tool_registry.py`,
  `core/async_tool_runner.py` — schema e dispatch das tools, execução
  assíncrona e limites de espera.
- `core/session_loops.py`, `core/session_lifecycle.py`,
  `core/background_tasks.py` — loops de runtime, boot/fechamento de sessão e
  acompanhamento/cancelamento de tarefas.
- `core/llm_client.py` — chamadas de texto/visão, roteamento de providers,
  fallback, limites, métricas e circuit breaker.
- `actions/` — implementações de controle do computador, navegador, arquivos,
  busca web, processamento de arquivos, lembretes, monitoramento,
  proatividade e agente de desenvolvimento.
- `core/knowledge_vault.py`, `core/memory_store.py`,
  `core/memory_policy.py` — armazenamento Markdown, fatos/sessões e decisão de
  gravação de memória.
- `core/context_index.py`, `core/context_resolver.py` — índice local e
  resolução de arquivo/projeto.
- `core/runtime_state.py` — estado operacional local, separado das notas de
  memória.
- `core/write_guard.py` — confirmação, auditoria e backup nos fluxos que usam
  o guard.
- `core/plugin_loader.py`, `memory/config_manager.py`, `plugins/` — descoberta,
  registro e configuração de plugins.
- `core/wake_word_gate.py`, `core/hw_sensors.py` — gate local de áudio e
  sensores opcionais usados por wake word/proatividade/monitoramento.

## Contratos de tools e plugins

`core/tool_declarations.py` contém 25 declarações. 23 handlers são registrados
em `core/tool_registry.py`; `screen_process` e `close_camera` são tratados por
caminhos próprios em `main.py`. O dispatch preserva respostas estruturadas e
executa handlers síncronos fora do loop de áudio; um timeout limita a espera,
mas não garante que uma thread de trabalho já iniciada seja encerrada.

Os plugins são descobertos dinamicamente em `plugins/`. O módulo incluído
`plugins/reminder_verbal.py` é um plugin disponível no código; se está ativo
depende da configuração local, que não foi verificada. O loader ignora arquivos
de template/nomes excluídos e a configuração padrão é opt-in para plugins
desconhecidos.

## Dados e integrações

- Vault local: arquivos Markdown, incluindo fatos estruturados, sessões e notas
  de projetos/pessoas; localização configurável por `vault_path`.
- Busca: SQLite com FTS5 para arquivos/Markdown e fallback de varredura local;
  não é banco remoto nem busca semântica por embeddings.
- Estado local: `memory/runtime_state.json`, índice `memory/context_index.db`,
  auditoria `memory/audit_log.jsonl` e backups em `memory/backups`.
- Configuração/credenciais: `config/api_keys.json`, fora do escopo de inspeção
  desta revisão por poder conter segredos.
- Providers: Gemini Live para a sessão multimodal; o cliente compartilhado
  implementa rotas resilientes Groq → OpenRouter para texto/visão e também
  mantém suporte a providers configuráveis compatíveis com OpenAI, como
  Ollama. O provider efetivamente selecionado depende da configuração local.
- A busca web usa fontes externas; browser, captura de tela/câmera e automação
  interagem com recursos do sistema e dependem do ambiente.

## Limites arquiteturais observados

- `main.py` continua sendo um orquestrador relevante, embora vários helpers e
  serviços tenham módulos próprios.
- O timeout do dispatch limita quanto o runtime aguarda; não cancela
  necessariamente trabalho síncrono já iniciado em executor.
- Índice FTS5/backlinks não oferece recuperação semântica por embeddings.
- Wake word depende de `openwakeword`, que não está listado em
  `requirements.txt`; a falha de carregamento mantém o gate de áudio aberto.
- A UI importa Qt WebEngine sem declarar `PyQt6-WebEngine` explicitamente em
  `requirements.txt`.
- Serviços remotos, credenciais e comportamento de dispositivos reais não são
  validados pela arquitetura estática nem pela suíte unitária.
