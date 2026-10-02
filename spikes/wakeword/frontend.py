"""Frontend propio del detector (D29): audio 16 kHz → log-mel de 40 bandas cada 10 ms.

Hay dos implementaciones que deben dar el mismo resultado (lo verifica test_frontend.py):
- `logmel_np`: numpy puro, la que se porta a luchi-voice para correr en vivo.
- `LogMelTorch`: PyTorch, para calcular features en GPU durante el entrenamiento.
"""
import numpy as np

SR = 16000
N_FFT = 512
WIN = 400          # 25 ms
HOP = 160          # 10 ms → 100 cuadros por segundo
N_MELS = 40
F_MIN, F_MAX = 60.0, 7600.0
EPS = 1e-6


def _hz_a_mel(f):
    return 2595.0 * np.log10(1.0 + f / 700.0)


def _mel_a_hz(m):
    return 700.0 * (10 ** (m / 2595.0) - 1.0)


def banco_mel() -> np.ndarray:
    """Matriz (N_MELS, N_FFT//2+1) de filtros triangulares en escala mel (HTK)."""
    mels = np.linspace(_hz_a_mel(F_MIN), _hz_a_mel(F_MAX), N_MELS + 2)
    hz = _mel_a_hz(mels)
    bins = np.fft.rfftfreq(N_FFT, 1.0 / SR)
    fb = np.zeros((N_MELS, len(bins)), dtype=np.float32)
    for m in range(N_MELS):
        izq, centro, der = hz[m], hz[m + 1], hz[m + 2]
        subida = (bins - izq) / (centro - izq)
        bajada = (der - bins) / (der - centro)
        fb[m] = np.maximum(0.0, np.minimum(subida, bajada))
    return fb


VENTANA = np.hanning(WIN + 1)[:-1].astype(np.float32)  # Hann periódica
FB = banco_mel()


def logmel_np(audio: np.ndarray) -> np.ndarray:
    """audio float32 en [-1, 1] → (cuadros, N_MELS) float32. Sin relleno: cuadros = 1 + (n - WIN) // HOP."""
    audio = np.asarray(audio, dtype=np.float32)
    if len(audio) < WIN:
        return np.zeros((0, N_MELS), dtype=np.float32)
    n = 1 + (len(audio) - WIN) // HOP
    idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
    cuadros = audio[idx] * VENTANA
    espectro = np.abs(np.fft.rfft(cuadros, n=N_FFT, axis=1)) ** 2
    return np.log(espectro @ FB.T + EPS).astype(np.float32)


try:
    import torch

    class LogMelTorch(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.register_buffer("ventana", torch.from_numpy(VENTANA))
            self.register_buffer("fb", torch.from_numpy(FB))

        def forward(self, audio: torch.Tensor) -> torch.Tensor:
            """audio (lote, muestras) → (lote, cuadros, N_MELS), igual que logmel_np."""
            cuadros = audio.unfold(-1, WIN, HOP) * self.ventana
            espectro = torch.fft.rfft(cuadros, n=N_FFT, dim=-1).abs() ** 2
            return torch.log(espectro @ self.fb.T + EPS)
except ImportError:  # en Windows la app solo necesita la versión numpy
    pass
