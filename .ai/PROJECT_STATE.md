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
- `main.py` e `ui.py` compilam sem erros; suíte relevante atual: 30 testes passando.
- `core/llm_client.py` agora registra `Retry-After`/rate-limit, bloqueia provider em circuit breaker e faz fallback Groq→OpenRouter de forma controlada.

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
- O tamanho atual da orchestrator não é um problema por si só, mas é um sinal de acoplamento; a estratégia atual é decompor em blocos pequenos e testados sem mexer em áudio ou em lógica crítica.
- Meta de manutenção: manter a orquestração principal em faixa de 600-900 linhas, e mover helpers de áudio, visão, tools e monitoramento para módulos específicos conforme a decomposição continuar.
- A rodada atual de refatoração controlada foi concluída com `main.py` em 2.433 linhas; o lifecycle ficou mais organizado, mas a meta de 600-900 linhas ainda exige uma fase posterior de extração para módulos próprios.
- A fase modular posterior começou com `core/async_tool_runner.py`, que agora concentra os dois wrappers de timeout de tools; `main.py` preserva os aliases internos e ficou com 2.417 linhas. Suíte atual: 30 testes passando.
- O bloco estático `TOOL_DECLARATIONS` foi extraído integralmente para `core/tool_declarations.py`; as 27 tools foram preservadas na mesma ordem. `main.py` ficou com 1.883 linhas e o novo módulo com 535 linhas. Áudio, UI e conexão Gemini não foram alterados.
- As constantes puras de runtime foram extraídas para `core/runtime_constants.py`: timezone, fallbacks Live, cache e parâmetros de áudio. Valores foram validados, `main.py` ficou com 1.875 linhas e a suíte permaneceu com 30 testes passando. Caminhos e leitura de configuração continuam no `main.py` por participarem do boot.
- O I/O de configuração foi extraído para `core/runtime_config.py`, mantendo wrappers compatíveis no `main.py`. API key, prompt fallback, leitura JSON e escrita atômica do cache foram cobertos por testes; suíte atual: 32 testes passando. `main.py` ficou com 1.860 linhas.
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
- exclusão e sincronização opcionais, nunca obrigatórias.

Busca textual e indexação local não equivalem a introduzir um LLM local. Embeddings
ou outro índice semântico só devem ser considerados depois de medir custo, memória
e benefício real.

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
3. OpenRouter `:free` apenas como fallback, com limites explícitos.
4. Supabase Free apenas para memória sincronizada e storage cifrado; autenticação de usuário não faz parte do fluxo diário.
5. Cloudflare Workers Free somente para rate limit, webhook e proxy curto; não para a sessão de áudio Live.

Free tier não significa SLA, disponibilidade contínua ou latência constante.