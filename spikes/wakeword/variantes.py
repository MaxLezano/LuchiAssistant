"""F0-10: mide qué escritura de "Luchi" / "Oye Luchi" pronuncia mejor cada tipo de voz.

Genera N clips por variante con hablantes al azar, los transcribe con Whisper y reporta el
porcentaje que dice la frase esperada. Las mejores variantes van a TEXTOS en generar.py.

Uso (en WSL):  python variantes.py --datos ~/luchi-wakeword/data [--n 40]
"""
import argparse
import random
import tempfile
from pathlib import Path

import calidad
import generar

CANDIDATAS = {
    "luchi": {
        "es": ["Luchi", "Luchi.", "¡Luchi!", "Luchi,", "¿Luchi?", "Lúchi", "Luchí"],
        "en": ["[[ lˈutʃi ]]", "[[ lˈuːtʃi ]]", "[[ lˈutʃiː ]]", "[[ lˈuːtʃiː ]]", "[[ lˈutʃi. ]]", "[[ lˈutʃi! ]]"],
    },
    "oye_luchi": {
        "es": ["Oye Luchi", "Oye, Luchi.", "¡Oye Luchi!", "Oye Luchi,", "Oye, Luchi"],
        "en": ["[[ ˈoʝe lˈutʃi ]]", "[[ ˈoje lˈutʃi ]]", "[[ ˈojɛ lˈutʃi ]]", "[[ ˈoʊjeɪ lˈutʃi ]]",
               "[[ ˈoʊ jˈeɪ lˈutʃi ]]", "[[ ˈo jˈe lˈutʃi ]]", "[[ ˈoʝe, lˈutʃi. ]]"],
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", type=Path, required=True)
    ap.add_argument("--n", type=int, default=40)
    args = ap.parse_args()
    datos = args.datos.expanduser()
    rutas = {v: generar.descargar(datos, a, r) for v, (a, r, _, _) in generar.VOCES.items()}
    rng = random.Random(7)
    es = [v for v in generar.VOCES if generar.VOCES[v][3] == "es"]
    with tempfile.TemporaryDirectory() as tmp:
        for clase, por_idioma in CANDIDATAS.items():
            for idioma, textos in por_idioma.items():
                for texto in textos:
                    aciertos, por_voz = 0, {}
                    for i in range(args.n):
                        v = "libritts" if idioma == "en" else rng.choice(es)
                        h = rng.randrange(800) if v == "libritts" else rng.randrange(generar.VOCES[v][2])
                        ls, ns, nw = generar.variacion(rng)
                        wav = Path(tmp) / f"{clase}_{i}.wav"
                        wav.unlink(missing_ok=True)
                        generar.sintetizar((str(wav), str(rutas[v]), texto, h if generar.VOCES[v][2] > 1 else None, ls, ns, nw, i))
                        ok = calidad.aceptar(clase, calidad.transcribir(wav))
                        aciertos += ok
                        a = por_voz.setdefault(v, [0, 0]); a[0] += ok; a[1] += 1
                    det = " ".join(f"{k}:{a}/{t}" for k, (a, t) in sorted(por_voz.items())) if idioma == "es" else ""
                    print(f"{clase:10} {idioma} {aciertos / args.n:5.0%}  {texto:28} {det}", flush=True)


if __name__ == "__main__":
    main()
