# PROJECT_STATE — JARVIS MARK LI — HANDOFF SPRINT 5 (2026-09-02)

## ⚠️ LEIA ISTO PRIMEIRO — Handoff para a próxima sessão do Claude

Este handoff existe porque a sessão anterior atingiu limite de contexto no
meio da Sprint 5. TODO o diagnóstico abaixo já foi validado por testes reais
do Senhor Paulo — não é suposição, é fato observado em log. Não redescubra
o que já está aqui; execute o Plano de Ação na ordem especificada.

---

## RESUMO EXECUTIVO DA SPRINT 5

**Objetivo original:** latência de resposta de voz entre 1-3s.
**Resultado:** ALCANÇADO E CONFIRMADO — 1-2s, com 78+ chunks de áudio
enviados continuamente e sem perda de frame. O objetivo-fim da sprint foi
cumprido; o que resta é estabilização de concorrência, não performance.

**Efeito colateral do trabalho:** trocar o model ID Live expôs uma cadeia de
3 bugs pré-existentes e adormecidos (nunca testados antes desta sprint).
Cada correção revelou o próximo, na seguinte ordem real de causas:

1. `LIVE_MODEL` fixo apontava para um ID inexistente/desatualizado →
   `client.aio.live.connect()` falhava com 1007/1008.
2. O handler de erro tratava QUALQUER 1007/1008 como "API key inválida" →
   resetava config e abria tela de setup, mascarando a causa real (1).
3. Resolvido (1)+(2) → surgiu erro novo: `send_realtime_input(media=...)`
   usa parâmetro descontinuado pelo servidor Google ("media_chunks is
   deprecated. Use audio, video, or text instead").
4. Resolvido (3) → surgiu erro novo: `mime_type="audio/pcm"` sem sample
   rate explícito era rejeitado ("1007 Request contains an invalid
   argument") ao usar o campo tipado `audio=types.Blob(...)`. Corrigido
   para `audio/pcm;rate=16000`.
5. Resolvido (4) → restava um deadlock de lógica (não de protocolo): gate
   `turn_pending` em `_listen_audio::callback` silenciava o mic sempre que
   `_turn_done_event` ficasse preso por uma conexão caída no meio de uma
   resposta. Removido — o VAD do próprio Gemini Live já lida com isso.
6. Resolvido (5) → MIC E LATÊNCIA CONFIRMADOS FUNCIONANDO (1-2s, 78+ chunks).
7. Bug NOVO e ainda ABERTO nesta sessão: qualquer `send_client_content` ou
   `send_tool_response` que colida no tempo com outra chamada ao `session`
   derruba o socket com `1007 Request contains an invalid argument`.
   Confirmado em DOIS cenários distintos e independentes:
     - ESC durante uma tool ativa (`interrupt()` chamava `speak()` antes do
       `send_tool_response` da task cancelada ser enviado).
     - Texto digitado na UI (`_on_text_command`) durante outra atividade
       de sessão em andamento.
   **Diagnóstico consolidado:** não é mais um problema de payload/schema —
   é FALTA DE SERIALIZAÇÃO no acesso ao objeto `session` do SDK
   `google-genai`. Múltiplos pontos do código (`speak`, `interrupt`,
   `_on_text_command`, `plugin_say`, o watchdog, `_receive_audio`) podem
   chamar métodos do `session` a qualquer momento, de threads/tasks
   diferentes, sem nenhum mutex/lock protegendo o WebSocket. Ver ESPECIFICAÇÃO
   DO PONTO 0 abaixo.

**Sintomas colaterais ainda não resolvidos (são CONSEQUÊNCIA do item 7, não
bugs novos e independentes):**
   - Saudação de boot não é falada. Causa provável: `_send_boot_greeting()`
     colide com outra chamada concorrente ao `session` durante os primeiros
     segundos de conexão (watchdog, dashboard, etc.) e é vítima do mesmo 1007.
     Correção anterior (`_boot_greeted` resetado quando `session_log` vazio)
     já foi aplicada e ajuda no caso de "conexão caiu antes de qualquer
     conversa", mas NÃO resolve o caso de colisão em conexão que sobrevive.
   - ACTIVITY LOG poluído com tracebacks/erros crus da API — não é bug de
     lógica, é falta de sanitização de log (ver Ponto 2 do plano).

---

## ANÁLISE DE VIABILIDADE DOS 4 PONTOS DISCUTIDOS (decisão já tomada)

### Ponto 1 — Seleção de dispositivos de áudio (mic/output) na UI
**Decisão: FAZER, prioridade BAIXA (depois da estabilização).**
Overlay estilo `SetupOverlay`/`CustomizeOverlay` em `ui.py`, salva
`input_device_index`/`output_device_index` em `config/api_keys.json`,
aplicado via `sd.InputStream(device=idx, ...)` / `sd.RawOutputStream(device=idx, ...)`
em `main.py`. NÃO fazer hot-swap em runtime na v1 — só seleção no boot,
aplicada no próximo restart do stream (que já acontece a cada reconexão
do `TaskGroup` em `JarvisLive.run()`). Complexidade real: baixa.

### Ponto 2 — Sanitização de logs (tracebacks → jarvis.log, não para UI)
**Decisão: FAZER, prioridade MÉDIA — logo após o Ponto 0.**
Fazer em duas camadas:
1. Imediata: em `main.py`, trocar prints crus de traceback/erro de SDK que
   hoje vazam para `self.ui.write_log()` por `logging.exception()` gravando
   em arquivo `jarvis.log`. O vazamento observado vem do
   `except BaseException as e:` no loop de reconexão de `JarvisLive.run()`,
   que hoje escreve `err_str` cru na UI via `self.ui.write_log(...)`.
2. Depois: módulo `core/logger.py` com `logging.RotatingFileHandler` para
   arquivo + handler customizado que só repassa para `LogWidget` mensagens
   curadas (prefixo `SYS:`/`You:`/nome do assistente). NÃO migrar todos os
   `print()` de `actions/*.py` de uma vez — fora de escopo, baixo retorno
   imediato; os tracebacks visíveis até agora vêm 100% de `main.py`.

### Ponto 3 — Model ID Live fixo vs. descoberta dinâmica
**Decisão: MANTER a descoberta dinâmica com cache. NÃO fixar hardcoded.**
Fixar reintroduziria exatamente o bug de origem desta sprint (Sprint 4 já
fixou um ID que não existia). O mecanismo atual (`_resolve_live_model()`,
`_discover_live_models()`, `_current_live_model()`, `_advance_live_model()`)
já se comporta como "modelo fixo" no dia a dia — 1º boot descobre e testa
candidatos, grava o vencedor em `config/api_keys.json["live_model_id_cache"]`;
boots seguintes usam o cache DIRETO, sem round-trip a `models.list()`. Só
refaz a descoberta se o candidato em cache falhar (1007/1008). Ou seja:
já temos estabilidade de hardcode COM auto-recuperação a mudanças futuras
de catálogo da Google. Nenhuma ação de código necessária neste ponto —
está correto como está.

### Ponto 4 — Saudação automática de boot
**Decisão: NÃO tratar isoladamente — é sintoma do Ponto 0.**
Assim que a serialização do `session` (Ponto 0) estiver implementada, a
saudação deve voltar a funcionar sem nenhuma mudança de código adicional
nela mesma. Se persistir falhando DEPOIS do Ponto 0 resolvido, aí sim
investigar `_send_boot_greeting()` isoladamente.

---

## ⭐ ESPECIFICAÇÃO DO PONTO 0 — LOCK DE SERIALIZAÇÃO DO SESSION (PRIORIDADE ABSOLUTA)

Este é o único item de código pendente com prioridade máxima. Especificação
completa para a próxima sessão implementar sem precisar perguntar nada:

### Problema exato
`google.genai.live.AsyncSession` (o objeto `self.session` em `JarvisLive`)
não é thread-safe nem coroutine-safe para chamadas concorrentes de
`send_client_content()` / `send_tool_response()` / `send_realtime_input()`.
Hoje esses métodos são chamados de múltiplos pontos sem nenhuma exclusão
mútua:
  - `_send_realtime()` (task contínua, chama `send_realtime_input` em loop)
  - `_receive_audio()` (chama `send_tool_response` após tool calls, e
    `send_client_content` para injeção de visão/imagem)
  - `speak()` (chamado de qualquer lugar, inclusive de threads via
    `asyncio.run_coroutine_threadsafe`, por `interrupt()`, `plugin_say()`,
    `speak_error()`)
  - `_on_text_command()` (thread da UI Qt, via `run_coroutine_threadsafe`)
  - `_send_startup_briefing()`, `_send_boot_greeting()`,
    `_run_system_monitor()`, `_run_background_monitor()`,
    `_run_proactive_mode()`, `_process_dashboard_commands()` — todas
    background tasks que também chamam `send_client_content`.

Quando duas dessas chamadas colidem no tempo (ex: `send_tool_response`
ainda em voo quando `speak()` dispara um `send_client_content` novo), o
servidor Live rejeita com `1007 Request contains an invalid argument` e
derruba o WebSocket inteiro — não é um erro recuperável por chunk, mata a
sessão inteira e força reconexão completa.

### Solução especificada
1. Adicionar `self._session_lock = asyncio.Lock()` em `JarvisLive.__init__`.
2. Criar um método único de saída para conteúdo de cliente, algo como:
async def _safe_send_content(self, parts: list, turn_complete: bool = True) -> None:
if not self.session:
return
async with self._session_lock:
await self.session.send_client_content(
turns={"parts": parts}, turn_complete=turn_complete
)
3. Método análogo para `send_tool_response` (mesmo lock).
4. `send_realtime_input` (áudio contínuo do mic) é caso especial: NÃO deve
   competir pelo mesmo lock que `send_client_content`/`send_tool_response`
   com espera bloqueante longa, porque é chamado em alta frequência (a cada
   chunk de ~64ms) e uma tool call pode demorar segundos. Duas opções a
   avaliar na implementação:
   a) Usar o MESMO lock, mas garantir que nenhuma seção crítica de
      `send_client_content`/`send_tool_response` segure o lock por muito
      tempo (elas são chamadas únicas, não deveriam demorar).
   b) Lock separado apenas para conteúdo "de turno" (`send_client_content`
      + `send_tool_response`), deixando `send_realtime_input` livre — o
      áudio realtime não conflita com texto de turno no protocolo real,
      o conflito observado foi especificamente entre chamadas de TURNO
      concorrentes entre si (tool_response vs. speak vs. texto digitado).
   **Recomendação da sessão anterior: opção (b)** — é mais cirúrgica e
   não arrisca introduzir latência no áudio, que é o requisito #1 do
   projeto (1-3s) e já está funcionando.
5. Substituir TODOS os pontos de chamada direta a
   `self.session.send_client_content(...)` e
   `self.session.send_tool_response(...)` espalhados por `main.py` para
   passar pelo(s) método(s) seguro(s) acima. Locais confirmados que
   precisam ser migrados (buscar por `send_client_content` e
   `send_tool_response` em `main.py`):
   - `plugin_say()`
   - `_on_text_command()`
   - `speak()`
   - dentro de `_execute_tool()` (branch `shutdown_jarvis`)
   - dentro de `_receive_audio()` (injeção de visão + fluxo de tool_response)
   - `_send_startup_briefing()` (fase 1 e fase 2)
   - `_send_boot_greeting()`
   - `_run_system_monitor()`
   - `_run_background_monitor()`
   - `_run_proactive_mode()`
   - `_process_dashboard_commands()`
6. Consequência esperada: ESC durante tool ativa, texto digitado durante
   qualquer atividade de sessão, e saudação de boot devem passar a
   funcionar sem 1007, SEM precisar de nenhum patch adicional específico
   para cada um — todos são o mesmo bug de concorrência.

### Ordem de implementação sugerida
1. Lock + método `_safe_send_content` / `_safe_send_tool_response`.
2. Migrar `speak()`, `interrupt()` (via `_pending_cancel_phrase`, já
   implementado em rodada anterior — só precisa passar a usar o método
   seguro), `_on_text_command()`.
3. Migrar as background tasks (system_monitor, background_monitor,
   proactive_mode, dashboard_commands, briefing, boot_greeting).
4. Migrar o fluxo de tool_response dentro de `_receive_audio()`.
5. Testar: ESC durante tool ativa, texto digitado durante fala, boot do
   zero (saudação).

---

## PLANO DE AÇÃO SEQUENCIAL (ordem definitiva, não reordenar)

1. **PONTO 0 — Lock de serialização do `session`** (especificação completa
   acima). Resolve ESC, texto digitado, e saudação de boot como efeito
   colateral — são todos sintomas da mesma causa raiz.
2. **Sanitização de logs** (Ponto 2, camada 1 mínima em `main.py` primeiro).
   Necessário para as próximas rodadas de teste não perderem sinal em meio
   a ruído de traceback.
3. **Menu de seleção de mic/audio na UI** (Ponto 1). Só depois de tudo
   acima estabilizado — é melhoria de UX, não bugfix.
4. Ponto 3 (model ID): NENHUMA AÇÃO — já está correto como está.

---

## Funcionalidades Operacionais Estáveis (não tocar sem necessidade)
- Gemini Live API conecta com sucesso, latência de voz 1-2s CONFIRMADA.
- Descoberta dinâmica de model Live + cache (`_resolve_live_model` e afins)
  — funcionando corretamente, não fixar hardcoded (ver Ponto 3).
- Captura de microfone (`_listen_audio`) — CORRIGIDA e confirmada (78+
  chunks contínuos), gate `turn_pending` removido, mime_type com rate
  explícito (`audio/pcm;rate=16000`).
- Sistema de plugins (auto-discovery em `plugins/`, isolamento de crash).
- HUD PyQt6, Dashboard remoto (FastAPI + AES-256 + QR pairing).
- File processor multi-formato, Browser control (Playwright).
- Memory manager (long_term.json).
- Identidade PT-BR fixa, hotkey F4 global, Modo Fantasma/Bandeja.
- OpenRouter gratuito para deep_reasoning.

## Regras de Ouro (inalteradas)
- PT-BR estrito em toda saída falada/escrita do assistente.
- Tratamento exclusivo: "Senhor" (nunca "sir", nunca "efendim").
- CPU/GPU mínimo durante jogos — HUD e métricas pausam ao minimizar.
- Toda entrega de código é cirúrgica (antes/depois), nunca arquivo completo.
- Zero saudações/preâmbulos em respostas técnicas.
- **NOVA REGRA (Sprint 5): qualquer erro 1007/1008 NUNCA deve ser tratado
  como prova de API key inválida.** A causa real está sempre na mensagem
  de texto associada (`err_str`) — deve ser lida e diagnosticada, nunca
  assumida. Ver post-mortem completo acima.
- **NOVA REGRA (Sprint 5): NUNCA chamar `self.session.send_client_content`
  ou `send_tool_response` diretamente fora dos métodos seguros do Ponto 0**,
  uma vez implementados — todo acesso ao `session` para envio de conteúdo
  de turno deve passar pelo lock.