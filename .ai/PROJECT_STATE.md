# JARVIS — Estado atual do projeto

## Resumo

Aplicação assistente desktop escrita em Python, voltada ao Windows. O runtime
principal está em `main.py`; a interface combina PyQt6, Qt WebEngine,
WebChannel e a página `ui_web/index.html`. A sessão de voz usa Gemini Live e
`sounddevice`; ferramentas, memória, contexto, estado de tarefas e políticas de
confirmação são implementados em módulos separados.

Este documento descreve o que o código rastreado implementa. Não representa
uma certificação de disponibilidade de serviços externos nem a configuração
privada instalada no computador.

## Implementado no código

- **Voz e sessão:** conexão Gemini Live, envio de áudio PCM, recepção e
  reprodução de áudio, transcrições, VAD do servidor, tratamento de ferramentas,
  reconexão e watchdog para respostas pendentes.
- **Interface:** janela Qt com conteúdo WebEngine, ponte Qt/WebChannel e
  interface HTML/WebGL. A página é carregada por `ui.py`.
- **Tools:** 25 tools declaradas. 23 são registradas em
  `core/tool_registry.py`; `screen_process` e `close_camera` têm tratamento
  específico no runtime. Cobrem busca web, controle do computador e navegador,
  arquivos, lembretes, monitoramento, contexto local, memória, raciocínio,
  tarefas em segundo plano e configurações do assistente.
- **Agente de desenvolvimento:** `dev_agent` oferece revisão/mentoria e
  operações de projeto. O próprio código inclui caminhos de escrita de arquivos
  e instalação de dependências; portanto, não é correto caracterizar todo o
  módulo como estritamente somente leitura. A autorização e o efeito dependem
  da ação solicitada.
- **Texto e visão:** `core/llm_client.py` inclui chamadas resilientes com
  roteamento Groq → OpenRouter para texto e visão, circuit breaker e métricas.
  Há suporte adicional a provedores configuráveis compatíveis com APIs OpenAI,
  inclusive Ollama; a configuração privada efetiva não foi inspecionada.
  `deep_reasoning` usa um modelo premium definido no código, separado do
  fallback resiliente.
- **Memória:** política com estados `automatic`, `suggested`, `explicit` e
  `ignore`; notas Markdown no vault configurado por `vault_path`, fatos
  estruturados, notas de projetos/pessoas e resumos de sessão.
- **Contexto local:** resolução de arquivos/projetos a partir de raízes locais,
  índice SQLite/FTS5 e fallback de busca. O índice lexical e os backlinks não
  são busca por embeddings.
- **Segurança de ações:** `core/write_guard.py` centraliza confirmação local
  para ações sensíveis e grava auditoria; há backup para escritas cobertas pelo
  helper. Os testes verificam, entre outros casos, exclusão de arquivo e ações
  de energia.
- **Plugins:** descoberta dinâmica dos módulos em `plugins/`; plugins
  desconhecidos ficam desativados por padrão. A configuração efetiva de plugins
  não foi inspecionada.
- **Wake word e proatividade:** o código implementa gate openWakeWord e regras
  locais de proatividade. Ambos vêm desativados por padrão no código e podem
  ser configurados; a operação real dessas opções não foi confirmada nesta
  revisão.

## Persistência e configuração

- A configuração local é lida de `config/api_keys.json`; esse arquivo pode
  conter credenciais e não foi aberto. Não inferir dela chaves disponíveis,
  provider ativo, caminho do vault ou opções habilitadas.
- O vault Markdown é escolhido por configuração e tem fallback definido pelo
  código. O caminho efetivo nesta máquina não foi verificado.
- O estado de runtime de monitores/tópicos usa `memory/runtime_state.json`.
- A busca contextual mantém um índice SQLite/FTS5; a auditoria de ações é
  gravada em `memory/audit_log.jsonl`; backups são criados sob `memory/backups`
  pelos fluxos que usam o guard.
- Os dados acima são dados locais de runtime, não uma garantia de que existam
  no checkout ou estejam versionados. Não há integração Supabase no runtime
  rastreado.

## Parcial, opcional ou dependente de ambiente

- Gemini Live, Groq e OpenRouter exigem conectividade, credenciais válidas,
  cotas e disponibilidade dos serviços. Os testes não verificam essas
  condições.
- O gate de wake word depende do pacote opcional `openwakeword`, ausente de
  `requirements.txt`. Se o modelo ou o pacote não puder ser carregado, o código
  registra a falha e deixa o áudio passar; isso preserva o fluxo de áudio, mas
  não fornece detecção de wake word.
- `PyQt6.QtWebEngineWidgets` é importado pela interface, mas
  `requirements.txt` não declara `PyQt6-WebEngine` separadamente.
- Sensores de hardware e recursos de automação dependem da plataforma e de
  pacotes opcionais. A cobertura automatizada inclui o comportamento quando
  sensores não estão disponíveis, não todos os dispositivos reais.
- Não há evidência nesta revisão de validação operacional prolongada do wake
  word, da qualidade da transcrição em uso real, da disponibilidade atual dos
  modelos remotos ou de todos os fluxos de áudio/câmera.

## Verificação automatizada

No ambiente Python 3.11 usado nesta revisão, `python -m pytest tests/ -q`
concluiu com **151 testes passando**. Isso valida os casos automatizados do
checkout; não equivale a teste manual de hardware, credenciais, serviços
remotos ou interface em uso prolongado.
