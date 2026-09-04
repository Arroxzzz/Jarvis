# CURRENT_TASK — PRÓXIMA AÇÃO: P3 (Segurança Crítica)

## Contexto
P0, P1 e P2 validados em campo e consolidados em PROJECT_STATE.md.
Gemini isolado para voz confirmado. Groq→OpenRouter operacional.

## Pendência aberta antes de P3 (decisão do Senhor Paulo necessária)
`file_processor.py::_process_audio::transcribe` ainda usa Gemini —
único ponto de texto/multimodal fora da regra "Gemini só para voz".
Decidir: manter exceção documentada, ou migrar para Whisper local
(zero custo, mas consome CPU — avaliar frente à regra de jogos).

## PRÓXIMA AÇÃO IMEDIATA — Fase P3
1. `dashboard/server.py`: AES-256-CBC → AES-GCM; derivação de chave
   SHA256 puro → PBKDF2 (lib já disponível em crypto-js.min.js).
2. `actions/desktop.py::_build_sandbox`: remover `pyautogui` do sandbox
   de código gerado por IA (hoje é RCE de fato via automação de teclado).
3. `actions/computer_control.py::user_data`: allowlist de campos
   permitidos (hoje qualquer chave de `identity` é exfiltrável).

## Depois de P3 — ordem definida
1. P6 — Memória em Nuvem (Supabase): tabela `memory_entries`,
   substituir backend de `memory/memory_manager.py` mantendo API pública.
2. P7 — Modo Portátil (Pen Drive): resolver `Path.home()` espalhado,
   modo de execução sem rastro no PC anfitrião, dependente de P6 pronto
   para não perder memória de sessão em caso de perda do pen drive.
3. P4 — Silero VAD (filtro de áudio local).

## Decisões já fechadas — não reabrir sem novo motivo
- Ollama (P5): arquivado.
- Gemini exclusivo para voz: regra permanente do projeto.
- Groq primário, OpenRouter fallback: cadeia oficial de resiliência de texto.
- Código-fonte: repositório Git privado remoto é o backup primário.
- Chaves de API: nunca em repositório, nunca embutidas em pen drive portátil.
