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
transcrições, VAD, voz Charon, resumption e compressão de contexto.

## UI E THREADING

Qt é a thread principal; `JarvisLive` roda em thread asyncio separada. JavaScript
usa `_Backend` via QWebChannel para comandos. Logs, estados, conteúdo, câmera e
reconfiguração usam sinais Qt. Código fora da GUI thread não pode chamar `runJavaScript()` diretamente.

## TOOLS E FALLBACKS

As tools são declaradas em `TOOL_DECLARATIONS` e despachadas por `_execute_tool()`.
`core/llm_client.py` fornece Groq e OpenRouter com fallback; os defaults históricos
de Ollama/OpenAI-compatível não devem ser ativados, pois o produto não usa LLM local.

## LACUNAS DE SEGURANÇA

- Prompt e identidade "Paulo" não autenticam o operador.
- Ações destrutivas precisam de confirmação ou desbloqueio local.
- Falta um bloqueio de emergência que pare áudio, tools, notificações e comandos pendentes.
- Segredos cloud devem permanecer fora do frontend e fora de prompts.

## ARQUITETURA CLOUD RECOMENDADA

- Gemini Live: caminho primário de voz e visão.
- Groq: texto rápido quando houver quota gratuita disponível.
- OpenRouter `:free`: fallback; limites atuais documentados incluem caps de RPM/RPD e limites upstream.
- Supabase Free: Postgres/Auth/Storage/Edge Functions; free tier inclui limites de armazenamento, funções e pausa por inatividade.
- Cloudflare Workers Free: auth, rate limit, webhook e proxy curto; não transportar o WebSocket de áudio Live pelo Worker.

Fontes oficiais consultadas:
- https://ai.google.dev/gemini-api/docs/models/gemini
- https://openrouter.ai/docs/limits
- https://supabase.com/pricing
- https://developers.cloudflare.com/workers/platform/limits/

## PLANO DE EVOLUÇÃO

1. Autenticação do proprietário, bloqueio de emergência e allowlist de tools.
2. Observabilidade de latência por turno sem conteúdo sensível.
3. Roteamento determinístico, timeouts, cancelamento e circuit breaker.
4. Buffer adaptativo e fallback de visão textual.
5. Separação gradual do `main.py` em módulos testáveis.
6. Testes de Qt, Live, reconexão, visão, segurança e concorrência.

Não é tecnicamente possível prometer 100% de eficiência ou latência zero com APIs
externas gratuitas. O critério mensurável é feedback rápido em condições normais,
timeouts finitos e nenhuma falha indefinidamente bloqueante.