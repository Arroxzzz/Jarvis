# JARVIS MARK LI — ARQUITETURA VIGENTE E ALVO

## ARQUITETURA VIGENTE

# CAMADAS

- Boot/portabilidade: `_INICIAR_JARVIS.bat`, `boot_stage0.py`, `project.enc`, `core/crypto_vault.py`.
- Interface: `ui.py` + `ui_web/index.html` com PyQt6, QWebEngineView, WebGL e QWebChannel.
- Núcleo: `main.py`, `JarvisLive`, Gemini Live, áudio, tools, reconexão e watchdog.
- Dados: `memory/`, `knowledge/`, `core/sync_manager.py` e Supabase opcional.
- Extensões: `plugins/` descobertos pelo `core/plugin_loader.py`.
- Ações: `actions/` para sistema, arquivos, web, comunicação, visão e desenvolvimento.

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