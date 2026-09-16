# JARVIS MARK LI — ARQUITETURA VIGENTE E ALVO

## ARQUITETURA VIGENTE

# CAMADAS

- Boot/portabilidade: `_INICIAR_JARVIS.bat`, `boot_stage0.py`, `project.enc`, `core/crypto_vault.py`.
- Interface: `ui.py` + `ui_web/index.html` com PyQt6, QWebEngineView, WebGL e QWebChannel.
- Núcleo: `main.py`, `JarvisLive`, Gemini Live, áudio, tools, reconexão e watchdog.
- Dados: `memory/`, `knowledge/`, `core/sync_manager.py` e Supabase opcional.
- Extensões: `plugins/` descobertos pelo `core/plugin_loader.py`.
- Ações: `actions/` para sistema, arquivos, web, comunicação, visão e desenvolvimento.
- Utilidades de execução: `core/async_tool_runner.py` concentra execução de tools síncronas em executor e seus timeouts, sem depender de Qt, Gemini Live ou áudio.
- Contratos estáticos de tools: `core/tool_declarations.py` concentra os schemas e descrições enviados ao Gemini; não contém implementação, UI, áudio ou conexão.
- Constantes de runtime: `core/runtime_constants.py` concentra valores puros de timezone, modelos fallback, cache e parâmetros de áudio; não executa lógica de boot.
- Configuração de runtime: `core/runtime_config.py` concentra leitura da API key, prompt fallback, JSON de configuração e escrita atômica de cache; `main.py` mantém apenas wrappers compatíveis e decide quando chamar essas operações.

## FLUXO DE VOZ

`sounddevice.InputStream` -> `out_queue` -> `send_realtime_input()` -> Gemini Live/VAD/transcrição/tool calls -> `receive()` -> `audio_in_queue`/FunctionResponse/sinais Qt -> `RawOutputStream` e HUD.

O modelo Live é descoberto dinamicamente, com fallbacks. O código configura áudio,
transcrições, VAD com sensibilidade alta, voz Charon, resumption e compressão de
contexto. O thinking está desativado no caminho Live para reduzir latência.

## UI E THREADING

Qt é a thread principal; `JarvisLive` roda em thread asyncio separada. JavaScript
usa `_Backend` via QWebChannel para comandos. Logs, estados, conteúdo, câmera e
reconfiguração usam sinais Qt. Código fora da GUI thread não pode chamar `runJavaScript()` diretamente.

## TOOLS E FALLBACKS

As tools são declaradas em `TOOL_DECLARATIONS` e despachadas por `_execute_tool()`.
`core/llm_client.py` fornece Groq e OpenRouter com fallback; os defaults históricos
de Ollama/OpenAI-compatível não devem ser ativados, pois o produto não usa LLM local.
`deep_reasoning` é reservado para tarefas genuinamente complexas e não deve atender
aritmética, perguntas simples, resumos básicos, traduções ou pesquisas.

## SEGURANÇA ATUAL E LACUNAS

- Não há autenticação diária por senha/passphrase; essa exigência foi cancelada para preservar fluidez no computador pessoal.
- Kill switch local: `Ctrl+Shift+F12` ou item da bandeja encerra o processo com `os._exit(0)`, sem depender da IA, rede ou event loop.
- O prompt-base instrui o modelo a tratar web, arquivos, imagens, notificações, tools e memória como dados não confiáveis.
- Ações destrutivas precisam de confirmação ou desbloqueio local.
- Segredos cloud devem permanecer fora do frontend e fora de prompts.

## ARQUITETURA-ALVO DO PRODUTO

### Memória local baseada em Obsidian

O vault Markdown local será a camada primária de memória de longo prazo do usuário.
Um futuro `core/memory_index.py` deverá indexar apenas metadados e texto necessário,
com atualização incremental por arquivo alterado. A consulta deverá combinar:

1. busca textual e normalização de termos;
2. recência e diretórios relevantes;
3. links, tags e frontmatter do Obsidian;
4. ranking semântico somente se o custo for comprovadamente aceitável.

O resultado deve carregar caminho e trecho de origem para o modelo. Memórias não
confirmadas devem ser apresentadas como hipótese, não como fato. Escrita no vault
deve ser explícita, auditável e limitada a diretórios permitidos.

### Contexto do computador

O contexto operacional deve ser obtido por um `ContextResolver` futuro, com fontes
de baixo custo e escopo controlado: arquivos recentes, área de trabalho, downloads,
janela ativa, abas do navegador e estado de mídia quando disponível por API nativa.
O resolver deve retornar candidatos classificados e pedir desambiguação apenas quando
a confiança for baixa. Não deve capturar a tela continuamente nem varrer o disco
inteiro em cada comando.

### Segurança autônoma

Um futuro `SecurityMonitor` deve separar detecção, decisão e ação:

- detecção: sinais do Windows, processos, arquivos e rede;
- decisão: regras determinísticas, allowlist e nível de confiança;
- ação: bloquear, isolar, registrar, restaurar ou pedir confirmação.

Quarentena e contenção são preferíveis à exclusão imediata. Cada ação deve registrar
motivo, evidência, horário e resultado. O kill switch permanece independente da IA.

### Gatilhos e automação contextual

Palmas e estalos devem usar detecção local de evento sonoro, com debounce, limiar
configurável e suspensão quando o aplicativo estiver minimizado ou quando o custo
medido afetar jogos. O gatilho apenas ativa uma janela de interação; não autoriza
ações sensíveis por si só.

Comandos como "pause o vídeo" devem consultar o estado de mídia e o navegador ativo
por APIs nativas, integração do navegador ou `browser_control`, nesta ordem. Não se
deve usar automação visual contínua como primeira opção.

### Mentoria e autocorreção

O modo de mentoria deve incluir leitura de projeto, explicação, testes, revisão de
diff e diagnóstico guiado, mantendo mudanças sob aprovação do Senhor. Autodiagnóstico
do próprio JARVIS é uma fase posterior: primeiro gerar diagnóstico e patch proposto,
depois executar testes, e só então permitir aplicação controlada. Autoalteração
irrestrita do código de produção não faz parte do alvo seguro.

## ARQUITETURA CLOUD RECOMENDADA

- Gemini Live: caminho primário de voz e visão.
- Groq: texto rápido quando houver quota gratuita disponível.
- OpenRouter `:free`: fallback; limites atuais documentados incluem caps de RPM/RPD e limites upstream.
- Supabase Free: Postgres/Storage/Edge Functions para memória sincronizada; autenticação de usuário não faz parte do fluxo diário.
- Cloudflare Workers Free: rate limit, webhook e proxy curto; não transportar o WebSocket de áudio Live pelo Worker.

Fontes oficiais consultadas:
- https://ai.google.dev/gemini-api/docs/models/gemini
- https://openrouter.ai/docs/limits
- https://supabase.com/pricing
- https://developers.cloudflare.com/workers/platform/limits/

## PLANO DE EVOLUÇÃO

1. Bloqueio de emergência e allowlist/confirmação de tools destrutivas; autenticação diária foi cancelada.
2. [EM ANDAMENTO] Observabilidade de latência por turno sem conteúdo sensível.
3. Coleta de baseline p50/p95/máximo em 30-50 turnos controlados.
4. Roteamento determinístico, budgets, timeouts, cancelamento e circuit breaker.
5. Redução de reinjeções secundárias de contexto de tools em background.
6. Buffer adaptativo e fallback de visão textual.
7. Separação gradual do `main.py` em módulos testáveis.
8. Testes de Qt, Live, reconexão, visão, segurança, providers e concorrência.
9. [NOVA DIREÇÃO] Indexação local do vault Obsidian e recuperação de memória com fonte.
10. [NOVA DIREÇÃO] Resolução contextual de arquivos, downloads, janelas e mídia.
11. [NOVA DIREÇÃO] Monitor de segurança em camadas, com contenção auditável.
12. [NOVA DIREÇÃO] Gatilhos sonoros locais e modo de baixo consumo.
13. [NOVA DIREÇÃO] Mentoria full stack e autodiagnóstico controlado do próprio código.
14. [EM ANDAMENTO] Extrair fronteiras modulares coesas de `main.py`, começando por utilidades sem dependência de sessão. Já extraídos: timeouts, declarações estáticas, constantes puras e I/O de configuração.

Não é tecnicamente possível prometer 100% de eficiência ou latência zero com APIs
externas gratuitas. O critério mensurável é feedback rápido em condições normais,
timeouts finitos e nenhuma falha indefinidamente bloqueante.

### Instrumentação atual

`main.py` emite `[METRIC]` para `turn_start`, `first_audio_received`,
`first_audio_played`, `turn_complete`, `tool_start` e `tool_end`. `core/llm_client.py`
emite `provider_end` com provider, modelo, duração e status. Nenhum prompt, resposta,
áudio, transcrição, chave ou conteúdo de arquivo é registrado. Os eventos ainda são
somente terminal; a próxima etapa é coletar e comparar p50/p95/máximo.

## ORDEM DE IMPLEMENTAÇÃO DA LATÊNCIA

1. Coletar baseline com perguntas simples, tools, pesquisa, visão, interrupção e reconexão.
2. Medir primeiro áudio recebido versus primeiro áudio reproduzido para separar API de player.
3. Definir orçamento total por tool e provider, com resposta curta em timeout.
4. Priorizar Groq quando houver chave e quota; evitar cascatas desnecessárias.
5. Usar OpenRouter `:free` como fallback com backoff, `Retry-After` e circuit breaker.
6. Evitar reinjeção de resultados quando o painel já os apresenta.
7. Só então ajustar filas/lotes de áudio e validar interrupção.
8. Comparar os mesmos cenários antes/depois e registrar os números nesta documentação.