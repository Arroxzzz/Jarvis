# JARVIS MARK LI — ARQUITETURA OFICIAL

## CAMADAS DO SISTEMA

┌─────────────────────────────────────────────────────────────┐
│  INTERFACE (ui.py — PyQt6)                                  │
│  HUD + mic + interrupt + text input + log                   │
└────────────────────┬────────────────────────────────────────┘
│
┌────────────────────▼────────────────────────────────────────┐
│  NÚCLEO (main.py — JarvisLive)                              │
│  Gemini Live (voz nativa) + asyncio TaskGroup               │
│  _safe_send_content / _safe_send_tool_response (Ponto 0)    │
│  _turn_watchdog / _bg_tasks_pending                         │
└──┬─────────┬──────────┬──────────┬────────────┬────────────┘
│         │          │          │            │
┌──▼──┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌────▼────┐
│TOOLS│  │MEMORY │  │CLOUD  │  │NOTIFY │  │PORTABLE │
└──┬──┘  └───┬───┘  └───┬───┘  └───┬───┘  └────┬────┘
│         │          │          │            │
│    long_term.json  │     ntfy.sh SSE  boot_stage0.py
│    knowledge/*.md  │     (Coulson)    project.enc
│                Supabase               AES-GCM
│                Storage
│                (sync criptografado)
│
├── Groq API (gpt-oss-120b/20b) — código/texto/pesquisa
└── OpenRouter free (fallback)

## FLUXO DE VOZ

Microfone → PyAudio chunks → Gemini Live (WebSocket)

→ tokens de voz → PyAudio playback

→ (paralelo) tool calls → actions/*.py

→ Groq/OpenRouter (texto)

→ resultado → Gemini Live

## FLUXO DE TEXTO (sem microfone)

ui.py TextInput → _on_text_command → _safe_send_content

→ Gemini Live → resposta de voz → playback

## FLUXO COULSON (notificações do celular)

MacroDroid → POST cifrado → ntfy.sh

ntfy.sh → SSE → listen_coulson (asyncio task)

→ decrypt → _format_message → speak_fn

→ JARVIS fala instantaneamente (<200ms)

## FLUXO PORTÁTIL (pendrive)

_INICIAR_JARVIS.bat

→ boot_stage0.py (texto puro no pendrive)

→ PBKDF2(senha) → AES-GCM decrypt

→ extrai project.enc → session_dir temporária

→ pythonw.exe main.py (sem console)

→ [sessão ativa]

→ encerra → secure_wipe(session_dir)

## FLUXO DE SYNC

"Jarvis, sincronize" → sync_memory tool

→ sync_manager.sync_all()

→ _resolve_password(cfg)  ← derivada de supabase_service_key

→ por arquivo: hash local vs hash remoto (sync_state.json)

→ só transfere arquivos modificados

→ upload: encrypt_bytes → Supabase Storage PUT

→ download: Supabase GET → decrypt_bytes → write local

## RESILIÊNCIA DE TEXTO (Groq → OpenRouter)

resilient_text_call(prompt, task_type)

→ GROQ_MODELS[task_type] (gpt-oss-120b, gpt-oss-20b)

→ [falha] → FREE_MODELS[task_type] (openrouter/free)

→ [falha total] → mensagem de erro ao usuário

## ARQUIVOS CRÍTICOS

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Orquestração, Gemini Live, tool dispatch |
| `core/prompt.txt` | Personalidade, regras, identidade |
| `core/llm_client.py` | Resiliência Groq→OpenRouter |
| `core/crypto_vault.py` | AES-GCM+PBKDF2, encrypt/decrypt |
| `core/sync_manager.py` | Sync Supabase por arquivo |
| `core/knowledge_vault.py` | Notas Markdown locais |
| `core/paths.py` | Paths portáteis (get_home_dir) |
| `actions/coulson_listener.py` | ntfy.sh SSE, Efeito Coulson |
| `boot_stage0.py` | Boot portátil, decrypt, wipe |
| `memory/long_term.json` | Memória estruturada (identity/prefs) |
| `knowledge/*.md` | Notas de conhecimento |
| `config/api_keys.json` | Chaves (local only, nunca em nuvem) |

## SEGURANÇA

- `api_keys.json`: local only, `.gitignore`, nunca em nuvem
- Pendrive: AES-256-GCM + PBKDF2 200k iter, wipe pós-sessão
- Supabase: blobs cifrados (nuvem cega), RLS no inbox
- ntfy.sh: payload cifrado (AES-GCM, chave derivada localmente)
- Dashboard web: **REMOVIDO** (superfície de ataque eliminada)
- Sandbox desktop.py: sem pyautogui, shutil com allowlist

## MODELOS EM USO

| Uso | Modelo | Provider |
|---|---|---|
| Voz ao vivo | gemini-2.5-flash-native-audio-latest | Google (Live API) |
| Código | openai/gpt-oss-120b | Groq |
| Geral/pesquisa | openai/gpt-oss-20b + groq/compound-mini | Groq |
| Fallback total | openrouter/free | OpenRouter |