# CURRENT_TASK — Sprint 5 EM ANDAMENTO — PONTO 0 É A PRÓXIMA AÇÃO

## Contexto de handoff (sessão anterior atingiu limite de contexto)
Ler `.ai/PROJECT_STATE.md` INTEIRO antes de qualquer código — contém o
diagnóstico completo e a especificação técnica exata do que fazer.
Este arquivo é só o resumo acionável.

## Estado atual confirmado por teste real (Senhor Paulo)
- ✅ Latência de voz: 1-2s (objetivo da sprint CUMPRIDO).
- ✅ Microfone: 78+ chunks enviados continuamente, sem falha.
- ✅ Conexão Live estabelece e permanece de pé durante uso normal.
- ❌ ESC durante tool ativa → 1007, derruba socket.
- ❌ Texto digitado na UI durante sessão ativa → 1007, derruba socket.
- ❌ Saudação de boot não fala.
- ❌ ACTIVITY LOG poluído com tracebacks crus.

## PRÓXIMA AÇÃO IMEDIATA (sem precisar perguntar nada ao usuário)
Implementar o PONTO 0 conforme especificação completa em
`.ai/PROJECT_STATE.md` seção "⭐ ESPECIFICAÇÃO DO PONTO 0": adicionar
`asyncio.Lock` em `JarvisLive`, criar métodos seguros de envio
(`_safe_send_content` / equivalente para tool_response), migrar todos os
pontos de chamada listados na especificação. Isso resolve ESC, texto
digitado, e saudação de boot simultaneamente (mesma causa raiz).

Gerar diffs cirúrgicos "antes/depois" para `main.py`, sem reescrever
arquivo inteiro, seguindo o padrão de todas as rodadas anteriores desta
sessão.

## Depois do Ponto 0 (ordem já definida, não reordenar)
1. Testar: ESC durante tool longa, texto digitado durante fala ativa, boot
   do zero confirmando saudação única.
2. Sanitização de logs — camada mínima em `main.py` primeiro (trocar
   `write_log` de erros crus por `logging.exception()` → `jarvis.log`).
3. Menu de seleção de dispositivo de mic/output na UI (`ui.py`), aplicado
   só no boot/reconexão, sem hot-swap em runtime na v1.

## Decisões já fechadas nesta sprint — NÃO reabrir sem novo motivo concreto
- Model ID Live: manter descoberta dinâmica + cache. NÃO fixar hardcoded.
  (Ver justificativa completa em PROJECT_STATE.md, Ponto 3.)
- Logs: não migrar todos os `actions/*.py` de uma vez — só `main.py` por
  enquanto, é de onde vêm 100% dos tracebacks observados.
- Seleção de device de áudio: sem hot-swap em runtime na v1.

## Critério de aceite Sprint 5 (atualizado)
- Sessão Live conecta e permanece estável sem loop de reconexão.
- ESC cancela tool ativa sem derrubar o socket (1007).
- Texto digitado na UI funciona durante qualquer estado de sessão.
- Saudação de boot é falada uma única vez por sessão bem-sucedida.
- ACTIVITY LOG não exibe tracebacks crus ao usuário final.
- `FREE_MODELS["code"]` validado contra catálogo gratuito atual do
  OpenRouter (pendência antiga, não relacionada a esta rodada, ainda aberta).