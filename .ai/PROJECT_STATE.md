## ATUALIZAÇÃO (sessão pós-migração UI) — bugs residuais mapeados

### Confirmado funcionando
- Threading fix (sinais Qt _log_sig/_state_sig/_clear_log_sig): resolveu
  duplicação de log e crash em reconexão de rede — validado em campo.
- Animação SPEAKING/LISTENING da orb: funcionando corretamente após
  debounce em set_speaking (aguardando confirmação final do Senhor Paulo).
- Reconexão de sessão: anunciada corretamente ao usuário.
- Pesquisas longas: não travam mais o sistema (era comportamento normal
  de latência de API, não bug).

### Bug em aberto — comportamento distinto entre minimizar e bandeja
Restaurar da bandeja do Windows: funciona normalmente.
Restaurar da minimização pela barra de tarefas: tela branca / travamento.
Isso indica que o QWebEngineView reage de forma diferente a esses dois
eventos de visibilidade do Qt — precisa de tratamento explícito separado
para cada caminho (provavelmente em changeEvent/showEvent de MainWindow).

### Nova diretriz de produto
Painel de telemetria (CPU/MEM/DISK/GPU/TMP) será REMOVIDO permanentemente
do HUD por decisão do Senhor Paulo — não agrega valor percebido ao projeto.