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

## Diagnóstico atual

- O caminho principal já é cloud-first; nenhum LLM local deve ser introduzido.
- Latência veio de chamadas externas desnecessárias, limites/instabilidade da API
  Live e ferramentas que aguardam serviços externos.
- A troca para HTML/WebGL não foi a causa raiz da latência.
- Autenticação diária foi cancelada; kill switch independente do modelo e política anti-prompt-injection foram implementados.
- Free tiers servem para uso pessoal moderado, mas não oferecem SLA ou latência determinística.
- Estado da instrumentação: eventos `[METRIC]` aparecem somente no terminal; ainda não há agregação automática p50/p95.
- Validação da instrumentação: `main.py`, `ui.py` e `core/llm_client.py` compilam; 24 testes passaram.
- Baseline parcial: primeiro áudio em 1,797 s, conclusão em 9,640 s; `open_app` é a tool local mais lenta observada, enquanto visão ficou abaixo de 0,21 s.
- A amostra ainda contém somente um `turn_start`; é insuficiente para p50/p95 e exige corrigir a cobertura das métricas antes de otimizar o player.

## Próxima sequência aprovada

1. Coletar baseline real em 30-50 turnos usando eventos `[METRIC]`.
2. Separar p50/p95/máximo de primeiro áudio recebido, primeiro áudio reproduzido e conclusão.
3. Corrigir roteamento determinístico e aplicar budgets/timeouts às ferramentas restantes.
4. Fortalecer Groq-first, fallback OpenRouter, quotas, `Retry-After` e circuit breaker.
5. Reduzir reinjeções de contexto de background tools quando o painel já tem o resultado.
6. Medir backlog/underrun e só então ajustar buffer/lote de áudio.
7. Revisar confirmações locais para ações destrutivas.
8. Só depois refatorar módulos grandes de `main.py` em fatias testáveis.

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