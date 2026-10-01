"""Mede o wake word com a SUA voz (feche o JARVIS antes: o microfone é compartilhado).
  python tools/wake_eval.py record pos 30        # 30 x "Jarvis" (2 s cada)
  python tools/wake_eval.py record pos_hey 30    # 30 x "Hey Jarvis" (2 s cada)
  python tools/wake_eval.py record neg 30        # 30 x fala normal SEM a palavra (3 s cada)
  python tools/wake_eval.py record ambient 600   # 600 s de som ambiente (jogo/YouTube/TV)
  python tools/wake_eval.py eval [modelo]        # modelo: hey_jarvis (padrão) ou caminho de um .onnx
Os .wav ficam em wake_samples/ (fora do git)."""
import sys
import time
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "wake_samples"
SR = 16000
FRAME = 1280                      # 80 ms
PHRASES = {"pos": "Jarvis", "pos_hey": "Hey Jarvis"}
THRESHOLDS = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
REFRACTORY = 25                   # quadros (~2 s): detecções mais próximas contam como um evento só


def _record(seconds: float) -> np.ndarray:
    import sounddevice as sd
    data = sd.rec(int(seconds * SR), samplerate=SR, channels=1, dtype="int16")
    sd.wait()
    return data[:, 0]


def _save(path: Path, pcm: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.astype(np.int16).tobytes())


def _load(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)


def _scores(model, pcm: np.ndarray) -> list[float]:
    """Score por quadro de 80 ms (com 1 s de silêncio antes/depois para limpar o estado do modelo)."""
    if hasattr(model, "reset"):
        model.reset()
    pad = np.zeros(SR, dtype=np.int16)
    audio = np.concatenate([pad, pcm.astype(np.int16), pad])
    return [
        max(model.predict(audio[i:i + FRAME]).values(), default=0.0)
        for i in range(0, len(audio) - FRAME + 1, FRAME)
    ]


def _events(scores: list[float], thr: float) -> int:
    n, last = 0, -REFRACTORY
    for i, s in enumerate(scores):
        if s > thr and i - last >= REFRACTORY:
            n += 1
            last = i
    return n


def cmd_record(kind: str, n: int) -> None:
    if kind == "ambient":
        print(f"Gravando {n}s de som ambiente. Deixe tocando o que costuma rodar no PC (jogo, YouTube, TV).")
        _save(SAMPLES / "ambient" / f"amb_{int(time.time())}.wav", _record(n))
        print("OK")
        return
    if kind in PHRASES:
        secs, prompt = 2.0, f'Diga "{PHRASES[kind]}" (varie tom, velocidade e distância)'
    elif kind == "neg":
        secs, prompt = 3.0, "Fale uma frase qualquer SEM a palavra Jarvis"
    else:
        sys.exit(f"Tipo desconhecido: {kind}")
    start = len(list((SAMPLES / kind).glob("*.wav")))
    for i in range(n):
        input(f"[{i + 1}/{n}] {prompt} — ENTER e fale: ")
        _save(SAMPLES / kind / f"{kind}_{start + i:03d}.wav", _record(secs))
    print("OK")


def cmd_eval(spec: str) -> None:
    from openwakeword.model import Model
    if spec.lower().endswith(".onnx"):
        p = Path(spec)
        spec = str(p if p.is_absolute() else ROOT / p)
    try:
        model = Model(wakeword_models=[spec], inference_framework="onnx")
    except Exception:
        import openwakeword
        openwakeword.utils.download_models()
        model = Model(wakeword_models=[spec], inference_framework="onnx")

    def peaks(folder: Path) -> list[float]:
        return [max(_scores(model, _load(p)), default=0.0) for p in sorted(folder.glob("*.wav"))]

    pos_sets = {d.name: peaks(d) for d in sorted(SAMPLES.glob("pos*")) if d.is_dir()}
    neg = peaks(SAMPLES / "neg")
    amb = [_scores(model, _load(p)) for p in sorted((SAMPLES / "ambient").glob("*.wav"))]
    hours = sum(len(s) * FRAME / SR for s in amb) / 3600
    print(f"\nModelo: {spec}\nfala normal: {len(neg)} clipes | ambiente: {hours * 60:.1f} min")

    def fph(thr: float) -> float:
        return sum(_events(sc, thr) for sc in amb) / hours if hours else float("nan")

    for name, pos in pos_sets.items():
        med = float(np.median(pos)) if pos else 0.0
        print(f"\n== {name} ({len(pos)} clipes) — menor score {min(pos, default=0):.2f}, mediana {med:.2f}")
        for thr in THRESHOLDS:
            recall = sum(s > thr for s in pos) / max(len(pos), 1)
            fp_neg = sum(s > thr for s in neg)
            print(f"  limiar {thr:.1f}: acerto {recall:4.0%} | falsos em fala normal {fp_neg}/{len(neg)}"
                  f" | falsos/hora no ambiente {fph(thr):.1f}")
        ok = [t for t in THRESHOLDS if sum(s > t for s in neg) == 0 and (not hours or fph(t) <= 1)]
        if ok:
            best = ok[0]
            print(f"  → limiar sugerido: {best:.1f} (acerto {sum(s > best for s in pos) / max(len(pos), 1):.0%})")
        else:
            print("  → nenhum limiar atende (0 falsos em fala normal e ≤ 1 falso/hora)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "record":
        cmd_record(a[1], int(a[2]))
    elif a and a[0] == "eval":
        cmd_eval(a[1] if len(a) > 1 else "hey_jarvis")
    else:
        print(__doc__)
