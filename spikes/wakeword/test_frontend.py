"""Las dos implementaciones del frontend tienen que coincidir (la de numpy es la que corre en la app)."""
import numpy as np
import torch

import frontend


def test_numpy_y_torch_coinciden():
    rng = np.random.default_rng(0)
    audio = (rng.standard_normal(16000 * 2) * 0.1).astype(np.float32)
    a = frontend.logmel_np(audio)
    b = frontend.LogMelTorch()(torch.from_numpy(audio)[None])[0].numpy()
    assert a.shape == b.shape == (1 + (len(audio) - frontend.WIN) // frontend.HOP, frontend.N_MELS)
    assert np.max(np.abs(a - b)) < 1e-3


def test_tono_cae_en_la_banda_correcta():
    t = np.arange(16000) / 16000
    audio = (0.5 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
    m = frontend.logmel_np(audio).mean(axis=0)
    centros = frontend._mel_a_hz(np.linspace(frontend._hz_a_mel(60), frontend._hz_a_mel(7600), 42))[1:-1]
    assert abs(centros[m.argmax()] - 1000) < 150


def test_silencio_da_piso():
    m = frontend.logmel_np(np.zeros(16000, dtype=np.float32))
    assert np.allclose(m, np.log(frontend.EPS))
