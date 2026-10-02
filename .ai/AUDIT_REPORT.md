# Inventário técnico read-only

## Escopo e método

Auditoria estática do checkout atual, com buscas de referências no repositório,
checagem de entrypoints e leitura pontual dos trechos necessários. Não foram
abertos conteúdos de configuração que possam conter credenciais nem executados
testes ou fluxos da aplicação. “Alta confiança” significa que as referências
estáticas no repositório sustentam a conclusão; caminhos externos, execução
manual e configuração de produção continuam sujeitos a confirmação humana.

## Código em uso confirmado

- `main.py::main` / `main.py::JarvisLive` — **Alta**. É o runtime do JARVIS
  executado no modo atual. Integra sessão Gemini Live, áudio, tools,
  memória/contexto, métricas e tarefas. O caminho de boot portátil citado na
  auditoria original foi posteriormente confirmado pelo usuário como abandonado.
- `ui.py::JarvisUI` — **Alta**. Constrói um `QWebEngineView`, configura o canal
  Qt WebChannel e carrega `ui_web/index.html`; chamadas de estado/conteúdo são
  encaminhadas ao JavaScript da página.
- `ui_web/index.html` — **Alta**. A página carregada por `JarvisUI` renderiza a
  interface ativa; o relógio HTML atualiza a cada segundo.
- `actions/background_monitor.py::add_monitor/remove_monitor/list_monitors/check_all`
  — **Alta**. Importadas por `main.py`; `check_all` é agendada e a manutenção de
  tópicos usa a chave superior `monitors` em `long_term.json`.
- `actions/screen_processor.py::_capture_camera/_capture_screen` — **Alta**.
  Importadas e chamadas pelos caminhos especiais de captura em `main.py`.
- `actions/system_monitor.py::SystemMonitor/get_system_status` — **Alta**.
  `SystemMonitor` é instanciado pelo runtime; `get_system_status` é registrado
  no registry e declarado como tool.
- `actions/proactive.py::ProactiveEngine` — **Alta**. Instanciada por
  `JarvisLive`; o ciclo de proatividade usa o sensor de inatividade.
- `actions/browser_control.py`, `actions/code_helper.py`,
  `actions/computer_control.py`, `actions/computer_settings.py`,
  `actions/desktop.py`, `actions/dev_agent.py`, `actions/file_controller.py`,
  `actions/file_processor.py`, `actions/flight_finder.py`, `actions/open_app.py`,
  `actions/reminder.py`, `actions/send_message.py`, `actions/weather_report.py`,
  `actions/web_search.py` e `actions/youtube_video.py` — **Alta**. Seus handlers
  são importados por `core/tool_registry.py` e ligados por `@register_tool`;
  a invocação ocorre via `dispatch_tool`, não exige chamadas diretas em `main.py`.
- `core/tool_registry.py::register_tool/dispatch_tool/get_declarations` —
  **Alta**. O registry mantém handlers em `_REGISTRY`; `main.py` usa
  `dispatch_tool` e combina as declarações core com as declarações de plugins.
- `main.py::_execute_tool_impl` — **Alta**. Trata diretamente as tools especiais
  `screen_process`, `close_camera`, `find_context`, `save_memory`,
  `knowledge_note`, `shutdown_jarvis` e `sync_memory`; as demais seguem o registry.
- `core/plugin_loader.py::discover_plugins/PluginRegistry.run` — **Alta**.
  `main.py` chama discovery, gera declarações e despacha `run()` por registro.
  `plugins/reminder_verbal.py::run` é descoberto dinamicamente se habilitado;
  plugins novos ou desconhecidos ficam desabilitados por padrão segundo
  `memory/config_manager.py`. O arquivo `plugins/_template.py` é excluído por
  começar com `_`.
- Despacho por mapas — **Alta**. `actions/computer_settings.py::ACTION_MAP`,
  `actions/send_message.py::_PLATFORM_MAP`,
  `actions/open_app.py::_APP_ALIASES`,
  `actions/browser_control.py::_BROWSER_SPECS` e
  `actions/youtube_video.py::_ACTION_MAP` são consultados pelo fluxo das ações.
  Os valores dessas tabelas não devem ser considerados mortos por ausência de
  chamada nominal direta.
- `core/llm_client.py::call_llm_text/resilient_text_call/resilient_vision_call`
  — **Alta**. Chamadas usadas por tools e pelo caminho principal; fazem fallback
  entre providers e expõem limites/erros por tipo de tarefa.
- `core/context_index.py::rebuild_index/query` e
  `core/context_resolver.py::find_context_candidates/resolve_context` — **Alta**.
  `main.py` agenda indexação e resolução local usa o índice com fallback de busca.
- `core/knowledge_vault.py` e `core/memory_policy.py` — **Alta**. São conectados
  ao contexto e às tools de memória; o vault Markdown é separado dos registros
  estruturados de `memory/long_term.json`.
- `core/background_tasks.py::BackgroundTaskTracker`,
  `core/async_tool_runner.py::run_bounded/run_tool_bound`,
  `core/write_guard.py` e `core/runtime_config.py` — **Alta**. Importados pelo
  runtime para rastreamento/cancelamento, limites de tools, guard/auditoria e
  acesso à configuração.
- `core/paths.py::get_home_dir/get_base_dir/get_desktop_dir` — **Alta**. Chamados
  por UI, resolução contextual e diversas actions; `get_home_dir` consulta
  `is_portable`.
- `memory/memory_manager.py::load_memory/format_memory_for_prompt/
  save_session_summary/pop_last_session` — **Alta**. `main.py` lê memória
  estruturada, consome o último resumo e grava resumos de sessão; outros
  caminhos leem/gravam dados de monitor e ambiente.
- `memory/memory_manager.py::save_memory` — **Média**. Não é o caminho de gravação
  da tool `save_memory`; a função JSON é chamada pelo boot alternativo
  `core/boot_terminal.py` e internamente por `forget`, sem outro chamador ativo
  encontrado.
- `memory/config_manager.py` — **Alta**. Usado por loader de plugins e pelo
  runtime/configuração da UI.
- `core/sync_manager.py` — **Alta quanto à integração técnica**. A tool
  `sync_memory` chama o módulo para sincronizar arquivos cifrados e estado;
  o usuário confirmou posteriormente que a sincronização com Supabase foi
  totalmente descartada. Ver a classificação de decisão ao final.
- `actions/file_processor.py` — **Alta**. Invocado pela tool registrada; usa
  `pdfplumber` e fallback `PyPDF2` para PDF, além de `PIL` e `python-pptx` em
  outros formatos.
- `actions/computer_control.py::_screen_find` — **Alta**. Chama `_get_api_key`
  antes do fluxo de busca visual e usa `resilient_vision_call`; esta ocorrência
  distingue-se dos wrappers de chave sem chamadores descritos adiante.
- `core/hw_sensors.py::get_gpu_usage/get_cpu_temp` — **Alta**. Importadas por
  `actions/system_monitor.py`; `get_idle_seconds/is_foreground_fullscreen` são
  importadas por `main.py`.
- `tools/build_vault.py` e `core/crypto_vault.py::encrypt_archive` — **Alta
  quanto ao fluxo técnico**. O script manual gera o arquivo cifrado usado pelo
  boot portátil; o usuário confirmou que esse fluxo foi abandonado. A auditoria
  original também encontrou uso de `encrypt_bytes/decrypt_bytes` em
  `core/sync_manager.py`, sincronização que foi descartada.
- `tests/test_jarvis_core.py` — **Alta**. Único módulo de testes listado; inclui
  testes do runtime e testes de criptografia/índice/dispatch.
- `config/__init__.py`, `core/__init__.py`, `memory/__init__.py` e
  `plugins/__init__.py` — arquivos de pacote sem lógica relevante; agrupados,
  não tratados individualmente como achados de limpeza.

## Código não utilizado / morto

- `ui.py::JarvisUI._build_header/_build_left_panel/_build_right_panel/
  _build_content_panel/_build_footer` — **Alta**. Busca no workspace encontra
  definições, mas nenhuma chamada a esses builders. O construtor ativo monta a
  área com `QWebEngineView`; `_show_content` também chama JavaScript em vez do
  builder Qt.
- `ui.py::HudCanvas` — **Alta**. Nenhuma instanciação ou referência externa
  encontrada.
- `ui.py::MetricBar` — **Alta**. Só é instanciada dentro de `_build_left_panel`,
  que não tem chamador encontrado.
- `ui.py::LogWidget` e `ui.py::FileDropZone` — **Alta**. Só são instanciadas em
  `_build_right_panel`, que não tem chamador encontrado.
- `ui.py::_DropCanvas` — **Alta**. Instanciada apenas por `FileDropZone`, sem
  caminho de construção ativo encontrado.
- `actions/youtube_video.py::_get_api_key`,
  `actions/flight_finder.py::_get_api_key`,
  `actions/desktop.py::_get_api_key`,
  `actions/dev_agent.py::_get_api_key`,
  `actions/code_helper.py::_get_api_key`,
  `actions/file_processor.py::_get_api_key` e
  `actions/computer_settings.py::_get_api_key` — **Alta**. Em cada caso, a
  referência no repositório é a própria definição; os fluxos de LLM dessas
  actions usam o cliente resiliente compartilhado. `actions/computer_control.py`
  é exceção: seu `_get_api_key` é chamado por `_screen_find`.
- `memory/memory_manager.py::remember/forget/forget_memory/update_memory` —
  **Alta**. `remember` e `forget` não têm chamadores fora das próprias
  definições/alias; `update_memory` só é chamada por `remember`.
  A tool chamada `save_memory` em `main.py` grava via política/vault; não chama
  essas funções.
- `core/runtime_constants.py::LIVE_MODEL` e import correspondente em `main.py`
  — **Alta**. Só aparece na definição e no import; a seleção efetiva usa
  `LIVE_MODEL_FALLBACKS` e cache.
- Imports diretos em `main.py` de handlers também importados pelo registry —
  **Alta**. `file_processor`, `flight_finder`, `open_app`, `weather_action`,
  `send_message`, `reminder`, `computer_settings`, `youtube_video`,
  `desktop_control`, `browser_control`, `file_controller`, `code_helper`,
  `dev_agent`, `web_search_action`, `computer_control` e `get_system_status`
  aparecem somente nas linhas de import em `main.py`. Os handlers são usados
  através de `core/tool_registry.py`; os imports locais de `_capture_camera`,
  `_capture_screen`, `SystemMonitor`, `ProactiveEngine` e `monitor_check_all`
  tinham usos locais na auditoria.
- Imports em `main.py` de `add_monitor/remove_monitor/list_monitors` — **Alta**.
  Não são referenciados no corpo de `main.py`; as operações de monitoramento
  estão disponíveis pela tool/registry. Não foram encontrados testes que
  acessem esses atributos de `main`.
- `core/installer.py::install_for_config` — **Alta**. Nenhuma importação ou
  chamada encontrada. A instalação de dependências do agente de projeto tem
  implementação separada em `actions/dev_agent.py::_install_dependencies`.
- `core/paths.py::get_downloads_dir/get_documents_dir` — **Alta**. Nenhuma
  referência fora das definições encontrada; outros fluxos constroem caminhos
  a partir de `get_home_dir`.
- `core/crypto_vault.py::secure_wipe` — **Alta**. Nenhum chamador encontrado;
  o entrypoint portátil usa implementação própria em `boot_stage0.py`.
- `core/crypto_vault.py::decrypt_archive` — **Alta para ausência no runtime;
  média para remoção**. As únicas chamadas encontradas são testes; `boot_stage0.py`
  decifra o arquivo com função própria.
- `plugins/_template.py::run` — **Alta**. É template e o loader pula todo arquivo
  cujo nome começa por `_`; não é um plugin executável descoberto.

## Duplicação entre arquivos

- `actions/code_helper.py::_get_gemini` e `actions/dev_agent.py::_get_model` —
  **Alta**. Os dois criam uma classe interna com `generate_content`, constroem
  objeto de resposta com `.text` e chamam `resilient_text_call(...,
  task_type="code", raise_on_fail=True)`. Ambos os wrappers têm uso local.
- `actions/file_processor.py::_gemini_client` — **Alta**. Segue o mesmo padrão
  de adaptador `generate_content`/`.text`, mas não é duplicação exata dos outros:
  suporta texto e imagem, roteando imagem por `resilient_vision_call`.
- Helpers `_get_api_key` — **Alta**. Há implementações repetidas em oito actions
  (as sete citadas acima mais `computer_control`); a maioria não tem chamada,
  mas a cópia em `computer_control` é efetivamente invocada.
- `get_base_dir/_get_base_dir` — **Alta**. Implementações com o mesmo propósito
  (raiz do projeto ou diretório do executável congelado) aparecem em
  `main.py`, `core/paths.py`, `core/llm_client.py`,
  `memory/memory_manager.py`, `memory/config_manager.py`,
  `actions/code_helper.py`, `actions/dev_agent.py`, `actions/desktop.py`,
  `actions/computer_settings.py`, `actions/flight_finder.py` e
  `actions/youtube_video.py`. Algumas são chamadas para inicializar caminhos
  locais; outras coexistem com `core.paths`.
- Criptografia de arquivo compactado em `boot_stage0.py::_derive_key/
  _decrypt_archive/_secure_wipe` versus `core/crypto_vault.py` — **Alta**.
  Repetem AES-GCM, salt fixo e 600.000 iterações PBKDF2. O boot portátil está
  autocontido e o empacotador usa `core.crypto_vault.encrypt_archive`.
- `memory/long_term.json` e o vault Markdown — **Alta quanto à coexistência;
  média quanto à duplicação funcional**. `long_term.json` mantém campos
  estruturados e sessões; `core/knowledge_vault.py` mantém notas Markdown.
  `main.py` usa ambas as superfícies; não são duas implementações idênticas do
  mesmo armazenamento.
- Escritas nas categorias estruturadas de `memory/long_term.json` — **Alta**.
  Entre `identity/preferences/projects/relationships/wishes`, a escrita externa
  encontrada é `core/boot_terminal.py::_check_environment_change`, que atualiza
  `identity.last_known_host`; esse boot não é chamado pelo launcher principal.
  `main.py` lê campos de identidade e grava resumos em `sessions`, não nessas
  cinco categorias. `actions/background_monitor.py` grava `monitors` na raiz do
  JSON. `remember/forget/update_memory` poderiam alterar categorias se
  invocados, mas não têm chamadores ativos encontrados. A tool `save_memory` em
  `main.py` grava via política/vault, não em `long_term.json`.

## Funcionalidade abandonada / incompleta

- `core/paths.py::is_portable/get_home_dir` e `JARVIS_PORTABLE/JARVIS_HOME` —
  **Alta para a ligação no código; uso atual esclarecido pelo usuário**.
  `get_home_dir` e o helper de paths continuam usados por várias actions, mas
  a ramificação específica `JARVIS_PORTABLE/JARVIS_HOME` pertence ao fluxo
  portátil/pendrive, que o usuário confirmou abandonado. O helper geral de
  diretórios não é exclusivo do portátil.
- `ui.py::JarvisUI._tick_clock` — **Alta**. É chamado pelo construtor, mas o
  corpo é `pass`; o relógio visível é atualizado por `ui_web/index.html`.
- `actions/background_monitor.py::_save` versus `core/paths.py::get_monitor_position`
  — **Alta**. O primeiro persiste a configuração na chave superior `monitors`;
  o segundo lê `identity.monitors` de `long_term.json`. As duas leituras/
  gravações usam estruturas diferentes.
- `core/boot_terminal.py::run` — **Alta**. Tem bloco `__main__`, mas nenhuma
  importação/chamada no runtime foi encontrada; o usuário confirmou que o fluxo
  portátil/pendrive está abandonado.
- `tools/encrypt_keys.py` — **Alta**. Gera `config/api_keys.enc` para o boot
  alternativo de `core/boot_terminal.py`; o usuário confirmou que esse fluxo foi
  abandonado.
- `tools/wake_eval.py::cmd_record/cmd_eval` e `wake_samples/` — **Alta**. São
  ferramentas/dados de calibração manual, não invocados pelo runtime da aplicação.
  O runtime `core/wake_word_gate.py` depende opcionalmente de `openwakeword`;
  se o import/carregamento falha, o próprio gate repassa áudio em vez de bloqueá-lo.
- `core/installer.py` — **Alta para ausência de integração**. A docstring diz
  instalação automática, mas não há chamada em startup; além disso, parte da
  lista de dependências e os caminhos STT/TTS não correspondem a uma chamada
  encontrada no runtime.

## Arquivo obsoleto / candidato à remoção

- `ui.py` — **Alta** para o bloco Qt legado identificado acima; a classe principal
  continua ativa. A evidência só sustenta a ausência de construção dos builders
  e widgets citados, não a remoção do arquivo inteiro.
- `_INICIAR_JARVIS.bat`, `boot_stage0.py`, `project.enc`,
  `core/boot_terminal.py`, `tools/encrypt_keys.py` e `config/api_keys.enc` —
  **Alta, decisão confirmada pelo usuário**. São partes do fluxo portátil ou do
  boot alternativo de chave criptografada; ambos foram confirmados como
  abandonados. Ver os detalhes e limites de escopo na seção de decisões.
- `core/installer.py` — **Alta no uso interno do repositório**. Nenhum chamador;
  utilitário isolado com documentação de integração que não se confirma.
- `plugins/_template.py` — **Alta para ausência em runtime**, mas é um template
  intencionalmente excluído da descoberta; a busca não determina se deve ser
  mantido como material de desenvolvimento.

## Dependência (requirements.txt) sem uso confirmado

- `google-generativeai` — **Alta**. Não há import de `google.generativeai` nem
  `generativeai`; o código importa `google.genai` do pacote `google-genai`.
- `pypdf` — **Alta**. Não há import de `pypdf`; `actions/file_processor.py`
  importa `pdfplumber` e usa `PyPDF2` como alternativa.
- `screen-brightness-control` — **Alta**. Não há import ou referência ao módulo
  `screen_brightness_control`; buscas no workspace não localizaram uso.
- `httpx` e `beautifulsoup4` — **Alta**. Não há import de `httpx` ou `bs4` no
  runtime; os nomes aparecem apenas como strings em mapas de dependências de
  projetos manipulados pelo agente/instalador.
- `pdfplumber` e `PyPDF2` — **Alta**. Ambos têm import ativo em
  `actions/file_processor.py`; portanto, não estão no mesmo caso de `pypdf`.
- `PyQt6-WebEngine` — **Alta para ausência no manifesto; média para impacto de
  instalação**. `ui.py` importa `PyQt6.QtWebEngineWidgets.QWebEngineView`, mas
  `requirements.txt` não declara explicitamente o pacote WebEngine.
- `openwakeword` — **Alta para ausência no manifesto; média para disponibilidade
  efetiva**. Importado por `core/wake_word_gate.py` e `tools/wake_eval.py`, mas
  não declarado em `requirements.txt`; a funcionalidade de wake word depende
  dele em runtime.
- `pynvml` e `wmi` — **Alta para ausência no manifesto**. São imports opcionais
  em `core/hw_sensors.py`; as funções têm tratamento para indisponibilidade e
  fallback.
- As demais dependências listadas têm referências de import encontradas no
  runtime ou em ferramentas/testes: por exemplo, `sounddevice`/`google-genai`
  em `main.py`, Playwright em `actions/browser_control.py`, `pyautogui` em
  actions, e `cryptography` no fluxo de vault/sincronização. A ausência de uma
  referência textual para um pacote opcional não prova que seu uso externo seja
  impossível.

## Sistema experimental / parcial

- `core/wake_word_gate.py::WakeWordGate` e `tools/wake_eval.py` — **Alta**.
  Código funcional, configurável e com modelo local no repositório; a avaliação
  automatizada é ferramenta manual e a validação prolongada de uso não é
  executada pelo código. A disponibilidade do pacote `openwakeword` não é
  garantida pelo manifesto.
- `boot_stage0.py::run` — **Alta para o mecanismo; decisão confirmada de abandono**.
  Descriptografa `project.enc` em sessão temporária e executa o `main.py`
  extraído; o usuário confirmou que o portátil não é mais usado.
- `core/boot_terminal.py::run` — **Alta para o mecanismo; decisão confirmada de
  abandono**. Lê `config/api_keys.enc`, restaura `api_keys.json` e inicia
  `main.py`; não é selecionado pelo launcher rastreado.
- `core/crypto_vault.py::encrypt_file/decrypt_file/encrypt_archive/decrypt_archive`
  e `tools/encrypt_keys.py` — **Alta quanto ao vínculo técnico**. Dão suporte
  aos dois fluxos de boot criptografado agora confirmados como abandonados.
  `encrypt_bytes/decrypt_bytes` estavam ligados à sincronização com Supabase,
  também descartada pelo usuário.
- `core/context_index.py` — **Alta**. Índice SQLite/FTS5 local usado pelo
  resolver; não representa indexação semântica ou por embeddings.

## Dependência entre módulos (quem importa quem, acoplamentos relevantes)

- Entry points: o caminho portátil rastreado era `_INICIAR_JARVIS.bat` →
  `boot_stage0.py` → `project.enc` descriptografado em runtime → `main.py`;
  esse caminho foi confirmado pelo usuário como abandonado. `setup.py` e
  `readme.md` documentam execução direta de `main.py`, que é o caminho de
  runtime atual identificado nesta auditoria. `core/boot_terminal.py` não
  participa desse caminho.
- UI/runtime: `main.py` instancia `ui.JarvisUI`; a comunicação atravessa sinais
  Qt/WebChannel e chamadas JavaScript para `ui_web/index.html`.
- Tools core: `main.py` chama `core.tool_registry.dispatch_tool`; o registry
  importa os handlers de `actions/*`. As 30 entradas de
  `core/tool_declarations.py` se dividem em 23 tools registradas e sete
  tratadas diretamente por `main.py` (`screen_process`, `close_camera`,
  `shutdown_jarvis`, `find_context`, `save_memory`, `knowledge_note`,
  `sync_memory`). Não foi encontrada tool registrada sem declaração nem
  declaração sem um caminho correspondente. As declarações totais também
  servem à prevenção de colisão com plugins.
- Plugins: `main.py` → `core.plugin_loader.discover_plugins` → importação dinâmica
  por `spec_from_file_location`; `PluginRegistry.run` chama o `run()` do módulo
  obtido do registro `PLUGIN`.
- Texto/visão: actions → `core.llm_client`; `main.py` também usa o cliente para
  operações de texto. `actions/computer_control.py::_screen_find` mantém um
  caminho adicional de leitura da chave antes de usar o helper resiliente.
- Contexto/memória: `main.py` e `actions` → `core.context_resolver`,
  `core.context_index`, `core.memory_policy` e `core.knowledge_vault`;
  `memory.memory_manager` continua fornecendo estrutura JSON para identidade,
  configuração de monitores e resumos de sessão. `core.sync_manager` dependia
  dos armazenamentos para Supabase, sincronização que o usuário descartou.
- Segurança de escrita: `actions` e `main.py` → `core.write_guard`; o log fica
  em `memory/audit_log.jsonl`. `core.paths` também fornece os diretórios
  consumidos pelos controladores de arquivos e pelo resolver.
- Telemetria/assistência: `main.py` → `core.background_tasks`,
  `core.async_tool_runner`, `actions.system_monitor` e `actions.proactive`;
  `core.hw_sensors` fornece os sensores ao monitor e à proatividade.
- Arquivos de dados/runtime: `memory/long_term.json`, `memory/context_index.db`,
  logs, backups, `wake_samples/`, `models/wake/jarvis.onnx`, arquivos `.enc` e
  `knowledge/*.md` são dados/artefatos, não módulos mortos por falta de imports.
  A utilização do diretório `knowledge/` depende do caminho de vault em
  configuração externa, cujo valor não foi inspecionado.

## Candidatos a remoção de alta confiança

1. Builders e widgets Qt sem construção ativa: cinco métodos `_build_*`, mais
   `HudCanvas`, `MetricBar`, `LogWidget`, `FileDropZone` e `_DropCanvas`.
2. Definições sem chamador de `_get_api_key` em
   `youtube_video.py`, `flight_finder.py`, `desktop.py`, `dev_agent.py`,
   `code_helper.py`, `file_processor.py` e `computer_settings.py`.
3. `LIVE_MODEL` (constante e import), imports de handlers não usados em
   `main.py`, e `add_monitor/remove_monitor/list_monitors` importados ali.
4. `remember`, `forget`, `forget_memory` e `update_memory` em
   `memory/memory_manager.py`.
5. `core/installer.py::install_for_config`,
   `core/paths.py::get_downloads_dir/get_documents_dir` e
   `core/crypto_vault.py::secure_wipe` (considerando apenas referências internas
   do repositório).
6. Dependências sem uso confirmado: `google-generativeai`, `pypdf`,
   `screen-brightness-control`, `httpx` e `beautifulsoup4`.

## Precisam de confirmação manual do Paulo antes de remover

1. As dependências ausentes do manifesto (`PyQt6-WebEngine`, `openwakeword`,
   `pynvml`, `wmi`) e quais são instaladas fora de `requirements.txt`.
2. A posição e uso real dos dados em `knowledge/` e backups; a configuração
   externa que determina o vault não foi inspecionada.
3. O destino pretendido da chave `monitors` em `long_term.json`, pois o gravador
   e o leitor de posição de monitor usam caminhos diferentes.

## DECISÕES CONFIRMADAS PELO USUÁRIO

As classificações abaixo registram decisões de uso posteriores à auditoria
técnica. “Candidato à remoção” não significa que arquivos foram apagados: esta
atualização não modifica código nem configuração.

### MANTER

- `actions/reminder.py` — o usuário confirmou que usa essa funcionalidade.
  Mantêm-se os lembretes e suas notificações locais do sistema operacional; isso
  não é o fluxo de mensagens por plataformas nem uma notificação para celular.

### NÃO UTILIZADO — CANDIDATO À REMOÇÃO

- `actions/weather_report.py` — o usuário confirmou que não usa a funcionalidade.
  Continua tecnicamente registrada no `core/tool_registry.py`.
- `actions/send_message.py` — o usuário confirmou que não usa a funcionalidade.
  A action, a tool `send_message` em `core/tool_declarations.py`, seu wrapper no
  registry e os handlers de WhatsApp, Telegram, Instagram, Signal, Discord e
  Messenger são superfícies relacionadas e candidatas à remoção.
- Funcionalidades de celular/mensagens/notificações por plataformas — o usuário
  confirmou que não usa celular neste projeto. O envio por plataformas acima é
  candidato à remoção; o tratamento/autopreenchimento do campo `phone` em
  `actions/computer_control.py` é uma funcionalidade específica relacionada,
  mas não torna toda a action candidata. Aliases de apps em `open_app.py` são
  parte de um abridor genérico e não foram classificados como exclusivos de
  celular.
- `actions/flight_finder.py` — o usuário confirmou que não usa a funcionalidade;
  continua tecnicamente registrada no registry.
- `actions/youtube_video.py` — o usuário confirmou que não usa a funcionalidade;
  continua tecnicamente registrada no registry.
- O briefing/noticiário automático no startup foi removido no Bloco 3. A
  saudação de boot é um caminho separado; a busca manual da tool `web_search`
  e o monitoramento de tópicos permanecem.
- Sincronização de memória com Supabase — descartada totalmente; a memória
  deverá permanecer local no PC. São candidatos à remoção o fluxo
  `core/sync_manager.py`, a tool/declaração `sync_memory`, o dispatch em
  `main.py`, chaves específicas de configuração (`supabase_url`,
  `supabase_service_key`, `supabase_bucket`, `sync_password`), o estado
  `memory/sync_state.json` e `core.crypto_vault.encrypt_bytes/decrypt_bytes`,
  cujo único chamador de produção identificado era o sincronizador. As funções
  criptográficas não foram removidas; os testes existentes também as referenciam.
  `core/memory_policy.py` contém uma classificação de conteúdo com palavras como
  “supabase”/“banco”, mas não implementa transporte ou sincronização e não foi
  confirmado como infraestrutura exclusiva do sync.

### LEGADO ABANDONADO — PORTÁTIL

- `_INICIAR_JARVIS.bat`, `boot_stage0.py`, `project.enc`,
  `core/boot_terminal.py`, `tools/encrypt_keys.py` e `config/api_keys.enc` —
  confirmados pelo usuário como não usados. Incluem o launcher, extração do
  arquivo do projeto e o caminho alternativo de descriptografia da configuração.
- `tools/build_vault.py` e as rotinas `encrypt_archive/decrypt_archive` e
  `encrypt_file/decrypt_file` em `core/crypto_vault.py` — componentes
  específicos dos fluxos portáteis/alternativos confirmados como abandonados.
- A ramificação `JARVIS_PORTABLE/JARVIS_HOME` dentro de `core/paths.py` —
  infraestrutura específica do modo portátil. `core/paths.py` e seus helpers
  gerais continuam usados pelo runtime; somente essa ramificação está
  classificada como legado.
- O módulo `core/crypto_vault.py` também continha os helpers de bytes ligados
  à sincronização Supabase, agora descartada. A decisão classifica essas rotinas
  e os usos de produção correspondentes como candidatos; não afirma que o
  arquivo inteiro foi removido ou que seus testes deixaram de existir.
