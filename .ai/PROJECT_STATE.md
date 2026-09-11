## STATUS ATUAL (2026-09-11) — BASE CONSOLIDADA, FEATURES ATIVAS

### CONCLUÍDO E VALIDADO EM PRODUÇÃO
- Fase 0: Boot/descoberta dinâmica de modelo Live
- Fase 1 (Ponto 0): Lock de serialização do session (zero erro 1007)
- P0: Watchdog inteligente (congela durante tools, limite 5x, reconexão forçada)
- P1/P2: Gemini isolado para voz; Groq→OpenRouter para texto/código/pesquisa
- Fase 3: Segurança (AES-GCM+PBKDF2 dashboard→removido, sandbox desktop,
  allowlist user_data, escrita atômica de config, lock em browser_control)
- P7a: Modo Portátil (pendrive, user-mode, zero admin, boot_stage0.py com
  crypto AES-GCM, wipe automático pós-sessão)
- P6: Knowledge Vault híbrido (Markdown local + sync Supabase criptografado,
  tool knowledge_note, tool sync_memory, comando de voz)
- Prompt Supremo: personalidade JARVIS validada (1ª pessoa, PT-BR, brevidade)
- Auditoria Estrutural: todos os itens A1-A8, M1-M6, B1-B4 aplicados
- Dashboard web: REMOVIDO (não utilizado, reduziu superfície de ataque)
- Modo Texto: fallback automático quando sem microfone (PC da faculdade)
- Efeito Coulson: ntfy.sh SSE, latência <200ms, payload criptografado

### DECISÕES ARQUITETURAIS FECHADAS (não reabrir)
- Gemini exclusivo para voz ao vivo — zero chamadas de texto
- Groq (gpt-oss-120b/20b) primário, openrouter/free fallback
- Sync Supabase: manual por comando de voz, não automático contínuo
- Kokoro TTS: descartado (latência incompatível com Gemini Live nativo)
- Ollama: arquivado (conflita com CPU de jogos)
- Chaves de API: nunca em nuvem, nunca em repositório

### PENDENTE
- P7b: Sync pendrive↔PC principal via Supabase (depende de P6, pronto para iniciar)
- Evolution API (WhatsApp envio por voz): aprovado, não implementado
- E-mail IMAP leitura + SMTP envio: aprovado, não implementado
- Spotify API: aprovado, não implementado
- Google Calendar: aprovado, não implementado
- Modos de operação (Sentinela/Foco/Estudo/Jogos): planejado
- core/persona.py: consolidar identidade fragmentada entre prompt.txt e _build_config
- Testes unitários: 26 testes criados em tests/test_jarvis_core.py

### REGRAS DE OURO
- PT-BR estrito, tratamento "Senhor" (nunca "sir"/"efendim")
- CPU/GPU mínimo durante jogos
- Edições cirúrgicas (antes/depois), nunca arquivo completo
- Sistema 100% gratuito — zero API paga, zero cartão cadastrado
