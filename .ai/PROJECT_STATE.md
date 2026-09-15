# JARVIS MARK LI — ESTADO ATUAL DO PROJETO

## Estado validado

- Aplicação desktop Python em produção, com `PyQt6` + `QWebEngineView`.
- `main.py` mantém `JarvisLive` em thread própria com `asyncio`; a UI Qt fica na thread principal.
- Gemini Live é o caminho primário de voz, com PCM via `sounddevice`, transcrições e VAD automático.
- A UI WebGL foi validada: restauração após minimizar corrigida, telemetria removida e painel de pesquisas separado do log.
- Sinais Qt continuam obrigatórios para chamadas ao `QWebEngineView`.
- O microfone foi diagnosticado e restaurado; o VAD foi ajustado.
- `deep_reasoning` foi restringido para não ser usado em contas, perguntas simples, resumos básicos, traduções ou pesquisas.
- O fluxo de visão possui timeout de 30 segundos e reconexão controlada quando a resposta multimodal não chega.
- `main.py` e `ui.py` compilam sem erros; testes existentes cobrem criptografia, notas e sync.

## Problemas ainda conhecidos

- APIs gratuitas não oferecem latência zero, SLA ou disponibilidade constante.
- A visão depende da capacidade e disponibilidade do modelo Live; o timeout evita congelamento, mas não torna a análise instantânea.
- O áudio pode ficar picotado quando a API deixa de entregar chunks.
- O histórico da UI é limpo após reconexão.
- Há avisos não fatais de DPI do Qt e AFC do SDK Gemini.
- Não existe autenticação forte de proprietário. Identidade no prompt não é controle de acesso.
- Não existe ainda bloqueio de emergência independente da Gemini.
- `main.py` concentra sessão Live, áudio, tools, visão, reconexão, memória e watchdog.

## Direção do produto

JARVIS deve ser um assistente pessoal de voz externo à máquina, com resposta curta,
consciência temporal, tratamento "Senhor", primeira pessoa, memória controlada,
ferramentas seguras e prioridade absoluta para fluidez. A GPU local permanece livre
para jogos; nenhum LLM local deve ser introduzido.

## Decisão cloud provisória

1. Gemini Live para diálogo de voz e multimodalidade.
2. Groq para texto rápido quando houver chave e cota.
3. OpenRouter `:free` apenas como fallback, com limites explícitos.
4. Supabase Free para memória sincronizada, autenticação opcional e storage cifrado.
5. Cloudflare Workers Free somente para auth, rate limit, webhook e proxy curto; não para a sessão de áudio Live.

Free tier não significa SLA, disponibilidade contínua ou latência constante.