"""F0-10: control de calidad automático de las muestras con faster-whisper (MIT).

Cada clip se transcribe en español, sin prompt (un prompt con "Luchi" haría aceptar audios malos).
- luchi / oye_luchi: se acepta solo si la transcripción es la frase esperada.
- adversarial: se descarta si suena a "Luchi" (sería un positivo disfrazado de negativo).
Los clips rechazados se mueven a <datos>/rechazados/ para poder escucharlos.

Uso (en WSL):  python calidad.py --datos ~/luchi-wakeword/data [--muestra]
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

        _modelo = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
    return _modelo


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
    args = ap.parse_args()
    datos = args.datos.expanduser() / ("muestra" if args.muestra else "")
    reporte = {}
    for clase_dir in sorted((datos / "clips").glob("*/*")):
        clase, split = clase_dir.parent.name, clase_dir.name
        ok = mal = 0
        por_voz: dict = {}
        for wav in sorted(clase_dir.glob("*.wav")):
            try:
                texto = transcribir(wav)
            except Exception:  # clip cortado (por ejemplo, si se interrumpió la generación)
                texto = "ilegible"
            voz = wav.stem.split("_", 1)[1].rsplit("_", 1)[0]
            v = por_voz.setdefault(voz, [0, 0])
            if aceptar(clase, texto):
                ok += 1; v[0] += 1
            else:
                mal += 1; v[1] += 1
                dest = datos / "rechazados" / clase / split
                dest.mkdir(parents=True, exist_ok=True)
                shutil.move(str(wav), dest / f"{wav.stem}__{normalizar(texto)[:40].replace(' ', '-')}.wav")
        reporte[f"{clase}/{split}"] = {"aceptados": ok, "rechazados": mal,
                                       "por_voz": {k: f"{a}/{a + b}" for k, (a, b) in sorted(por_voz.items())}}
        print(f"{clase}/{split}: {ok} aceptados, {mal} rechazados · {reporte[f'{clase}/{split}']['por_voz']}", flush=True)
    (datos / "clips" / "calidad.json").write_text(json.dumps(reporte, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
