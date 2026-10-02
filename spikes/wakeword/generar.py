"""F0-10: genera las muestras sintéticas del detector propio de "Luchi" (D29).

Positivos ("luchi", "oye_luchi") y negativos parecidos ("adversarial") con voces de Piper de
licencia permisiva (docs/LICENCIAS.md). piper-tts se usa solo en desarrollo para producir audio.

Uso (en WSL):  python generar.py --datos ~/luchi-wakeword/data [--escala 1.0] [--muestra]
Salida:        <datos>/clips/<clase>/<train|val>/*.wav  (16 kHz, mono, 16 bits)

Las voces y hablantes de validación nunca se usan para entrenar, así la validación mide
si el modelo generaliza a voces nuevas.
"""
import argparse
import json
import multiprocessing as mp
import random
import urllib.request
import wave
from math import gcd
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

HF = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
SR = 16000

# (archivo, ruta en HF, hablantes, idioma de la voz). Licencias en docs/LICENCIAS.md.
# Descartadas al escucharlas (F0-10): carlfm (x_low), mls_9972 y mls_10246 (low) no se entienden en palabras cortas.
VOCES = {
    "claude": ("es_MX-claude-high", "es/es_MX/claude/high", 1, "es"),
    "davefx": ("es_ES-davefx-medium", "es/es_ES/davefx/medium", 1, "es"),
    "ald": ("es_MX-ald-medium", "es/es_MX/ald/medium", 1, "es"),
    "sharvard": ("es_ES-sharvard-medium", "es/es_ES/sharvard/medium", 2, "es"),
    "libritts": ("en_US-libritts_r-medium", "en/en_US/libritts_r/medium", 904, "en"),
}

# Validación: hablantes ingleses que no se ven en entrenamiento. La validación en español la dan las
# grabaciones reales (spikes/grabar-voz), que valen más que cualquier voz sintética.
VAL_HABLANTES_EN = set(range(800, 904))

# Qué voces dicen bien cada frase, medido con variantes.py + calidad.py (F0-10, 40 clips por variante):
#   luchi:     libritts [[ lˈutʃi ]] 85-90 % · sharvard ~45 % · davefx ~30 % · claude y ald 0 % ("Loche")
#   oye_luchi: sharvard 90-100 % · davefx 60-80 % · libritts 25-35 % con las variantes de abajo
# (voz, peso) por clase; claude y ald quedan para los negativos: su "Loche" es un negativo ideal.
VOCES_POR_CLASE = {
    "luchi": [("libritts", 0.75), ("sharvard", 0.15), ("davefx", 0.10)],
    "oye_luchi": [("sharvard", 0.45), ("davefx", 0.30), ("libritts", 0.25)],
    "adversarial": [("libritts", 0.40), ("sharvard", 0.15), ("davefx", 0.15), ("claude", 0.15), ("ald", 0.15)],
}

# Las voces en español leen el texto; las inglesas reciben fonemas del español entre [[ ]],
# así los 904 hablantes dicen "Luchi" como en castellano.
TEXTOS = {
    "luchi": {
        "es": ["Luchi", "Luchi,", "Lúchi", "¿Luchi?"],
        "en": ["[[ lˈutʃi ]]", "[[ lˈutʃi. ]]", "[[ lˈuːtʃi ]]", "[[ lˈutʃi! ]]"],
    },
    "oye_luchi": {
        "es": ["Oye Luchi", "¡Oye Luchi!", "Oye Luchi,", "Oye, Luchi"],
        "en": ["[[ ˈoʊ jˈeɪ lˈutʃi ]]", "[[ ˈo jˈe lˈutʃi ]]", "[[ ˈoʝe, lˈutʃi. ]]"],
    },
}
# Se genera de más porque el control de calidad descarta lo que no se entiende.
SOBREGENERAR = {"luchi": 1.3, "oye_luchi": 2.0, "adversarial": 1.0}

# Negativos parecidos: comparten sonidos con "Luchi" o son órdenes frecuentes de la casa.
ADVERSARIAL = [
    "luz", "la luz", "prendé la luz", "apagá la luz", "la luz del comedor", "Lucho", "Lucha", "luchar",
    "luché", "lucha libre", "luchador", "Lucía", "Luci", "Lucy", "Luis", "Luigi", "lunes", "luna", "lunita",
    "leche", "lechuga", "lucir", "lucen", "lúcido", "chuchi", "cuchi", "duchi", "ducha", "voy a la ducha",
    "mochi", "pochi", "uchi", "mucha", "muchas gracias", "música", "cuchillo", "chile", "Chichi", "Luli",
    "Lula", "Lupe", "Lucas", "lunch", "lucky", "looking", "Lichi", "lichi", "luchito no", "oye", "oye Lucho",
    "oye Lucía", "oye Luis", "oíd", "hoy luchamos", "joya", "ojo Lucho", "oye mira", "oye che", "che Luchi no",
    "uchi uchi", "chau", "hola", "listo", "poné música", "pausa", "subí el volumen", "la tele", "Netflix",
]
# Frases de una sola palabra suelen ser cortas: se repiten más para equilibrar.
ADVERSARIAL_EN = ["[[ lˈuːsi ]]", "[[ lˈʌki ]]", "[[ lˈʊkɪŋ ]]", "[[ lˈuːdʒi ]]", "[[ tʃˈuːtʃi ]]", "[[ lˈitʃi ]]"]


def variacion(rng: random.Random):
    """Velocidad (length_scale), entonación (noise) y ritmo (noise_w). Rangos acotados:
    con más variación las voces deforman las palabras cortas ("loche", "luqui")."""
    return rng.uniform(0.85, 1.25), rng.uniform(0.5, 0.75), rng.uniform(0.6, 0.9)


def descargar(datos: Path, archivo: str, ruta: str) -> Path:
    destino = datos / "voces" / f"{archivo}.onnx"
    for suf in (".onnx", ".onnx.json"):
        f = datos / "voces" / f"{archivo}{suf}"
        if not f.exists():
            f.parent.mkdir(parents=True, exist_ok=True)
            print(f"descargando {f.name}", flush=True)
            urllib.request.urlretrieve(f"{HF}/{ruta}/{archivo}{suf}", f)
    return destino


_cache: dict = {}


def _un_hilo():
    """Cada proceso usa 1 hilo de onnxruntime: con 14 procesos × 16 hilos la CPU se ahogaba (carga 260)."""
    import onnxruntime as ort

    if getattr(ort.InferenceSession, "_luchi", False):
        return
    original = ort.InferenceSession

    class Sesion(original):
        _luchi = True

        def __init__(self, *args, sess_options=None, **kw):
            sess_options = sess_options or ort.SessionOptions()
            sess_options.intra_op_num_threads = 1
            sess_options.inter_op_num_threads = 1
            super().__init__(*args, sess_options=sess_options, **kw)

    ort.InferenceSession = Sesion


def _voz(path: str):
    _un_hilo()
    from piper import PiperVoice  # import tardío: cada proceso carga sus voces

    if path not in _cache:
        _cache[path] = PiperVoice.load(path)
    return _cache[path]


def sintetizar(tarea):
    """tarea = (salida, ruta_voz, texto, hablante, length, noise, noise_w, semilla)"""
    from piper import SynthesisConfig

    salida, ruta, texto, hablante, ls, ns, nw, _ = tarea
    if Path(salida).exists():
        return 0
    voz = _voz(ruta)
    cfg = SynthesisConfig(speaker_id=hablante, length_scale=ls, noise_scale=ns, noise_w_scale=nw)
    chunks = list(voz.synthesize(texto, syn_config=cfg))
    if not chunks:
        return 0
    audio = np.concatenate([c.audio_int16_array for c in chunks]).astype(np.float32)
    sr = chunks[0].sample_rate
    g = gcd(SR, sr)
    audio = resample_poly(audio, SR // g, sr // g)
    audio = np.clip(audio, -32768, 32767).astype(np.int16)
    Path(salida).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(salida, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(audio.tobytes())
    return 1


def planificar(datos: Path, rutas: dict, n: dict, rng: random.Random):
    tareas = []
    clips = datos / "clips"

    def elegir(clase: str, split: str):
        """Voz + hablante. En validación solo hablantes ingleses que no se usan para entrenar."""
        if split == "val":
            return "libritts", rng.choice(sorted(VAL_HABLANTES_EN))
        voces, pesos = zip(*VOCES_POR_CLASE[clase])
        v = rng.choices(voces, pesos)[0]
        if v == "libritts":
            return v, rng.randrange(800)
        return v, rng.randrange(VOCES[v][2])

    for clase in ("luchi", "oye_luchi", "adversarial"):
        for split in ("train", "val"):
            for i in range(int(n[(clase, split)] * SOBREGENERAR[clase])):
                v, h = elegir(clase, split)
                idioma = VOCES[v][3]
                if clase == "adversarial":
                    texto = rng.choice(ADVERSARIAL_EN) if idioma == "en" and rng.random() < 0.3 else rng.choice(ADVERSARIAL)
                else:
                    texto = rng.choice(TEXTOS[clase][idioma])
                ls, ns, nw = variacion(rng)
                salida = str(clips / clase / split / f"{i:06d}_{v}_{h}.wav")
                tareas.append((salida, str(rutas[v]), texto, h if VOCES[v][2] > 1 else None, ls, ns, nw, i))
    return tareas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", type=Path, required=True)
    ap.add_argument("--escala", type=float, default=1.0, help="multiplica la cantidad de muestras")
    ap.add_argument("--muestra", action="store_true", help="solo 8 por clase, para escuchar")
    ap.add_argument("--procesos", type=int, default=max(1, mp.cpu_count() - 2))
    args = ap.parse_args()

    base = {("luchi", "train"): 30000, ("luchi", "val"): 3000,
            ("oye_luchi", "train"): 30000, ("oye_luchi", "val"): 3000,
            ("adversarial", "train"): 40000, ("adversarial", "val"): 4000}
    n = {k: (8 if args.muestra else int(v * args.escala)) for k, v in base.items()}
    datos = args.datos.expanduser()
    if args.muestra:
        datos = datos / "muestra"
    rutas = {v: descargar(args.datos.expanduser(), a, r) for v, (a, r, _, _) in VOCES.items()}
    tareas = planificar(datos, rutas, n, random.Random(1234))
    print(f"{len(tareas)} clips con {args.procesos} procesos", flush=True)
    hechos = 0
    with mp.get_context("spawn").Pool(args.procesos) as pool:
        for k, r in enumerate(pool.imap_unordered(sintetizar, tareas, chunksize=64), 1):
            hechos += r
            if k % 5000 == 0:
                print(f"  {k}/{len(tareas)}", flush=True)
    resumen = {f"{c}/{s}": len(list((datos / "clips" / c / s).glob("*.wav"))) for c, s in n}
    (datos / "clips" / "resumen.json").write_text(json.dumps(resumen, indent=2))
    print(json.dumps(resumen, indent=2))


if __name__ == "__main__":
    main()
