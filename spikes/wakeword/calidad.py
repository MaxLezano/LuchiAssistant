"""F0-10: control de calidad automático de las muestras con faster-whisper (MIT).

Cada clip se transcribe en español, sin prompt (un prompt con "Luchi" haría aceptar audios malos).
- luchi / oye_luchi: se acepta solo si la transcripción es la frase esperada.
- adversarial: se descarta si suena a "Luchi" (sería un positivo disfrazado de negativo).
Los clips rechazados se mueven a <datos>/rechazados/ para poder escucharlos, y los aceptados quedan
listados en clips/<clase>/<split>/aceptados.txt (entrenar.py usa solo esos si el archivo existe).

Uso (en WSL):  python calidad.py --datos ~/luchi-wakeword/data [--clases luchi oye_luchi] [--maximo 25000] [--muestra]
Medido (F0-10): solo ~0,3 % de los negativos parecidos suena a "Luchi", así que no hace falta revisarlos;
Whisper revisa ~10 clips/s, por eso los positivos de entrenamiento se revisan hasta --maximo por clase.
"""
import argparse
import ctypes
import json
import re
import shutil
import sysconfig
import unicodedata
from pathlib import Path

# CTranslate2 necesita cuBLAS/cuDNN 12/9 de los paquetes nvidia-*. LD_LIBRARY_PATH no sirve una vez
# arrancado el proceso, así que se cargan a mano (RTLD_GLOBAL) antes de crear el modelo.
_nv = Path(sysconfig.get_paths()["purelib"]) / "nvidia"
for _patron in ("cublas/lib/libcublasLt.so.12", "cublas/lib/libcublas.so.12", "cudnn/lib/libcudnn*.so.9"):
    for _lib in sorted(_nv.glob(_patron)):
        ctypes.CDLL(str(_lib), mode=ctypes.RTLD_GLOBAL)

# Grafías con las que Whisper escribe /lutʃi/: "Luchi", "Luchy", "Lucci", "Lutchi". No acepta "Luci" ni "Loche".
LUCHI = r"lu ?(ch|sh|cc|tch)(i|y)"
ACEPTA = {
    "luchi": re.compile(rf"^{LUCHI}$"),
    "oye_luchi": re.compile(rf"^(oye|olle|oie) {LUCHI}$"),
}
PARECE_LUCHI = re.compile(rf"\b{LUCHI}\b")


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-zñ ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def aceptar(clase: str, texto: str) -> bool:
    n = normalizar(texto)
    if clase in ACEPTA:
        return bool(ACEPTA[clase].match(n))
    return not PARECE_LUCHI.search(n)


_modelo = None


def modelo():
    global _modelo
    if _modelo is None:
        from faster_whisper import WhisperModel

        _modelo = WhisperModel("large-v3-turbo", device="cuda", compute_type="int8_float16")
    return _modelo


def transcribir_lote(rutas: list[Path]) -> list[str]:
    """Transcribe varios clips juntos con CTranslate2 (mismo modelo que transcribir, ~10× más rápido):
    cada clip se rellena a 30 s, que es lo que espera el encoder de Whisper."""
    import ctranslate2
    import numpy as np
    import soundfile as sf
    from faster_whisper.tokenizer import Tokenizer

    m = modelo()
    tok = Tokenizer(m.hf_tokenizer, True, task="transcribe", language="es")
    prompt = tok.sot_sequence + [tok.no_timestamps]
    feats, validos = [], []
    for k, ruta in enumerate(rutas):
        try:
            audio, sr = sf.read(str(ruta), dtype="float32")
            assert sr == 16000
        except Exception:
            continue
        # El espectrograma se calcula solo sobre el audio real (calcularlo sobre 30 s era el cuello de botella,
        # en CPU). Whisper recorta a (máximo - 8) en log10 y normaliza con (x + 4) / 4, así que el silencio de
        # relleno vale exactamente máximo - 2: el resultado es equivalente a rellenar el audio.
        corto = m.feature_extractor(audio[: 30 * 16000], padding=160)[:, :3000]
        f = np.full((corto.shape[0], 3000), corto.max() - 2.0, dtype=np.float32)
        f[:, : corto.shape[1]] = corto
        feats.append(f)
        validos.append(k)
    textos = ["ilegible"] * len(rutas)
    if feats:
        lote = ctranslate2.StorageView.from_array(np.ascontiguousarray(np.stack(feats), dtype=np.float32))
        res = m.model.generate(lote, [prompt] * len(feats), beam_size=1, max_length=32)
        for k, r in zip(validos, res):
            textos[k] = tok.decode(r.sequences_ids[0]).strip()
    return textos


def transcribir(ruta: Path) -> str:
    # Se pasa el audio ya leído (16 kHz mono): evita PyAV, cuya versión nueva no es compatible.
    import soundfile as sf

    audio, sr = sf.read(str(ruta), dtype="float32")
    assert sr == 16000, f"{ruta} no está a 16 kHz"
    segs, _ = modelo().transcribe(audio, language="es", beam_size=1, vad_filter=False,
                                  condition_on_previous_text=False, without_timestamps=True)
    return " ".join(s.text for s in segs).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", type=Path, required=True)
    ap.add_argument("--muestra", action="store_true")
    ap.add_argument("--clases", nargs="+", default=["luchi", "oye_luchi", "adversarial"])
    ap.add_argument("--maximo", type=int, default=0, help="máximo de clips de train por clase (0 = todos)")
    args = ap.parse_args()
    datos = args.datos.expanduser() / ("muestra" if args.muestra else "")
    reporte = {}
    import random

    for clase_dir in sorted((datos / "clips").glob("*/*")):
        clase, split = clase_dir.parent.name, clase_dir.name
        if clase not in args.clases:
            continue
        ok = mal = 0
        por_voz: dict = {}
        aceptados = []
        wavs = sorted(clase_dir.glob("*.wav"))
        if split == "train" and args.maximo:
            random.Random(0).shuffle(wavs)
            wavs = wavs[: args.maximo]
        textos = {}
        for ini in range(0, len(wavs), 32):
            if ini % 2496 == 0:
                print(f"  {clase}/{split}: {ini}/{len(wavs)}", flush=True)
            lote = wavs[ini:ini + 32]
            textos.update(zip(lote, transcribir_lote(lote)))  # "ilegible" si el clip está cortado
        for wav in wavs:
            texto = textos[wav]
            voz = wav.stem.split("_", 1)[1].rsplit("_", 1)[0]
            v = por_voz.setdefault(voz, [0, 0])
            if aceptar(clase, texto):
                ok += 1; v[0] += 1
                aceptados.append(wav.name)
            else:
                mal += 1; v[1] += 1
                dest = datos / "rechazados" / clase / split
                dest.mkdir(parents=True, exist_ok=True)
                shutil.move(str(wav), dest / f"{wav.stem}__{normalizar(texto)[:40].replace(' ', '-')}.wav")
        (clase_dir / "aceptados.txt").write_text("\n".join(aceptados) + "\n")
        reporte[f"{clase}/{split}"] = {"aceptados": ok, "rechazados": mal,
                                       "por_voz": {k: f"{a}/{a + b}" for k, (a, b) in sorted(por_voz.items())}}
        print(f"{clase}/{split}: {ok} aceptados, {mal} rechazados · {reporte[f'{clase}/{split}']['por_voz']}", flush=True)
    previo = datos / "clips" / "calidad.json"
    total = json.loads(previo.read_text()) if previo.exists() else {}
    total.update(reporte)
    previo.write_text(json.dumps(total, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
