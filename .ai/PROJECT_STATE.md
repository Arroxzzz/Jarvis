# JARVIS MARK LI — ESTADO ATUAL DO PROJETO

## Estado validado

- Aplicação desktop Python em produção, com `PyQt6` + `QWebEngineView`.
- `main.py` mantém `JarvisLive` em thread própria com `asyncio`; a UI Qt fica na thread principal.
- Gemini Live é o caminho primário de voz, com PCM via `sounddevice`, transcrições e VAD automático.
- A sessão Live usa `thinking_budget=0` e `include_thoughts=False` para reduzir latência; o VAD usa sensibilidade alta, buffer de 300 ms e silêncio de 700 ms.
- O watchdog atual reconecta quando uma resposta pendente excede 20 segundos; o antigo achado H5 sobre contador que nunca alcançava o limite não descreve mais o código.
- A UI WebGL foi validada: restauração após minimizar corrigida, telemetria removida e painel de pesquisas separado do log.
- Sinais Qt continuam obrigatórios para chamadas ao `QWebEngineView`.
- O microfone foi diagnosticado e restaurado; o VAD foi ajustado.
- `deep_reasoning` foi restringido para não ser usado em contas, perguntas simples, resumos básicos, traduções ou pesquisas.
- O fluxo de visão possui timeout de 30 segundos e reconexão controlada quando a resposta multimodal não chega.
- Instrumentação de latência não sensível iniciada: turnos, primeiro áudio recebido/reproduzido,
  conclusão, duração de tools e duração de providers são emitidos como eventos `[METRIC]`.
- `core/llm_client.py` mede chamadas remotas Groq/OpenRouter sem registrar conteúdo.
- Comandos de texto agora iniciam eventos `[METRIC]` próprios; o caminho sem microfone participa do baseline.
- Validação atual do checkout: `python -m pytest tests/ -v` — 129 testes passaram em 5,20 s.
- `core/llm_client.py` agora registra `Retry-After`/rate-limit, bloqueia provider em circuit breaker e faz fallback Groq→OpenRouter de forma controlada.
- O loader de plugins foi ajustado para opt-in por padrão: plugins novos descobertos em `/plugins` nascem desligados até ativação explícita no Plugin Manager; isso evita que código de terceiro seja ativado por omissão.
- O log de boot em `main.py` agora conta plugins ativos e desligados, sem anunciar módulos indisponíveis como “carregados”.
- A camada de arquivos foi ajustada para a regra de produto: somente exclusão exige confirmação; criação, movimentação e abertura de pasta não bloqueiam o fluxo normal, e `open_folder` agora informa o resultado real do Explorer em vez de afirmar sucesso falso.
- A confirmação e a auditoria de ações estão centralizadas em `core/write_guard.py`; os fluxos de arquivo e configurações usam o guard sem alterar o áudio ou a sessão Live.
- O runtime de tarefas em background foi extraído para `core/background_tasks.py`; `JarvisLive` usa `BackgroundTaskTracker` para contador, lock, deduplicação e entrega de resultados ao painel.
- O vault Obsidian agora cria WikiLinks automáticos por regex, oferece backlinks e participa do índice SQLite de contexto; a relevância considera a quantidade de backlinks.
- O wake word é configurável e opt-in por padrão no código; na configuração local atual está habilitado com um modelo ONNX próprio em `models/wake/jarvis.onnx`. A validação de três dias de uso real continua pendente.
- A proatividade local existe com regras de tempo de uso/horário, mas está desabilitada na configuração local atual.
- A criptografia do pacote portátil e a sincronização Supabase foram removidas; `core/crypto_vault.py` não existe mais.
- `main.py` tem 1.755 linhas no checkout atual. As contagens de linhas abaixo são registros históricos de versões anteriores.
- Removidos do runtime: boot/empacotamento portátil, sincronização Supabase, briefing automático, builders/widgets Qt legados, `core/crypto_vault.py` e as actions `weather_report`, `send_message`, `flight_finder` e `youtube_video`. A dependência `youtube-transcript-api` também foi removida.
- `memory/context_index.db` e `memory/audit_log.jsonl` são dados locais e não são versionados.
- `core/memory_store.py` usa o vault Markdown para fatos (`Identidade.md`, `Preferencias.md`, `Desejos.md`), sessões (`Sessoes.md`) e notas organizadas em `Projetos/`, `Pessoas/` e `Notas/`. `core/runtime_state.py` guarda posições de monitores e tópicos monitorados em `memory/runtime_state.json`. Os dados migrados de `memory/long_term.json` foram verificados; o arquivo e `memory/memory_manager.py` foram removidos.

## Problemas ainda conhecidos

- APIs gratuitas não oferecem latência zero, SLA ou disponibilidade constante.
- A visão depende da capacidade e disponibilidade do modelo Live; o timeout evita congelamento, mas não torna a análise instantânea.
- O áudio pode ficar picotado quando a API deixa de entregar chunks.
- O histórico da UI é limpo após reconexão.
- Há avisos não fatais de DPI do Qt e AFC do SDK Gemini.
- Autenticação diária por senha/passphrase foi cancelada por decisão do Senhor Paulo.
- Kill switch local implementado: `Ctrl+Shift+F12` ou menu da bandeja encerra o processo imediatamente, independente da Gemini.
- Defesa anti-prompt-injection adicionada ao prompt-base; conteúdo externo é tratado como dado não confiável.
- `main.py` concentra sessão Live, áudio, tools, visão, reconexão, memória e watchdog; o estado de tasks e painel fica em `core/background_tasks.py`.
- O tamanho atual da orchestrator não é um problema por si só, mas é um sinal de acoplamento; a estratégia atual é decompor em blocos pequenos e testados sem mexer em áudio ou em lógica crítica.
- Meta de manutenção: manter a orquestração principal em faixa de 600-900 linhas, e mover helpers de áudio, visão, tools e monitoramento para módulos específicos conforme a decomposição continuar.
### Marcos históricos de refatoração

As contagens abaixo são da época, não representam o tamanho atual de `main.py`.

- A rodada inicial de refatoração controlada foi concluída com `main.py` em 2.433 linhas; o lifecycle ficou mais organizado, mas a meta de 600-900 linhas ainda exige extrações posteriores.
- A fase modular posterior começou com `core/async_tool_runner.py`, que concentra os dois wrappers de timeout de tools; naquele marco `main.py` tinha 2.417 linhas e a suíte dessa etapa tinha 30 testes.
- O bloco estático `TOOL_DECLARATIONS` foi extraído integralmente para `core/tool_declarations.py`; as 27 tools foram preservadas na mesma ordem. `main.py` ficou com 1.883 linhas e o novo módulo com 535 linhas. Áudio, UI e conexão Gemini não foram alterados.
- As constantes puras de runtime foram extraídas para `core/runtime_constants.py`: timezone, fallbacks Live, cache e parâmetros de áudio. Naquele marco `main.py` tinha 1.875 linhas e a suíte da etapa tinha 75 testes. Caminhos e leitura de configuração continuaram no `main.py` por participarem do boot.
- O I/O de configuração foi extraído para `core/runtime_config.py`, mantendo wrappers compatíveis no `main.py`; API key, prompt fallback, leitura JSON e escrita atômica do cache foram cobertos por testes. Naquele marco `main.py` tinha 1.860 linhas e a suíte tinha 75 testes.
- Na etapa inicial da Fase 2, `core/knowledge_vault.py` usava `D:\MEMORIA_JARVIS` como raiz e buscava `.md` recursivamente; o caminho passou depois a ser configurável por `vault_path`. Naquela etapa, a leitura encontrou `Memoria_Jarvis/Bem-vindo` e a suíte tinha 75 testes.
- A baseline formal ainda é uma amostra controlada de 6 turnos, não uma promessa estatística de 30-50 turnos; nenhuma troca de provider, buffer ou timeout de voz foi feita com base em especulação.
- Métricas atualmente são emitidas no terminal, não persistidas nem agregadas; a coleta real de 30-50 turnos ainda está pendente.
- Baseline atual validado: 6 turnos reais coletados no terminal, com amostra variada (web_search, análise de código, visão e interrupção).
  - `first_audio_received`: p50 = 2,085 ms, p95 = 2,687 ms, máximo = 2,687 ms (n=6).
  - `first_audio_played`: p50 = 2,085 ms, p95 = 2,687 ms, máximo = 2,687 ms (n=6).
  - `turn_complete`: p50 = 8,250 ms, p95 = 13,937 ms, máximo = 13,937 ms (n=6).
- Tools observadas na amostra: `web_search` 0 ms, `screen_process` 203 ms e `provider_end` com Groq em 735-969 ms; a resposta do áudio principal está em faixa excelente, enquanto o maior custo observado está em turnos com análise de código e interrupção.
- O canal principal de voz está validado como saudável na amostra atual; casos mais longos continuam sendo o eixo prioritário para observação, mas sem otimização prematura antes da próxima coleta controlada.

## Direção do produto

JARVIS deve ser um assistente pessoal de voz exclusivo do Senhor Paulo, inspirado
na experiência do JARVIS do Homem de Ferro, mas limitado ao que pode ser validado
com segurança e dentro da infraestrutura gratuita. Ele deve combinar:

- diálogo de voz natural, contínuo e contextual;
- mentoria de desenvolvimento full stack;
- assistência pessoal e consciência operacional do computador;
- memória de longo prazo local, controlada e pesquisável;
- resolução de referências ambíguas por contexto, recência e evidência local;
- automação segura, observável e reversível sempre que possível;
- capacidade futura de diagnosticar o próprio projeto e propor correções, sem
  permitir autoalteração irrestrita nesta fase.

O objetivo de produto é uma experiência de assistente contextual avançado, não a
promessa literal de AGI. A GPU local permanece livre para jogos; nenhum LLM local
deve ser introduzido.

### Memória de longo prazo

Obsidian com arquivos Markdown locais é a direção preferida para a memória pessoal:
os dados permanecem no SSD, são legíveis, versionáveis e não exigem banco remoto.
O JARVIS deve tratar o vault como fonte de memória do usuário, com:

- indexação incremental de arquivos `.md`;
- busca por termos, sinônimos, datas, nomes e recência;
- metadados e links entre notas;
- confirmação da fonte antes de afirmar uma lembrança;
- escrita controlada, com registro do que foi adicionado ou alterado;
- exclusão opcional; não há sincronização em nuvem no runtime atual.

Busca textual e indexação local não equivalem a introduzir um LLM local. Embeddings
ou outro índice semântico só devem ser considerados depois de medir custo, memória
e benefício real.

### Política de gravação da memória

O JARVIS terá três modos complementares:

- **Memória automática:** registra fatos persistentes e marcos claros de projetos,
  como objetivo, stack, decisões e próximos passos, sem salvar cada frase.
- **Memória sugerida:** detecta algo potencialmente importante e pergunta ao Senhor
  antes de gravar.
- **Memória explícita:** grava imediatamente quando o Senhor disser para lembrar,
  anotar, salvar ou criar uma nota.

Conversas casuais, transcrições completas, segredos e dados temporários não devem
ser gravados automaticamente. A política deve manter origem, data, projeto e nível
de confiança para cada registro.

### Consciência contextual do computador

O JARVIS deve resolver referências como "o PDF que baixei agora" ou "o código na
área de trabalho" combinando diretório conhecido, tempo de modificação, extensão,
nome aproximado, tipo de conteúdo e confirmação quando houver mais de um candidato.
Ele não deve exigir nome exato nem escolher silenciosamente um arquivo ambíguo.

O contexto do PC deve ser obtido sob demanda ou por eventos leves. Monitoramento
contínuo de tela, microfone e processos não é o padrão, pois aumenta custo, ruído e
risco de privacidade.

### Autonomia e segurança

O JARVIS pode detectar sinais de risco, registrar evidências, sugerir contenção e
executar ações autorizadas. Remoção de malware, encerramento de processos, alteração
de rede e quarentena precisam de níveis de confiança, allowlist, log e reversão ou
confirmação local quando a ação for irreversível. Nunca apagar ou bloquear algo só
porque um modelo classificou o item como malicioso.

Gatilhos sonoros devem ser tratados como uma camada local e barata de wake/intent:
palma ou estalo podem acordar uma escuta curta, mas não devem executar ações
destrutivas. O custo deve ser validado com a aplicação minimizada e durante jogos.

## Decisão cloud provisória

1. Gemini Live para diálogo de voz e multimodalidade.
2. Groq para texto rápido quando houver chave e cota.
3. OpenRouter pago (GLM-5.3-Flash/DeepSeek V4.1 Flash) como fallback de texto após Groq; Claude Sonnet 5 permanece restrito a `deep_reasoning`.
4. A integração Supabase foi removida; não há sincronização em nuvem no runtime atual.
5. Cloudflare Workers Free somente para rate limit, webhook e proxy curto; não para a sessão de áudio Live.

Free tier não significa SLA, disponibilidade contínua ou latência constante.

## Estado final da linha de produto atual

- A base do JARVIS está funcional e segura dentro do escopo validado.
- O caminho principal de voz continua intacto e o loop de áudio não foi alterado por estas camadas.
- A memória local foi integrada com política de decisão em quatro estados: automatic, suggested, explicit e ignore.
- O contexto local do computador e do projeto foi resolvido com busca segura, sem expor caminhos absolutos ao usuário.
- O `dev_agent` atua em revisão e mentoria guiada, sem autoalteração irrestrita.
- A suíte atual tem 129 testes passando; os registros de 78 testes nas fases abaixo são resultados históricos daquela etapa.
- O modelo de plugins foi fechado em opt-in: qualquer plugin desconhecido ou de terceiro nasce desligado até habilitação explícita, evitando ativação silenciosa por descoberta automática.
- A experiência de uso do assistente foi refinada para reduzir ruído de confirmação: ações não destrutivas seguem fluxo direto e só exclusão exige consentimento local.
- A Fase 4 foi concluída com `BackgroundTaskTracker`; a última validação de então registrou 78 testes passando.
- A Fase 5 foi concluída com WikiLinks, backlinks e indexação do vault; a última validação de então registrou 78 testes passando.

## Roadmap de refatoração aprovado

O conjunto de trabalho foi reestruturado em 5 fases, com segurança de linha de produção e sem mexer no loop principal de áudio ou no contrato atual do assistente:

1. Fase 0 — Rede de Segurança: baseline, tag, testes verdes e registro manual dos 7 fluxos.
2. Fase 1 — Tool Registry: centralização das ferramentas em registry e redução do `if name == ...` do `main.py`.
3. Fase 2 — Context Index (SQLite): busca contextual via FTS5 com fallback incremental e background job.
4. Fase 3 — Sinal Verde (Write Guard): guard central para ações destrutivas e auditoria em `memory/audit_log.jsonl`.
5. Fase 4 — Limpeza do Task Runtime: extração dos task trackers e cache de painel para classe dedicada.
6. Fase 5 — Obsidian Vivo (WikiLinks): `[[WikiLink]]` automáticos, backlinks e indexação do vault em contexto.

A ordem foi definida para preservar a linha produtiva atual e reduzir risco antes do refactor estrutural. O objetivo é controlar complexidade sem quebrar o funcionamento do Jarvis em uso real.

## Encerramento da fase atual

A linha de produto atual está pronta para uso seguro no ambiente do Senhor. O próximo passo lógico é operação real e refinamento do comportamento, não expansão de escopo para autonomia ampla ou novas promessas de AGI.

## Sessão de estabilização (Fase 7)

O JARVIS passou por uma rodada extensa de debug guiado por testes reais de voz, não revisão de código a frio. Quinze problemas reais foram encontrados e corrigidos (lista completa em CURRENT_TASK.md, Fase 7). O padrão de causa raiz que se repetiu: bugs de timing/threading no pipeline de áudio (watchdog, dispatch_tool, wake gate) e chamadas de LLM sem proteção de fallback (dev_agent, screen_find, modelo Groq morto) — nenhum dos problemas era a "API do Google sendo lenta" como se suspeitava inicialmente; a maior parte era lógica própria do projeto.

Decisão de custo consolidada: o canal de voz (Gemini Live) fica no tier gratuito do Google — o mínimo de pagamento (R$150 no Brasil, tanto AI Studio quanto Google Cloud) está acima do orçamento disponível. Todo o resto do sistema (busca, código, ações, raciocínio pesado) roda em LLMs pagos baratos via OpenRouter (GLM-5.3-Flash/DeepSeek V4.1 Flash), com Groq grátis como primeira tentativa e Claude Sonnet 5 reservado só para `deep_reasoning`. Custo real observado em teste: frações de centavo de dólar por sessão de uso normal.

Problemas conhecidos que SAÍRAM da lista: watchdog nunca reconectando, ferramentas travando o áudio, teclado fantasma no open_app, resposta duplicada/repetitiva, memória desconectada do vault, microfone sempre ativo consumindo cota à toa.

Problemas que PERMANECEM: instabilidade ocasional do lado do servidor do Gemini (erro 1011, fora do nosso controle); a junção dos fragmentos de transcrição nos logs já foi corrigida em `_join_transcript`, mas o diagnóstico temporário `[Transcript]` ainda está no código e a qualidade do reconhecimento de fala não foi validada de ponta a ponta; Vertex AI Express Mode ainda não foi testado como via gratuita pra voz.