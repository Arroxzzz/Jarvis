"""Portão de wake word usando openWakeWord."""
from __future__ import annotations

import logging
import time

import numpy as np


def _wake_word_enabled() -> bool:
    """Wake word é OPT-IN: desligado por padrão. O modelo 'hey_jarvis' do openWakeWord é treinado
    em inglês e não detecta 'Jarvis' com fonética portuguesa de forma confiável — ligar isso sem
    calibrar deixa o microfone surdo depois da janela de graça. Ative só após validar a detecção."""
    from config import get_config
    return bool(get_config().get("wake_word_enabled", False))


_LOGGER = logging.getLogger(__name__)
_SAMPLE_RATE = 16000
_BYTES_PER_SAMPLE = 2
_FRAME_SAMPLES = 1280
_FRAME_BYTES = _FRAME_SAMPLES * _BYTES_PER_SAMPLE


class WakeWordGate:
    def __init__(
        self,
        rolling_seconds: float = 8.0,
        threshold: float = 0.5,
        grace_seconds: float = 12.0,
    ):
        import concurrent.futures

        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._available = False
        self._model = None
        self.threshold = threshold
        self.grace_seconds = grace_seconds
        self._max_buffer_bytes = max(
            _FRAME_BYTES,
            int(rolling_seconds * _SAMPLE_RATE * _BYTES_PER_SAMPLE),
        )
        self._rolling_buffer = bytearray()
        self._frame_buffer = bytearray()
        self._gate_open = False
        self._grace_until = 0.0

        if not _wake_word_enabled():
            print(
                "[WakeGate] Desativado por configuração (padrão atual) — o microfone não exige "
                "palavra de ativação. Defina 'wake_word_enabled': true em config/api_keys.json "
                "depois de validar a detecção para o seu uso (ver .ai/CURRENT_TASK.md)."
            )
            return

        try:
            import openwakeword
            from openwakeword.model import Model

            try:
                self._model = Model(
                    wakeword_models=["hey_jarvis"],
                    inference_framework="onnx",
                )
            except Exception:
                openwakeword.utils.download_models()
                self._model = Model(
                    wakeword_models=["hey_jarvis"],
                    inference_framework="onnx",
                )
            self._available = True
        except Exception as exc:
            _LOGGER.warning(
                "openWakeWord indisponível; portão permanecerá aberto: %s",
                exc,
            )

    async def feed_async(self, chunk: bytes, loop) -> bytes | None:
        return await loop.run_in_executor(self._executor, self.feed, chunk)

    def feed(self, chunk: bytes) -> bytes | None:
        try:
            if not self._available:
                return chunk

            self._rolling_buffer.extend(chunk)
            if len(self._rolling_buffer) > self._max_buffer_bytes:
                del self._rolling_buffer[
                    :len(self._rolling_buffer) - self._max_buffer_bytes
                ]

            now = time.monotonic()
            if self._gate_open or now < self._grace_until:
                return chunk

            self._frame_buffer.extend(chunk)
            while len(self._frame_buffer) >= _FRAME_BYTES:
                frame_bytes = self._frame_buffer[:_FRAME_BYTES]
                del self._frame_buffer[:_FRAME_BYTES]
                frame = np.frombuffer(frame_bytes, dtype=np.int16)
                prediction = self._model.predict(frame)
                if prediction.get("hey_jarvis", 0) > self.threshold:
                    self._gate_open = True
                    captured = bytes(self._rolling_buffer)
                    self._rolling_buffer.clear()
                    return captured
            return None
        except Exception as exc:
            self._available = False
            self._gate_open = True
            _LOGGER.warning(
                "Falha no portão openWakeWord; áudio será repassado: %s",
                exc,
            )
            return chunk

    def close_gate(self) -> None:
        try:
            self._gate_open = False
            self._grace_until = time.monotonic() + self.grace_seconds
        except Exception as exc:
            self._gate_open = True
            _LOGGER.warning(
                "Falha ao fechar o portão openWakeWord; portão aberto: %s",
                exc,
            )
