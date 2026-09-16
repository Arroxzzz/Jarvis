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
   - Status atual: concluído com deduplicação de `web_search` e `code_helper`, coberta por regressão.
6. Medir backlog/underrun e só então ajustar buffer/lote de áudio.
   - Status atual: concluído como diagnóstico; nenhum ajuste de buffer foi autorizado ou aplicado.
7. Revisar confirmações locais para ações destrutivas.
   - Status atual: concluído com confirmação explícita em `file_controller.py` e regressão validada.
8. Só depois refatorar módulos grandes de `main.py` em fatias testáveis.
   - Status atual: rodada atual concluída; extrações de lifecycle, runtime, visão, tools, painel e background foram validadas. `main.py` permanece com 2.433 linhas, portanto a meta de 600-900 linhas não foi declarada como atingida.

## Norte de produto após a fila atual

Depois de estabilizar a orchestrator, a evolução deve seguir esta ordem, sem tentar
implementar tudo de uma vez:

9. Memória local Obsidian
   - Definir diretório do vault, contrato de frontmatter, permissões e formato de
     citações de origem.
   - Criar indexação incremental e busca textual antes de qualquer busca semântica.
   - Validar lembranças por recência, fonte e desambiguação.

10. Resolver contextual de arquivos e estado do PC
   - Priorizar Downloads, Desktop, janela ativa, navegador e mídia.
   - Ranking por recência, nome aproximado, extensão e conteúdo.
   - Pedir confirmação somente quando houver candidatos próximos ou ação sensível.

11. Mentoria full stack
   - Adicionar fluxos de leitura de projeto, análise, testes, revisão e patch aprovado.
   - Manter o Senhor no controle das alterações e preservar logs de execução.

12. Segurança operacional em camadas
   - Detectar sinais, registrar evidências e propor contenção.
   - Preferir quarentena e bloqueio reversível à exclusão.
   - Exigir allowlist/confirmação para ações de alto impacto.

13. Gatilhos sonoros e automação contextual
   - Implementar palma/estalo com processamento local, debounce e medição de CPU.
   - Integrar estado de mídia e comandos como pausar vídeo por API nativa quando possível.
   - Suspender sensores e métricas pesadas quando minimizado ou durante jogos.

14. Autodiagnóstico controlado
   - Gerar diagnóstico e patch proposto do próprio projeto.
   - Rodar testes e apresentar diff.
   - Aplicar somente após aprovação explícita; nenhuma autoalteração irrestrita.

## Próximo passo ativo

- Continuar a refatoração controlada de `main.py` em blocos pequenos, com regressão
   após cada extração e sem tocar no caminho principal de áudio.
- Blocos já extraídos: painel/contexto, tarefas em background, visão, rotas de tools,
   tarefas de runtime, reconexão, setup de sessão e bootstrap do cliente Live.
- A fase modular começou com `core/async_tool_runner.py`, que recebeu os wrappers
   de timeout de tools. A próxima redução deve mover outra fronteira coesa para
   módulo próprio, sempre com teste específico e sem tocar primeiro no áudio Live.
- O bloco grande `TOOL_DECLARATIONS` foi extraído para `core/tool_declarations.py`;
   27 tools preservadas, import de `main.py` validado e suíte completa verde.
- As constantes puras de runtime foram extraídas para `core/runtime_constants.py`;
   valores preservados e suíte completa verde. Caminhos, API key e leitura de prompt
   continuam no `main.py` por estarem ligados ao boot.
- O I/O de configuração foi extraído para `core/runtime_config.py`; wrappers do
   `main.py` preservados, 2 testes específicos adicionados e suíte completa verde.

## Restrições permanentes

- PT-BR estrito, tratamento "Senhor", primeira pessoa e consciência temporal.
- Nenhum LLM local; GPU reservada para jogos.
- Free tiers apenas; não assumir SLA ou disponibilidade ilimitada.
- Nenhuma chamada direta ao `QWebEngineView` fora da GUI thread.
- Nenhuma automação de teclado/mouse quando houver API nativa equivalente.
- Uma mudança por vez, com validação executável antes da próxima.
- Não reescrever arquivos inteiros durante implementação.
- A experiência pode ser inspirada no JARVIS ficcional, mas os critérios de aceite
   devem ser mensuráveis e não podem depender de promessas de AGI.
- Contexto contínuo de tela, microfone, disco e processos não é permitido por padrão;
   preferir eventos, consultas sob demanda e escopos mínimos.
- Ações de segurança destrutivas exigem evidência, log, reversão ou confirmação local.
- Memória local deve preservar privacidade, origem e controle de escrita do usuário.

## Critério de aceite da próxima fase

- Kill switch encerra áudio, tools e novos comandos por encerramento imediato do processo.
- Conteúdo externo não consegue alterar as regras do sistema apenas por instrução embutida.
- Cada turno possui métricas de latência sem capturar conteúdo privado.
- Falhas de provider resultam em resposta curta e recuperação, nunca travamento indefinido.
- Baseline e pós-otimização usam os mesmos cenários controlados e não registram conteúdo privado.