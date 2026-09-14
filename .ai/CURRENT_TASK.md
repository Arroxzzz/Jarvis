# CURRENT_TASK — VALIDAÇÃO DOS 3 FIXES PÓS-MIGRAÇÃO UI

## STATUS
Migração de UI (WebGL/QWebEngineView) concluída estruturalmente. 3 fixes
aplicados nesta sessão, aguardando bateria de testes de campo antes de
prosseguir para novas features.

## PRÓXIMA AÇÃO IMEDIATA — Bateria de validação
1. T1 — Confirmar que reconexão de sessão limpa o log da UI (sem duplicação).
2. T2 — Confirmar que voz `Charon` não gera mais o erro 1007 de
   CONTENT_TYPE_AUDIO. Se persistir mesmo com Charon, o problema não é a
   voz — investigar outra causa (possível relação com affective_dialog).
3. T3 — Confirmar que `open_folder` abre pastas sem roubar foco/simular
   teclado, e que `open_app` continua funcionando normalmente para
   programas.
4. T4 — Regressão geral: notas, código, sync, apps.

## FILA APROVADA (após validação dos fixes)
1. Investigar erro de sync Supabase com nomes acentuados.
2. Resolver responsividade da UI em telas menores (COM cuidado, diff revisado
   antes de aplicar — não repetir o incidente desta sessão).
3. E-mail IMAP leitura + SMTP envio
4. Evolution API — WhatsApp envio por comando de voz
5. Spotify API — controle de música
6. Google Calendar — leitura de agenda + proatividade temporal
7. P7b — Sync pendrive↔PC via Supabase
8. Modos de operação (Sentinela/Foco/Estudo/Jogos e pensar em alguns eficientes e criativos para o uso do Senhor Paulo)
9. core/persona.py — consolidar identidade

## DECISÕES JÁ FECHADAS (não reabrir)
- Kokoro TTS: descartado
- Dashboard web: removido permanentemente
- Ollama: arquivado
- UI: WebGL/HTML via QWebEngineView é a interface oficial definitiva —
  widgets Qt antigos desativados, não reativar
- Câmera ao vivo no HUD: fora de escopo permanente (planejado para quando
  houver webcam dedicada, como frente de trabalho totalmente separada)
- FPS do WebGL nunca reduz em segundo plano — decisão explícita do Senhor
  Paulo, não "otimizar" isso sem pedido novo