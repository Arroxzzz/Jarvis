# CURRENT_TASK — PRÓXIMAS IMPLEMENTAÇÕES APROVADAS

## STATUS
Base 100% consolidada. Auditoria encerrada. Efeito Coulson implementado.

## PRÓXIMA AÇÃO RECOMENDADA — E-mail IMAP/SMTP
Menor esforço, maior valor imediato. Zero dependência nova.
- `actions/email_watcher.py`: IMAP polling + SMTP envio
- Tool `send_email(to, subject, body)` no main.py
- Leitura proativa de e-mails VIP (lista em long_term.json)

## FILA APROVADA (ordem de implementação)
1. E-mail IMAP leitura + SMTP envio
2. Evolution API — WhatsApp envio por comando de voz
3. Spotify API — controle de música
4. Google Calendar — leitura de agenda + proatividade temporal
5. P7b — Sync pendrive↔PC via Supabase (infra pronta)
6. Modos de operação (Sentinela/Foco/Estudo/Jogos)
7. core/persona.py — consolidar identidade

## DECISÕES JÁ FECHADAS (não reabrir)
- Kokoro TTS: descartado
- Dashboard web: removido permanentemente
- Ollama: arquivado
- Polling para Coulson: substituído por SSE (ntfy.sh)
- Sync automático contínuo: não fazer
