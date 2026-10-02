"""Spike F0-09: genera las mismas frases de Luchi con varias voces de Piper para elegir una.

Uso: cd spikes/piper && uv run python comparar.py
Descarga las voces a E:\\Luchi\\models\\piper (si faltan), genera WAV en output/ y una página
output/index.html para escucharlas. Mide el tiempo de síntesis en CPU (factor de tiempo real).
"""
import html
import json
import pathlib
import time
import urllib.request
import wave

from piper import PiperVoice, SynthesisConfig

MODELOS = pathlib.Path(r"E:\Luchi\models\piper")
SALIDA = pathlib.Path(__file__).parent / "output"
HF = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es"

# (id, ruta en el repo de voces, hablante, descripción, licencia del dataset)
VOCES = [
    ("daniela", "es_AR/daniela/high/es_AR-daniela-high", None, "Argentina · mujer · high", "CC BY-SA 4.0"),
    ("claude", "es_MX/claude/high/es_MX-claude-high", None, "México · high", "Apache 2.0"),
    ("sharvard_f", "es_ES/sharvard/medium/es_ES-sharvard-medium", 1, "España · hablante 1 · medium", "CC BY 3.0"),
    ("sharvard_m", "es_ES/sharvard/medium/es_ES-sharvard-medium", 0, "España · hablante 0 · medium", "CC BY 3.0"),
    ("davefx", "es_ES/davefx/medium/es_ES-davefx-medium", None, "España · hombre · medium", "CC0"),
    ("ald", "es_MX/ald/medium/es_MX-ald-medium", None, "México · hombre · medium", "Unlicense"),
]

FRASES = [
    "¡Hola! Soy Luchi. Decime qué necesitás.",
    "Listo, prendí la luz del comedor.",
    "No encontré la tele del comedor. ¿Está prendida?",
    "Encontré dos: Hollow Knight y Hollow Knight Silksong. ¿Cuál querés abrir?",
    "Grabando. Acordate de avisarle a los demás.",
    "Son las ocho menos dieciséis de la tarde.",
]


def descargar(ruta: str) -> pathlib.Path:
    nombre = pathlib.Path(ruta).name
    for sufijo in (".onnx", ".onnx.json"):
        destino = MODELOS / (nombre + sufijo)
        if not destino.exists():
            destino.parent.mkdir(parents=True, exist_ok=True)
            print(f"  descargando {destino.name}")
            urllib.request.urlretrieve(f"{HF}/{ruta}{sufijo}", destino)
    return MODELOS / (nombre + ".onnx")


def main():
    SALIDA.mkdir(exist_ok=True)
    resultados = []
    for vid, ruta, hablante, desc, lic in VOCES:
        print(f"{vid}: {desc}")
        voz = PiperVoice.load(descargar(ruta))
        cfg = SynthesisConfig(speaker_id=hablante)
        audio_total = sintesis_total = 0.0
        for i, frase in enumerate(FRASES):
            archivo = SALIDA / f"{vid}_{i}.wav"
            t0 = time.perf_counter()
            with wave.open(str(archivo), "wb") as wf:
                voz.synthesize_wav(frase, wf, syn_config=cfg)
            sintesis_total += time.perf_counter() - t0
            with wave.open(str(archivo), "rb") as wf:
                audio_total += wf.getnframes() / wf.getframerate()
        rtf = sintesis_total / audio_total
        t0 = time.perf_counter()
        with wave.open(str(SALIDA / f"{vid}_lat.wav"), "wb") as wf:
            voz.synthesize_wav("Listo.", wf, syn_config=cfg)
        primera = (time.perf_counter() - t0) * 1000
        print(f"  factor de tiempo real {rtf:.3f} · 'Listo.' en {primera:.0f} ms")
        resultados.append(dict(id=vid, desc=desc, licencia=lic, rtf=round(rtf, 3), listo_ms=round(primera)))

    (SALIDA / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    filas = "".join(
        f"<tr><th>{html.escape(f)}</th>" + "".join(f'<td><audio controls preload="none" src="{r["id"]}_{i}.wav"></audio></td>' for r in resultados) + "</tr>"
        for i, f in enumerate(FRASES)
    )
    cab = "".join(f"<th>{r['id']}<br><small>{html.escape(r['desc'])}<br>{r['licencia']} · RTF {r['rtf']} · {r['listo_ms']} ms</small></th>" for r in resultados)
    (SALIDA / "index.html").write_text(
        f"""<!doctype html><meta charset="utf-8"><title>Voces de Luchi</title>
<style>body{{font:14px Segoe UI,sans-serif;background:#13141b;color:#ece8f0;padding:16px}}table{{border-collapse:collapse}}
td,th{{border:1px solid #2c3040;padding:6px;vertical-align:top;text-align:left}}small{{color:#9a93a8}}audio{{width:170px}}</style>
<h1>Voces de Piper para Luchi</h1><p>Mismas frases con cada voz. RTF = tiempo de síntesis / duración del audio (menor es mejor).</p>
<table><tr><th>Frase</th>{cab}</tr>{filas}</table>""",
        encoding="utf-8",
    )
    print(f"\nAbrí {SALIDA / 'index.html'}")


if __name__ == "__main__":
    main()
