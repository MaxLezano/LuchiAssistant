"""F0-10: pasa los negativos generales (CC BY 4.0) a features log-mel del frontend propio.

Fuentes (descargadas con descargar.sh): LibriSpeech train-clean-100, Multilingual LibriSpeech en
español (parquet) y MUSAN (música, habla y ruido).

Salida en <datos>/features/:
  neg_<fuente>_<train|val>.f16   matriz float16 (cuadros, 40) escrita en crudo
  negativos.json                 forma de cada matriz y horas de audio
La validación es ~10 % por archivo (MLS dev/test enteros); sirve para medir falsos positivos por hora.

Uso (en WSL):  python preparar_negativos.py --datos ~/luchi-wakeword/data
"""
import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import soundfile as sf
import torch
from scipy.signal import resample_poly

import frontend

LOTE_SEGUNDOS = 600  # se juntan ~10 min de audio por pasada en la GPU


def es_val(nombre: str) -> bool:
    return int(hashlib.md5(nombre.encode()).hexdigest(), 16) % 10 == 0


def a_16k(audio: np.ndarray, sr: int) -> np.ndarray:
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != frontend.SR:
        audio = resample_poly(audio, frontend.SR, sr)
    return audio.astype(np.float32)


def librispeech(raw: Path):
    for f in sorted((raw / "LibriSpeech").rglob("*.flac")):
        audio, sr = sf.read(f, dtype="float32")
        yield f.name, a_16k(audio, sr), None


def musan(raw: Path):
    for f in sorted((raw / "musan").rglob("*.wav")):
        audio, sr = sf.read(f, dtype="float32")
        yield f"{f.parent.parent.name}/{f.name}", a_16k(audio, sr), None


def mls(raw: Path):
    for f in sorted((raw / "mls_es").glob("*.parquet")):
        forzar = "val" if f.stem in ("dev", "test") else "train"
        tabla = pq.ParquetFile(f)
        for lote in tabla.iter_batches(batch_size=64, columns=["audio"]):
            for fila in lote.column("audio").to_pylist():
                audio, sr = sf.read(io.BytesIO(fila["bytes"]), dtype="float32")
                yield fila.get("path") or f"{f.stem}-{hash(fila['bytes'][:64])}", a_16k(audio, sr), forzar


class Escritor:
    def __init__(self, ruta: Path):
        self.ruta, self.f, self.cuadros = ruta, ruta.open("wb"), 0

    def escribir(self, feats: np.ndarray):
        self.f.write(feats.astype(np.float16).tobytes())
        self.cuadros += len(feats)

    def cerrar(self):
        self.f.close()
        return {"archivo": self.ruta.name, "forma": [self.cuadros, frontend.N_MELS],
                "horas": round(self.cuadros / 100 / 3600, 2)}


def procesar(nombre, fuente, salida: Path, mel, dispositivo):
    esc = {s: Escritor(salida / f"neg_{nombre}_{s}.f16") for s in ("train", "val")}
    buffers = {"train": [], "val": []}
    tam = {"train": 0, "val": 0}

    def vaciar(s):
        if not buffers[s]:
            return
        audio = torch.from_numpy(np.concatenate(buffers[s])).to(dispositivo)
        with torch.no_grad():
            esc[s].escribir(mel(audio[None])[0].cpu().numpy())
        buffers[s], tam[s] = [], 0

    for n, (archivo, audio, forzar) in enumerate(fuente):
        s = forzar or ("val" if es_val(archivo) else "train")
        buffers[s].append(audio)
        tam[s] += len(audio)
        if tam[s] > LOTE_SEGUNDOS * frontend.SR:
            vaciar(s)
        if n % 2000 == 0:
            print(f"  {nombre}: {n} archivos", flush=True)
    for s in buffers:
        vaciar(s)
    return {s: e.cerrar() for s, e in esc.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", type=Path, required=True)
    args = ap.parse_args()
    datos = args.datos.expanduser()
    salida = datos / "features"
    salida.mkdir(parents=True, exist_ok=True)
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    mel = frontend.LogMelTorch().to(dispositivo)
    raw = datos / "raw"
    resumen = {}
    for nombre, fuente in [("librispeech", librispeech(raw)), ("mls_es", mls(raw)), ("musan", musan(raw))]:
        print(f"{nombre}…", flush=True)
        resumen[nombre] = procesar(nombre, fuente, salida, mel, dispositivo)
        print(f"  {json.dumps(resumen[nombre])}", flush=True)
    (salida / "negativos.json").write_text(json.dumps(resumen, indent=2))
    total = sum(v["horas"] for r in resumen.values() for v in r.values())
    print(f"total: {total:.0f} horas de negativos")


if __name__ == "__main__":
    main()
