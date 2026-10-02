"""Spike F0-09: pronunciar nombres en inglés dentro de frases en español.

Compara tres variantes con la voz elegida:
  1. texto tal cual (espeak lo lee con reglas del español);
  2. reescritura fonética a mano ("Jólou Náit");
  3. fonemas generados con espeak en inglés e insertados con la sintaxis [[ ]] de Piper.
Uso: cd spikes/piper && uv run python ingles.py  →  output/ingles.html
"""
import html
import pathlib
import wave

from piper import PiperVoice
from piper.phonemize_espeak import EspeakPhonemizer
from piper.voice import ESPEAK_DATA_DIR

VOZ = pathlib.Path(r"E:\Luchi\models\piper\es_AR-daniela-high.onnx")
SALIDA = pathlib.Path(__file__).parent / "output"

CASOS = [
    ("Abriendo {}.", "Hollow Knight", "Jólou Náit"),
    ("Encontré dos: {} y {}. ¿Cuál querés abrir?", ("Hollow Knight", "Hollow Knight Silksong"), ("Jólou Náit", "Jólou Náit Sílksong")),
    ("Poniendo música de {}.", "Daft Punk", "Daft Pank"),
    ("Abriendo {} en la tele.", "Netflix", "Nétflix"),
    ("Abriendo {}.", "League of Legends", "Lig of Léyends"),
]


def en_fonemas(espeak: EspeakPhonemizer, texto: str) -> str:
    """Fonemas en inglés para cada palabra, en el formato [[ ]] que acepta Piper."""
    frases = espeak.phonemize("en-us", texto)
    return "[[ " + " ".join("".join(f) for f in frases) + " ]]"


def main():
    SALIDA.mkdir(exist_ok=True)
    voz = PiperVoice.load(VOZ)
    espeak = EspeakPhonemizer(ESPEAK_DATA_DIR)
    filas = []
    for i, (plantilla, nombres, reescritos) in enumerate(CASOS):
        # Solo se pasan a inglés los nombres; las palabras en castellano de la frase no se tocan.
        nombres = nombres if isinstance(nombres, tuple) else (nombres,)
        reescritos = reescritos if isinstance(reescritos, tuple) else (reescritos,)
        nombre = " / ".join(nombres)
        variantes = [
            ("tal cual", plantilla.format(*nombres)),
            ("reescrito", plantilla.format(*reescritos)),
            ("fonemas en inglés", plantilla.format(*(en_fonemas(espeak, n) for n in nombres))),
        ]
        celdas = []
        for j, (_, texto) in enumerate(variantes):
            archivo = SALIDA / f"ingles_{i}_{j}.wav"
            with wave.open(str(archivo), "wb") as wf:
                voz.synthesize_wav(texto, wf)
            celdas.append(f'<td><audio controls preload="none" src="{archivo.name}"></audio><br><small>{html.escape(texto)}</small></td>')
        filas.append(f"<tr><th>{html.escape(nombre)}</th>{''.join(celdas)}</tr>")
        print(f"{nombre}: {variantes[2][1]}")
    (SALIDA / "ingles.html").write_text(
        f"""<!doctype html><meta charset="utf-8"><title>Nombres en inglés</title>
<style>body{{font:14px Segoe UI,sans-serif;background:#13141b;color:#ece8f0;padding:16px}}table{{border-collapse:collapse}}
td,th{{border:1px solid #2c3040;padding:6px;vertical-align:top;text-align:left}}small{{color:#9a93a8}}audio{{width:200px}}</style>
<h1>Nombres en inglés con la voz de daniela</h1>
<table><tr><th>Nombre</th><th>1 · tal cual</th><th>2 · reescrito a mano</th><th>3 · fonemas en inglés</th></tr>{''.join(filas)}</table>""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
