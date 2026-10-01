"""Exporta las piezas que usa el prototipo de interfaz (ui/index.html):

- piezas/boca_<estilo>_<pose>.png: la boca de cada estilo en 3 poses (neutral, feliz, hablando), 1024 px.
- piezas/ojos_feliz.png: los ojos cerrados ^ ^ de la pose feliz.
- datos.js: catálogo de assets/luchi/catalogo.json como variable global (los navegadores no dejan
  hacer fetch de archivos locales).

Las capas de cuerpo, ojos, tatuajes y accesorios se toman directo de assets/luchi/.
Uso: python generar_piezas.py   (desde esta carpeta; requiere Pillow)
"""
import json, os, sys
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "mockups", "animaciones"))
import luchi  # noqa: E402

OUT = os.path.join(HERE, "piezas")
os.makedirs(OUT, exist_ok=True)

POSES = {
    "neutral": dict(mouth={"w": 1}),
    "feliz": dict(mouth={"smile": 1}),
    "hablando": dict(mouth={"talk": 1}, talk_open=0.75),
}

def matte(draw):
    """Separa lo dibujado del fondo dibujándolo sobre negro y sobre blanco (alfa exacto)."""
    black = Image.new("RGB", (1024, 1024), (0, 0, 0)); draw(black)
    white = Image.new("RGB", (1024, 1024), (255, 255, 255)); draw(white)
    diff = ImageChops.subtract(white, black).convert("L")
    alpha = diff.point(lambda v: 255 - v)
    out = Image.new("RGBA", (1024, 1024))                 # color = (sobre negro) / alfa
    px_b = black.load(); px_a = alpha.load(); px_o = out.load()
    bbox = alpha.getbbox()
    if bbox:
        for y in range(bbox[1], bbox[3]):
            for x in range(bbox[0], bbox[2]):
                a = px_a[x, y]
                if a:
                    c = px_b[x, y]
                    px_o[x, y] = (min(255, c[0] * 255 // a), min(255, c[1] * 255 // a), min(255, c[2] * 255 // a), a)
    return out

for style in luchi.MOUTH_STYLES:
    luchi.set_style(mouth=style)
    for pose, kw in POSES.items():
        p = dict(luchi.DEFAULT); p.update(kw)
        matte(lambda img: luchi.draw_mouth(img, p)).save(os.path.join(OUT, f"boca_{style}_{pose}.png"), optimize=True)
    print("boca", style)
luchi.set_style()

ink = luchi.Ink()
for c in (luchi.EL, luchi.ER):
    ink.arc((c[0], c[1] + 20), 40, 36, 200, 340, 9)
eyes = Image.new("RGBA", (1024, 1024), luchi.INK + (0,)); eyes.putalpha(ink.mask())
eyes.save(os.path.join(OUT, "ojos_feliz.png"), optimize=True)

with open(os.path.join(ROOT, "assets", "luchi", "catalogo.json"), encoding="utf-8") as fh:
    cat = json.load(fh)
with open(os.path.join(HERE, "datos.js"), "w", encoding="utf-8") as fh:
    fh.write("// Generado por generar_piezas.py a partir de assets/luchi/catalogo.json\n")
    fh.write("window.LUCHI = " + json.dumps(cat, ensure_ascii=False) + ";\n")
print("ok")
