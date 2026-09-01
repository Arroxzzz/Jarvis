"""
core/hotkeys.py — Atalho global de teclado para mutar/desmutar o microfone.

Usa pynput (hook de teclado em nível de SO) para funcionar mesmo com a janela
do JARVIS sem foco — inclusive com um jogo em tela cheia. Roda numa thread
própria do pynput; nunca toca widgets Qt diretamente (usa o método thread-safe
JarvisUI.toggle_mic_mute(), que emite um pyqtSignal — o mesmo padrão já usado
no projeto para _camera_sig/_clipboard_sig).

Regra de produto: F4 SÓ corta a escuta do microfone. NUNCA interrompe uma fala
do JARVIS em andamento — isso continua sendo papel exclusivo do Escape/interrupt().
"""
from __future__ import annotations

try:
    from pynput import keyboard
    _PYNPUT_OK = True
except ImportError:
    _PYNPUT_OK = False


def _beep(freq: float, duration: float = 0.12, volume: float = 0.25) -> None:
    """Bipe curto e local — zero custo de rede/API, só pra confirmar a ação."""
    try:
        import numpy as np
        import sounddevice as sd
        sr = 24000
        t  = np.linspace(0, duration, int(sr * duration), False)
        tone = (volume * np.sin(2 * np.pi * freq * t)).astype(np.float32)
        sd.play(tone, sr)   # não-bloqueante
    except Exception as e:
        print(f"[Hotkeys] Beep failed (non-fatal): {e}")


class GlobalHotkeys:
    """F4 = mutar/desmutar o microfone, funciona com a janela sem foco."""

    def __init__(self, ui):
        self._ui = ui
        self._listener = None

    def start(self) -> bool:
        if not _PYNPUT_OK:
            print(
                "[Hotkeys] pynput não instalado — atalho global F4 desativado. "
                "Rode: pip install pynput  (o botão de mute na janela continua funcionando)"
            )
            return False

        def _on_press(key) -> None:
            if key != keyboard.Key.f4:
                return
            try:
                was_muted = self._ui.muted
                self._ui.toggle_mic_mute()
                # Tom agudo = microfone ficando ATIVO; tom grave = MUTADO.
                _beep(990 if was_muted else 660)
            except Exception as e:
                print(f"[Hotkeys] F4 handler error: {e}")

        try:
            self._listener = keyboard.Listener(on_press=_on_press)
            self._listener.daemon = True
            self._listener.start()
            print("[Hotkeys] Atalho global F4 (mutar microfone) ativo.")
            return True
        except Exception as e:
            print(f"[Hotkeys] Could not start global listener: {e}")
            return False

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None