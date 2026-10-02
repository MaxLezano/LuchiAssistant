"""F0-11: entrena el detector propio de "Luchi" / "Oye Luchi" (D29) y lo exporta a ONNX.

Una red convolucional chica con 3 salidas (nada, luchi, oye_luchi) sobre ventanas de 1,6 s de
log-mel (frontend.py). La aumentación se hace en GPU en cada lote: posición, eco sintético,
ruido/música de MUSAN y volumen. Los negativos generales salen de preparar_negativos.py.

Uso (en WSL):  python entrenar.py --datos ~/luchi-wakeword/data [--pasos 30000] [--salida modelos/]
"""
import argparse
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torch.nn as nn
import torch.nn.functional as F

import frontend

CUADROS = 160                                        # 1,6 s
MUESTRAS = frontend.WIN + (CUADROS - 1) * frontend.HOP  # 25.840 muestras → exactamente 160 cuadros
CLASES = ["nada", "luchi", "oye_luchi"]


# --- datos ------------------------------------------------------------------
def cargar_clips(carpeta: Path, maximo: int | None = None) -> list[np.ndarray]:
    lista = carpeta / "aceptados.txt"   # si pasó por calidad.py, solo los aceptados
    archivos = sorted(carpeta / n for n in lista.read_text().split()) if lista.exists() else sorted(carpeta.glob("*.wav"))
    if maximo:
        random.Random(0).shuffle(archivos)
        archivos = archivos[:maximo]
    clips = []
    for f in archivos:
        a, sr = sf.read(f, dtype="int16")  # int16 en memoria: ~150 mil clips en float32 no entran en 15 GB
        assert sr == frontend.SR
        clips.append(a[:MUESTRAS])
    return clips


def cargar_ruido(raw: Path, horas: float = 4.0) -> torch.Tensor:
    """Ruido y música de MUSAN en un solo tensor (para mezclar con positivos y parecidos)."""
    archivos = sorted((raw / "musan" / "noise").rglob("*.wav")) + sorted((raw / "musan" / "music").rglob("*.wav"))
    random.Random(1).shuffle(archivos)
    partes, total = [], 0
    for f in archivos:
        a, sr = sf.read(f, dtype="float32")
        if a.ndim > 1:
            a = a.mean(axis=1)
        partes.append(a)
        total += len(a)
        if total > horas * 3600 * frontend.SR:
            break
    return torch.from_numpy(np.concatenate(partes))


class Negativos:
    """Ventanas de 160 cuadros tomadas al azar de las features de negativos generales (memmap)."""

    def __init__(self, features: Path, split: str):
        meta = json.loads((features / "negativos.json").read_text())
        self.mats = []
        for fuente in meta.values():
            info = fuente[split]
            if info["forma"][0] > CUADROS:
                self.mats.append(np.memmap(features / info["archivo"], dtype=np.float16, mode="r", shape=tuple(info["forma"])))
        self.pesos = np.array([len(m) for m in self.mats], dtype=np.float64)
        self.pesos /= self.pesos.sum()
        self.horas = sum(len(m) for m in self.mats) / 100 / 3600

    def lote(self, n: int, rng: np.random.Generator, bloques: int = 8) -> torch.Tensor:
        """Lee pocos bloques contiguos y saca varias ventanas de cada uno: leer 320 ventanas sueltas
        de archivos de varios GB era lo que más frenaba cada paso."""
        largo = CUADROS * 12
        por_bloque = -(-n // bloques)
        out = []
        for i in rng.choice(len(self.mats), size=bloques, p=self.pesos):
            ini = rng.integers(0, len(self.mats[i]) - largo)
            bloque = np.asarray(self.mats[i][ini:ini + largo], dtype=np.float32)
            offs = rng.integers(0, largo - CUADROS, por_bloque)
            out.append(np.stack([bloque[o:o + CUADROS] for o in offs]))
        return torch.from_numpy(np.concatenate(out)[:n])


# --- aumentación en GPU -----------------------------------------------------
def eco_sintetico(n: int, dispositivo, rng: torch.Generator) -> torch.Tensor:
    """Respuestas al impulso propias: ruido con caída exponencial (RT60 entre 0,1 y 0,7 s)."""
    largo = int(0.4 * frontend.SR)
    t = torch.arange(largo, device=dispositivo) / frontend.SR
    rt60 = 0.1 + 0.6 * torch.rand(n, 1, device=dispositivo, generator=rng)
    ir = torch.randn(n, largo, device=dispositivo, generator=rng) * torch.exp(-6.9 * t / rt60)
    ir[:, 0] = 1.0                                      # sonido directo
    seco = torch.rand(n, 1, device=dispositivo, generator=rng) < 0.3
    ir = torch.where(seco, F.one_hot(torch.zeros(n, dtype=torch.long, device=dispositivo), largo).float(), ir)
    return ir / ir.norm(dim=1, keepdim=True)


def convolucion_fft(x: torch.Tensor, ir: torch.Tensor) -> torch.Tensor:
    n = x.shape[1] + ir.shape[1] - 1
    nfft = 1 << (n - 1).bit_length()
    y = torch.fft.irfft(torch.fft.rfft(x, nfft) * torch.fft.rfft(ir, nfft), nfft)
    return y[:, : x.shape[1]]


def armar_ventanas(clips: list[np.ndarray], idx: np.ndarray, rng: np.random.Generator) -> torch.Tensor:
    """Ubica cada clip en una posición al azar dentro de la ventana de 1,6 s, entero."""
    out = np.zeros((len(idx), MUESTRAS), dtype=np.float32)
    for k, i in enumerate(idx):
        c = clips[i]
        c = c.astype(np.float32) / 32768.0 if c.dtype == np.int16 else c
        ini = rng.integers(0, max(1, MUESTRAS - len(c)))
        out[k, ini:ini + len(c)] = c[: MUESTRAS - ini]
    return torch.from_numpy(out)


def tono_y_velocidad(audio: torch.Tensor, rng_t: torch.Generator, prob: float = 0.5) -> torch.Tensor:
    """Remuestreo: factor > 1 acelera y sube el tono (voces infantiles y femeninas más agudas; las 904 voces
    sintéticas son de adultos y la voz real de una nena no se detectaba). Factor < 1 baja el tono."""
    n, d = audio.shape[0], audio.device
    factor = torch.where(torch.rand(n, device=d, generator=rng_t) < 0.8,
                         1.0 + 0.35 * torch.rand(n, device=d, generator=rng_t),
                         1.0 - 0.12 * torch.rand(n, device=d, generator=rng_t))
    usar = torch.rand(n, device=d, generator=rng_t) < prob
    t = torch.arange(MUESTRAS, device=d, dtype=torch.float32)
    # ventana centrada en la energía: se estira o comprime alrededor del centro del clip
    origen = (t[None, :] - MUESTRAS / 2) * factor[:, None] + MUESTRAS / 2
    fuera = usar[:, None] & ((origen < 0) | (origen > MUESTRAS - 1))   # al acelerar, los bordes quedan sin audio
    pos = torch.where(usar[:, None], origen, t[None, :]).clamp(0, MUESTRAS - 1)
    i0 = pos.floor().long()
    i1 = (i0 + 1).clamp(max=MUESTRAS - 1)
    w = pos - i0
    out = torch.gather(audio, 1, i0) * (1 - w) + torch.gather(audio, 1, i1) * w
    return torch.where(fuera, torch.zeros_like(out), out)


def aumentar(audio: torch.Tensor, ruido: torch.Tensor, rng_t: torch.Generator) -> torch.Tensor:
    n, d = audio.shape[0], audio.device
    audio = tono_y_velocidad(audio, rng_t)
    audio = convolucion_fft(audio, eco_sintetico(n, d, rng_t))
    # el ruido vive en la GPU: se recortan las ventanas con un índice, sin pasar por la CPU
    ini = torch.randint(0, len(ruido) - MUESTRAS, (n, 1), generator=rng_t, device=d)
    fondo = ruido[ini + torch.arange(MUESTRAS, device=d)]
    snr_db = 20 * torch.rand(n, 1, device=d, generator=rng_t)
    p_voz = audio.pow(2).mean(dim=1, keepdim=True).clamp_min(1e-8)
    p_fondo = fondo.pow(2).mean(dim=1, keepdim=True).clamp_min(1e-8)
    fondo = fondo * torch.sqrt(p_voz / (p_fondo * 10 ** (snr_db / 10)))
    sin_fondo = torch.rand(n, 1, device=d, generator=rng_t) < 0.2
    audio = audio + torch.where(sin_fondo, torch.zeros_like(fondo), fondo)
    ganancia = 10 ** (-(25 * torch.rand(n, 1, device=d, generator=rng_t)) / 20)  # 0 a -25 dB
    audio = audio / audio.abs().amax(dim=1, keepdim=True).clamp_min(1e-6) * ganancia
    # piso de ruido de micrófono (-75 a -45 dBFS): los clips sintéticos tienen silencio digital perfecto y un
    # micrófono real nunca (con la voz real el log-mel tenía otro nivel de fondo, -7,4 contra -10,1)
    piso = 10 ** ((-75 + 30 * torch.rand(n, 1, device=d, generator=rng_t)) / 20)
    return audio + piso * torch.randn(audio.shape, device=d, generator=rng_t)


# --- modelo -----------------------------------------------------------------
class Bloque(nn.Module):
    def __init__(self, cin, cout, stride):
        super().__init__()
        self.dw = nn.Conv2d(cin, cin, 3, stride=stride, padding=1, groups=cin, bias=False)
        self.pw = nn.Conv2d(cin, cout, 1, bias=False)
        self.bn = nn.BatchNorm2d(cout)

    def forward(self, x):
        return F.relu(self.bn(self.pw(self.dw(x))))


class Detector(nn.Module):
    """Entrada (lote, 160, 40) log-mel → logits (lote, 3)."""

    def __init__(self, ancho: int = 64):
        super().__init__()
        self.norm = nn.BatchNorm2d(1)
        self.entrada = nn.Sequential(nn.Conv2d(1, ancho, (5, 3), stride=(2, 1), padding=(2, 1), bias=False),
                                     nn.BatchNorm2d(ancho), nn.ReLU())
        self.bloques = nn.Sequential(Bloque(ancho, ancho, (2, 2)), Bloque(ancho, ancho, 1),
                                     Bloque(ancho, ancho * 2, (2, 2)), Bloque(ancho * 2, ancho * 2, 1),
                                     Bloque(ancho * 2, ancho * 2, (2, 2)), Bloque(ancho * 2, ancho * 2, 1))
        self.salida = nn.Sequential(nn.Dropout(0.2), nn.Linear(ancho * 2, len(CLASES)))

    def forward(self, x):
        x = self.norm(x.unsqueeze(1))
        x = self.bloques(self.entrada(x))
        return self.salida(x.mean(dim=(2, 3)))


# --- evaluación -------------------------------------------------------------
@torch.no_grad()
def probabilidades(modelo, feats: torch.Tensor, lote: int = 2048) -> torch.Tensor:
    modelo.eval()
    out = [F.softmax(modelo(feats[i:i + lote]), dim=1) for i in range(0, len(feats), lote)]
    return torch.cat(out)


@torch.no_grad()
def falsos_por_hora(modelo, neg: Negativos, mel_dev, umbral: float, paso: int = 8, max_horas: float = 20.0):
    """Recorre los negativos de validación como si fuera audio en vivo (cada 80 ms) y cuenta activaciones.
    Tras una activación se ignoran 2 s (igual que hará luchi-voice)."""
    modelo.eval()
    activaciones, cuadros_vistos = 0, 0
    for m in neg.mats:
        limite = min(len(m), int(max_horas / len(neg.mats) * 3600 * 100))
        bloquear_hasta = -1
        for ini in range(0, limite - CUADROS, paso * 4096):
            fin = min(limite - CUADROS, ini + paso * 4096)
            idx = np.arange(ini, fin, paso)
            ventanas = np.stack([m[i:i + CUADROS] for i in idx]).astype(np.float32)
            p = probabilidades(modelo, torch.from_numpy(ventanas).to(mel_dev))[:, 1:].max(dim=1).values.cpu().numpy()
            for i, prob in zip(idx, p):
                if prob >= umbral and i > bloquear_hasta:
                    activaciones += 1
                    bloquear_hasta = i + 200
        cuadros_vistos += limite
    horas = cuadros_vistos / 100 / 3600
    return activaciones / max(horas, 1e-9), horas


def feats_de_clips(clips, mel, dispositivo, rng):
    idx = np.arange(len(clips))
    feats = []
    for i in range(0, len(idx), 1024):
        audio = armar_ventanas(clips, idx[i:i + 1024], rng).to(dispositivo)
        with torch.no_grad():
            feats.append(mel(audio))
    return torch.cat(feats)


def grabaciones_reales(carpeta: Path, mitad: str | None = None) -> dict[str, list[np.ndarray]]:
    """Tomas reales de spikes/grabar-voz (sección detector), separadas por clase.
    mitad="train" / "test" divide por frase (id par / impar), nunca por toma: las 3 tomas de una
    misma frase quedan del mismo lado, así la prueba es con frases que el modelo no escuchó."""
    import csv
    from scipy.signal import resample_poly

    out = {"luchi": [], "oye_luchi": [], "nada": []}
    meta = carpeta / "metadata.csv"
    if not meta.exists():
        return out
    for fila in csv.reader(meta.open(encoding="utf-8"), delimiter="|"):
        if mitad and (int(fila[0]) % 2 == 0) != (mitad == "train"):
            continue
        texto = fila[1].lower()
        clase = "oye_luchi" if texto.startswith("oye") else ("luchi" if "luchi" in texto else "nada")
        for f in sorted(carpeta.glob(f"{fila[0]}_t*.wav")):
            a, sr = sf.read(f, dtype="float32")
            a = resample_poly(a, frontend.SR, sr).astype(np.float32)
            # se recorta a la ventana alrededor de la parte con voz
            e = np.convolve(a ** 2, np.ones(800) / 800, "same")
            centro = int(np.argmax(e))
            ini = max(0, min(len(a) - MUESTRAS, centro - MUESTRAS // 2))
            out[clase].append(a[ini:ini + MUESTRAS])
    return out


# --- entrenamiento ----------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", type=Path, required=True)
    ap.add_argument("--pasos", type=int, default=30000)
    ap.add_argument("--salida", type=Path, default=Path("modelos"))
    ap.add_argument("--voz-real", type=Path, default=Path("/mnt/e/Luchi/voice-data/luz/detector"))
    ap.add_argument("--rapido", action="store_true", help="prueba de humo: pocos clips, pasos y horas de validación")
    ap.add_argument("--real-train", action="store_true",
                    help="entrenar también con la mitad de las tomas reales (por frase) y medir con la otra mitad")
    args = ap.parse_args()
    datos = args.datos.expanduser()
    args.salida.mkdir(parents=True, exist_ok=True)
    dispositivo = "cuda"
    torch.manual_seed(0)
    rng = np.random.default_rng(0)
    rng_t = torch.Generator(device=dispositivo).manual_seed(0)
    mel = frontend.LogMelTorch().to(dispositivo)

    print("cargando datos…", flush=True)
    maximo = 1500 if args.rapido else None
    if args.rapido:
        args.pasos = min(args.pasos, 300)
    clips = {c: {s: cargar_clips(datos / "clips" / c / s, maximo) for s in ("train", "val")}
             for c in ("luchi", "oye_luchi", "adversarial")}
    for c, d in clips.items():
        print(f"  {c}: {len(d['train'])} train · {len(d['val'])} val", flush=True)
    ruido = cargar_ruido(datos / "raw", horas=0.3 if args.rapido else 4.0).to(dispositivo)
    print(f"  ruido MUSAN: {len(ruido) / frontend.SR / 3600:.1f} h", flush=True)
    neg_train = Negativos(datos / "features", "train")
    neg_val = Negativos(datos / "features", "val")
    print(f"  negativos generales: {neg_train.horas:.0f} h train · {neg_val.horas:.0f} h val", flush=True)

    reales = {}
    if args.real_train:
        reales = {k: v for k, v in grabaciones_reales(args.voz_real, "train").items() if v}
        print("  reales para entrenar: " + " · ".join(f"{k} {len(v)}" for k, v in reales.items()), flush=True)
    modelo = Detector().to(dispositivo)
    print(f"  parámetros: {sum(p.numel() for p in modelo.parameters()):,}", flush=True)
    opt = torch.optim.AdamW(modelo.parameters(), lr=2e-3, weight_decay=1e-3)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=args.pasos, pct_start=0.05)
    n_pos, n_adv, n_neg = 96, 96, 320
    # pesos de clase: equivocarse con un negativo (falso positivo) cuesta más que perder un positivo
    pesos = torch.tensor([1.0, 1.0, 1.0], device=dispositivo)

    t0 = time.time()
    for paso in range(1, args.pasos + 1):
        modelo.train()
        il = rng.integers(0, len(clips["luchi"]["train"]), n_pos // 2)
        io = rng.integers(0, len(clips["oye_luchi"]["train"]), n_pos // 2)
        ia = rng.integers(0, len(clips["adversarial"]["train"]), n_adv)
        partes = [armar_ventanas(clips["luchi"]["train"], il, rng), armar_ventanas(clips["oye_luchi"]["train"], io, rng),
                  armar_ventanas(clips["adversarial"]["train"], ia, rng)]
        etiquetas = [torch.full((n_pos // 2,), 1), torch.full((n_pos // 2,), 2), torch.zeros(n_adv)]
        # tomas reales (pocas): se repiten con aumentación distinta en cada lote
        for clase, k, cant in (("luchi", 1, 16), ("oye_luchi", 2, 8), ("nada", 0, 8)):
            if clase in reales:
                partes.append(armar_ventanas(reales[clase], rng.integers(0, len(reales[clase]), cant), rng))
                etiquetas.append(torch.full((cant,), k))
        audio = torch.cat(partes).to(dispositivo)
        with torch.no_grad():
            feats = mel(aumentar(audio, ruido, rng_t))
        feats = torch.cat([feats, neg_train.lote(n_neg, rng).to(dispositivo)])
        y = torch.cat(etiquetas + [torch.zeros(n_neg)]).long().to(dispositivo)
        # SpecAugment liviano: tapar bandas y tramos al azar
        if paso > 500:
            b = rng.integers(0, frontend.N_MELS - 6)
            feats[:, :, b:b + rng.integers(0, 6)] = feats.mean()
        perdida = F.cross_entropy(modelo(feats), y, weight=pesos, label_smoothing=0.05)
        opt.zero_grad(set_to_none=True)
        perdida.backward()
        opt.step()
        sched.step()
        if paso % (100 if args.rapido else 1000) == 0:
            print(f"paso {paso} · pérdida {perdida.item():.3f} · {time.time() - t0:.0f} s", flush=True)

    # --- validación ---
    print("validando…", flush=True)
    rng_v = np.random.default_rng(99)
    reporte = {"pasos": args.pasos}
    val = {c: feats_de_clips(clips[c]["val"], mel, dispositivo, rng_v) for c in ("luchi", "oye_luchi", "adversarial")}
    real = grabaciones_reales(args.voz_real, "test" if args.real_train else None)
    real_feats = {c: feats_de_clips(v, mel, dispositivo, rng_v) for c, v in real.items() if v}
    for umbral in (0.5, 0.7, 0.8, 0.9, 0.95):
        fila = {}
        for c, k in (("luchi", 1), ("oye_luchi", 2)):
            p = probabilidades(modelo, val[c])
            fila[f"aciertos_{c}"] = round(float((p[:, k] >= umbral).float().mean()), 3)
        p = probabilidades(modelo, val["adversarial"])
        fila["parecidos_activados"] = round(float((p[:, 1:].max(dim=1).values >= umbral).float().mean()), 3)
        for c, f in real_feats.items():
            p = probabilidades(modelo, f)
            if c == "nada":
                fila["real_nada_activados"] = f"{int((p[:, 1:].max(dim=1).values >= umbral).sum())}/{len(f)}"
            else:
                k = CLASES.index(c)
                fila[f"real_{c}"] = f"{int((p[:, k] >= umbral).sum())}/{len(f)}"
        fph, horas = falsos_por_hora(modelo, neg_val, dispositivo, umbral, max_horas=0.5 if args.rapido else 20.0)
        fila["falsos_por_hora"] = round(fph, 2)
        fila["horas_evaluadas"] = round(horas, 1)
        reporte[f"umbral_{umbral}"] = fila
        print(f"umbral {umbral}: {fila}", flush=True)
    (args.salida / "reporte.json").write_text(json.dumps(reporte, indent=2, ensure_ascii=False))

    # --- exportar ---
    modelo.eval().cpu()
    torch.save(modelo.state_dict(), args.salida / "detector.pt")
    ejemplo = torch.randn(1, CUADROS, frontend.N_MELS)
    onnx_path = args.salida / "detector.onnx"
    torch.onnx.export(modelo, ejemplo, onnx_path, input_names=["logmel"], output_names=["logits"],
                      dynamic_axes={"logmel": {0: "lote"}, "logits": {0: "lote"}}, opset_version=17, dynamo=False)
    import onnxruntime as ort

    s = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    diff = np.abs(s.run(None, {"logmel": ejemplo.numpy()})[0] - modelo(ejemplo).detach().numpy()).max()
    print(f"ONNX exportado ({onnx_path.stat().st_size / 1024:.0f} KB) · diferencia con PyTorch {diff:.2e}", flush=True)


if __name__ == "__main__":
    main()
