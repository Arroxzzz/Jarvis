# JARVIS MARK LI — ESTADO ATUAL DO PROJETO

## Estado validado

- Aplicação desktop Python em produção, com `PyQt6` + `QWebEngineView`.
- `main.py` mantém `JarvisLive` em thread própria com `asyncio`; a UI Qt fica na thread principal.
- Gemini Live é o caminho primário de voz, com PCM via `sounddevice`, transcrições e VAD automático.
- A sessão Live usa `thinking_budget=0` e `include_thoughts=False` para reduzir latência; o VAD usa sensibilidade alta, buffer de 300 ms e silêncio de 700 ms.
- A UI WebGL foi validada: restauração após minimizar corrigida, telemetria removida e painel de pesquisas separado do log.
- Sinais Qt continuam obrigatórios para chamadas ao `QWebEngineView`.
- O microfone foi diagnosticado e restaurado; o VAD foi ajustado.
- `deep_reasoning` foi restringido para não ser usado em contas, perguntas simples, resumos básicos, traduções ou pesquisas.
- O fluxo de visão possui timeout de 30 segundos e reconexão controlada quando a resposta multimodal não chega.
- Instrumentação de latência não sensível iniciada: turnos, primeiro áudio recebido/reproduzido,
  conclusão, duração de tools e duração de providers são emitidos como eventos `[METRIC]`.
- `core/llm_client.py` mede chamadas remotas Groq/OpenRouter sem registrar conteúdo.
- Comandos de texto agora iniciam eventos `[METRIC]` próprios; o caminho sem microfone participa do baseline.
- `main.py` e `ui.py` compilam sem erros; suíte atual: 24 testes passando.

## Problemas ainda conhecidos

- APIs gratuitas não oferecem latência zero, SLA ou disponibilidade constante.
- A visão depende da capacidade e disponibilidade do modelo Live; o timeout evita congelamento, mas não torna a análise instantânea.
- O áudio pode ficar picotado quando a API deixa de entregar chunks.
- O histórico da UI é limpo após reconexão.
- Há avisos não fatais de DPI do Qt e AFC do SDK Gemini.
- Autenticação diária por senha/passphrase foi cancelada por decisão do Senhor Paulo.
- Kill switch local implementado: `Ctrl+Shift+F12` ou menu da bandeja encerra o processo imediatamente, independente da Gemini.
- Defesa anti-prompt-injection adicionada ao prompt-base; conteúdo externo é tratado como dado não confiável.
- `main.py` concentra sessão Live, áudio, tools, visão, reconexão, memória e watchdog.
- Ainda não há baseline real de p50/p95; nenhuma troca de provider, buffer ou timeout foi feita nesta etapa.
- Métricas atualmente são emitidas no terminal, não persistidas nem agregadas; a coleta real de 30-50 turnos ainda está pendente.
- Baseline parcial coletado: primeiro áudio recebido/reproduzido em 1,797 s e turno completo em 9,640 s.
- Tools observadas: `save_memory` 0 ms, `open_folder` 15 ms, `screen_process` 172-203 ms e `open_app` 4,718-4,922 ms.
- O áudio picotado não pode ser atribuído ao player com esta amostra; a API Live continua sendo a hipótese principal.

## Direção do produto

JARVIS deve ser um assistente pessoal de voz externo à máquina, com resposta curta,
consciência temporal, tratamento "Senhor", primeira pessoa, memória controlada,
ferramentas seguras e prioridade absoluta para fluidez. A GPU local permanece livre
para jogos; nenhum LLM local deve ser introduzido.

## Decisão cloud provisória

1. Gemini Live para diálogo de voz e multimodalidade.
2. Groq para texto rápido quando houver chave e cota.
3. OpenRouter `:free` apenas como fallback, com limites explícitos.
4. Supabase Free apenas para memória sincronizada e storage cifrado; autenticação de usuário não faz parte do fluxo diário.
5. Cloudflare Workers Free somente para rate limit, webhook e proxy curto; não para a sessão de áudio Live.

Free tier não significa SLA, disponibilidade contínua ou latência constante.