# CURRENT_TASK — ESTABILIZAÇÃO PÓS-MIGRAÇÃO DE UI (WebGL)

## STATUS
Migração de UI concluída. Threading fix (sinais Qt) resolveu duplicação
de log e crash em reconexão de rede. 2 bugs residuais identificados,
aguardando correção. 1 nova diretriz de simplificação de UI pendente.

## BUGS ABERTOS
1. Tela branca / travamento ao restaurar da MINIMIZAÇÃO (barra de tarefas).
   Restaurar da BANDEJA do sistema funciona normalmente — indica que são
   dois caminhos de código distintos no Qt lidando com estados diferentes
   de visibilidade da janela. Causa suspeita: gerenciamento de contexto
   OpenGL do QWebEngineView em janelas minimizadas via barra de tarefas
   (Windows), possivelmente relacionado a driver AMD (RX 7600).
   AÇÃO PENDENTE: diferenciar tratamento de changeEvent (minimizar) vs.
   hide()/tray icon (bandeja) em ui.py — hoje aparentemente só um dos
   caminhos foi coberto pelo fix anterior.

2. Fix de 1ª pessoa em "[SYSTEM_ALERT] Conexão restabelecida" e debounce
   de set_speaking() — diffs entregues, aplicação/validação pendente de
   confirmação do Senhor Paulo.

## NOVA DIRETRIZ — REMOÇÃO DE TELEMETRIA
Senhor Paulo decidiu remover PERMANENTEMENTE o painel de telemetria
(CPU/MEM/DISK/GPU/TMP/UP/PROC/OS) do HUD. Considerado ocupação de espaço
desnecessária que não agrega ao projeto. NÃO IMPLEMENTADO AINDA — aguarda
próxima rodada de trabalho, junto com o fix do bug de minimização.

## PRÓXIMA AÇÃO IMEDIATA (ordem sugerida)
1. Investigar e corrigir bug de tela branca ao restaurar de minimização.
2. Remover painel de telemetria do index.html + código Python associado
   (_push_telemetry, jarvisUpdateTelemetry) já que não será mais usado.
3. Validar fixes de 1ª pessoa e debounce de set_speaking já entregues.
4. Retomar Problema 4 da rodada anterior (painel dedicado de
   pesquisas/resultados, separado do log de chat) — planejado, não iniciado.

## LEMBRETE IMPORTANTE
A troca de interface para WebGL foi decisão válida e correta. Os bugs
encontrados são custo técnico normal de qualquer migração de renderização
de UI, não erro do Senhor Paulo. Continuar tratando um problema de cada vez.