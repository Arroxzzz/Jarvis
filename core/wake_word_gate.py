"""Portão de wake word usando openWakeWord."""
from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np
from core.paths import get_base_dir


def _wake_cfg() -> dict:
    """Ajustes do wake word em config/api_keys.json (todos opcionais)."""
    from config import get_config
    cfg = get_config()
    return {
        "enabled": bool(cfg.get("wake_word_enabled", False)),
        "model": str(cfg.get("wake_word_model", "hey_jarvis")),
        "threshold": float(cfg.get("wake_word_threshold", 0.5)),
        "grace": float(cfg.get("wake_word_grace_sec", 20)),
        "buffer": float(cfg.get("wake_word_buffer_sec", 8)),
        "vad": float(cfg.get("wake_word_vad", 0.0)),
    }


def _wake_word_enabled() -> bool:
    """Wake word é OPT-IN: desligado por padrão (ver .ai/CURRENT_TASK.md)."""
    return _wake_cfg()["enabled"]


def _resolve_model(spec: str) -> str:
    """'hey_jarvis' (pré-treinado) ou caminho de um .onnx próprio (relativo à raiz do projeto)."""
    if spec.lower().endswith((".onnx", ".tflite")):
        p = Path(spec)
        return str(p if p.is_absolute() else get_base_dir() / p)
    return spec


_LOGGER = logging.getLogger(__name__)
_SAMPLE_RATE = 16000
_BYTES_PER_SAMPLE = 2
_FRAME_SAMPLES = 1280
_FRAME_BYTES = _FRAME_SAMPLES * _BYTES_PER_SAMPLE


class WakeWordGate:
    def __init__(
        self,
        rolling_seconds: float | None = None,
        threshold: float | None = None,
        grace_seconds: float | None = None,
    ):
        import concurrent.futures

        cfg = _wake_cfg()
        rolling_seconds = cfg["buffer"] if rolling_seconds is None else rolling_seconds
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._available = False
        self._model = None
        self._model_name = cfg["model"]
        self.load_error: str | None = None
        self.detections = 0
        self.threshold = cfg["threshold"] if threshold is None else threshold
        self.grace_seconds = cfg["grace"] if grace_seconds is None else grace_seconds
        self._max_buffer_bytes = max(
            _FRAME_BYTES,
            int(rolling_seconds * _SAMPLE_RATE * _BYTES_PER_SAMPLE),
        )
        self._rolling_buffer = bytearray()
        self._frame_buffer = bytearray()
        self._gate_open = False
        self._grace_until = 0.0

        if not cfg["enabled"]:
            print(
                "[WakeGate] Desativado por configuração (padrão atual) — o microfone não exige "
                "palavra de ativação. Defina 'wake_word_enabled': true em config/api_keys.json "
                "depois de validar a detecção para o seu uso (ver .ai/CURRENT_TASK.md)."
            )
            return

        kwargs = {"wakeword_models": [_resolve_model(cfg["model"])], "inference_framework": "onnx"}
        if cfg["vad"] > 0:
            kwargs["vad_threshold"] = cfg["vad"]
        try:
            import openwakeword
            from openwakeword.model import Model

            try:
                self._model = Model(**kwargs)
            except Exception:
                openwakeword.utils.download_models()
                self._model = Model(**kwargs)
            self._available = True
            print(
                f"[WakeGate] Ativo: modelo={cfg['model']} limiar={self.threshold} "
                f"graça={self.grace_seconds:.0f}s buffer={rolling_seconds:.0f}s"
            )
        except Exception as exc:
            self.load_error = str(exc)
            _LOGGER.warning(
                "openWakeWord indisponível; portão permanecerá aberto: %s",
                exc,
            )

    def status_line(self) -> str:
        """Linha para o painel: o Senhor precisa SABER se o microfone está aberto ou protegido."""
        if self._available:
            return (f"SYS: Wake word ATIVO — modelo {self._model_name}, limiar {self.threshold}, "
                    f"janela pós-resposta {self.grace_seconds:.0f}s. O microfone só envia áudio após a palavra.")
        if self.load_error:
            return f"SYS: ⚠️ Wake word FALHOU ao carregar ({self.load_error[:80]}) — microfone ABERTO."
        return "SYS: Wake word desligado — microfone sempre aberto."

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
                score = max(prediction.values(), default=0.0)
                if score > self.threshold:
                    self.detections += 1
                    print(f"[WakeGate] ✅ detectado (score={score:.2f}, total={self.detections})")
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
