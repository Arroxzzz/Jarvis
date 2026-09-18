# BASELINE MANUAL — JARVIS MARK LI

## Objetivo

Registrar a linha de base funcional em produção antes da refatoração estrutural planejada nas fases 0 a 5. Este documento funciona como referência operacional e de regressão para os 7 fluxos principais do sistema.

## Linha de base

- Tag de referência: `v1-monolith-baseline`
- Status de testes: `python -m pytest tests/ -v` com 76 testes verdes
- Estado geral: linha de produção estável, sem quebra do loop principal de voz e com segurança mantida em nível aceitável

## Fluxos manuais validados

### 1) Boot do sistema
- Cenário: iniciar o projeto em ambiente local com UI e runtime ativos
- Resultado esperado: processo inicia sem crash, plugins descobertos e carregados conforme estado persistido, boot registra ativos/desligados
- Resultado anotado: OK

### 2) Conexão de voz Live e troca de texto
- Cenário: conectar a sessão principal de voz e enviar uma instrução textual simples
- Resultado esperado: sessão abre normalmente, caminho de texto responde sem bloquear e sem quebrar o loop
- Resultado anotado: OK

### 3) Busca de contexto e projeto ativo
- Cenário: pedir um arquivo ou relatório relevante do projeto ativo ou do desktop
- Resultado esperado: contexto resolve arquivo e projeto corretamente e evita retornos ambíguos
- Resultado anotado: OK

### 4) Memória sugerida e memória explícita
- Cenário: usuário pede lembrar ou o sistema identifica fato relevante para salvar
- Resultado esperado: memória segue política de 4 estados; itens relevantes são sugeridos ou salvos sem poluir o histórico casual
- Resultado anotado: OK

### 5) Operações de arquivos não destrutivas
- Cenário: criar arquivo, criar pasta, mover arquivo simples, abrir pasta
- Resultado esperado: fluxo funciona sem confirmação indevida; só exclusão continua protegida
- Resultado anotado: OK

### 6) Ação destrutiva com confirmação
- Cenário: tentar excluir um arquivo ou pasta
- Resultado esperado: sistema pede confirmação explicita e só execute depois de consentimento
- Resultado anotado: OK

### 7) Segurança e plugins
- Cenário: plugin desconhecido ou de terceiro sem habilitação
- Resultado esperado: nasce desligado, não ativa silenciosamente, log de boot permanece neutro e seguro
- Resultado anotado: OK

## Observações finais

- Esta baseline é a linha segura e funcional antes do refactor de estrutura.
- A meta do refactor é reduzir acoplamento sem mexer na experiência principal do Jarvis.
- Qualquer mudança futura deve preservar estes 7 fluxos como critério mínimo de regressão.
