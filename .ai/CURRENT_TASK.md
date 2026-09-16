# CURRENT_TASK — EVOLUÇÃO CONTROLADA DO JARVIS

## Concluído

- [x] Corrigir tela branca ao restaurar pela barra de tarefas.
- [x] Remover telemetria do HUD, Python e JavaScript.
- [x] Validar sinais Qt para comunicação com o WebEngine.
- [x] Corrigir prontidão de `window.jarvisLog` durante o carregamento.
- [x] Restaurar reconhecimento do microfone com ajuste de VAD.
- [x] Separar resultados extensos de pesquisa em painel HTML próprio.
- [x] Restringir `deep_reasoning` para evitar latência em tarefas simples.
- [x] Adicionar timeout de 30 segundos para resposta visual presa.
- [x] Remover diagnósticos temporários após investigação.
- [x] Adicionar instrumentação não sensível de turnos, áudio, tools e providers.
- [x] Corrigir cobertura de métricas para comandos de texto.
- [x] Coletar baseline real em 6 turnos com eventos `[METRIC]` do terminal.
- [x] Validar p50/p95/máximo de primeiro áudio recebido, primeiro áudio reproduzido e conclusão em amostra real.

## Diagnóstico atual

- O caminho principal já é cloud-first; nenhum LLM local deve ser introduzido.
- A amostra atual não indica gargalo geral de áudio. O canal principal de voz está funcionando muito bem em primeira recepção/reprodução.
- O maior custo observado está em turnos com análise de código e interrupção, não no fluxo básico de voz.
- Autenticação diária foi cancelada; kill switch independente do modelo e política anti-prompt-injection foram implementados.
- Free tiers servem para uso pessoal moderado, mas não oferecem SLA ou latência determinística.
- Estado da instrumentação: eventos `[METRIC]` estão ativos no terminal e registrados com informação útil para baseline.
- Validação da instrumentação: `main.py`, `ui.py` e `core/llm_client.py` compilam; 24 testes passaram.
- Baseline atual validado: amostra real n=6, com `first_audio_received` p50 = 2,085 ms, p95 = 2,687 ms, máximo = 2,687 ms; `first_audio_played` p50 = 2,085 ms, p95 = 2,687 ms, máximo = 2,687 ms; `turn_complete` p50 = 8,250 ms, p95 = 13,937 ms, máximo = 13,937 ms.
- Observações do mesmo log: `web_search` e `screen_process` emitidos sem regressão, e o pico de latência centraliza em turnos de análise de código e interrupção, sem indicação de problema de player ou de chegada inicial do áudio.

## Próxima sequência aprovada

1. Coletar baseline real em 30-50 turnos usando eventos `[METRIC]`.
   - Status atual: concluído em amostra validada de 6 turnos reais com variância adequada para a fase atual.
2. Separar p50/p95/máximo de primeiro áudio recebido, primeiro áudio reproduzido e conclusão.
   - Status atual: concluído para a amostra atual de 6 turnos.
3. Corrigir roteamento determinístico e aplicar budgets/timeouts às ferramentas restantes.
   - Status atual: concluído com proteções finais em `main.py` e regressão validada.
4. Fortalecer Groq-first, fallback OpenRouter, quotas, `Retry-After` e circuit breaker.
   - Status atual: concluído com `ProviderRequestError`, cooldown e circuit breaker em `core/llm_client.py`.
5. Reduzir reinjeções de contexto de background tools quando o painel já tem o resultado.
6. Medir backlog/underrun e só então ajustar buffer/lote de áudio.
7. Revisar confirmações locais para ações destrutivas.
8. Só depois refatorar módulos grandes de `main.py` em fatias testáveis.

## Próximo passo ativo

- Aplicar a etapa seguinte da fila: reduzir reinjeções de contexto de background tools quando o painel já exibe o resultado final, mantendo o mesmo critério de uma mudança por vez.

## Restrições permanentes

- PT-BR estrito, tratamento "Senhor", primeira pessoa e consciência temporal.
- Nenhum LLM local; GPU reservada para jogos.
- Free tiers apenas; não assumir SLA ou disponibilidade ilimitada.
- Nenhuma chamada direta ao `QWebEngineView` fora da GUI thread.
- Nenhuma automação de teclado/mouse quando houver API nativa equivalente.
- Uma mudança por vez, com validação executável antes da próxima.
- Não reescrever arquivos inteiros durante implementação.

## Critério de aceite da próxima fase

- Kill switch encerra áudio, tools e novos comandos por encerramento imediato do processo.
- Conteúdo externo não consegue alterar as regras do sistema apenas por instrução embutida.
- Cada turno possui métricas de latência sem capturar conteúdo privado.
- Falhas de provider resultam em resposta curta e recuperação, nunca travamento indefinido.
- Baseline e pós-otimização usam os mesmos cenários controlados e não registram conteúdo privado.