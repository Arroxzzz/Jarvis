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

## Diagnóstico atual

- O caminho principal já é cloud-first; nenhum LLM local deve ser introduzido.
- Latência veio de chamadas externas desnecessárias, limites/instabilidade da API
  Live e ferramentas que aguardam serviços externos.
- A troca para HTML/WebGL não foi a causa raiz da latência.
- Falta autenticação forte do proprietário e bloqueio de emergência independente do modelo.
- Free tiers servem para uso pessoal moderado, mas não oferecem SLA ou latência determinística.

## Próxima sequência aprovada

1. Implementar autenticação do proprietário sem tocar ainda no pipeline de áudio.
2. Implementar bloqueio de emergência com prioridade sobre tools e reprodução.
3. Criar observabilidade de latência por turno, sem dados sensíveis.
4. Corrigir roteamento determinístico e timeouts das ferramentas restantes.
5. Fortalecer fallback cloud, quotas e circuit breaker.
6. Só depois refatorar módulos grandes de `main.py` em fatias testáveis.

## Restrições permanentes

- PT-BR estrito, tratamento "Senhor", primeira pessoa e consciência temporal.
- Nenhum LLM local; GPU reservada para jogos.
- Free tiers apenas; não assumir SLA ou disponibilidade ilimitada.
- Nenhuma chamada direta ao `QWebEngineView` fora da GUI thread.
- Nenhuma automação de teclado/mouse quando houver API nativa equivalente.
- Uma mudança por vez, com validação executável antes da próxima.
- Não reescrever arquivos inteiros durante implementação.

## Critério de aceite da próxima fase

- Usuário não autenticado não consegue executar tools sensíveis.
- Bloqueio de emergência interrompe áudio, tools e novos comandos.
- Cada turno possui métricas de latência sem capturar conteúdo privado.
- Falhas de provider resultam em resposta curta e recuperação, nunca travamento indefinido.