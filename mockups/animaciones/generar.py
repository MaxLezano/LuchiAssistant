"""Exporta las animaciones y el catálogo de personalización de Luchi.

Uso: python generar.py [anim] [catalogo] [presets] [assets] [<emoción> ...] [--frames]   (requiere Pillow)
  sin argumentos   genera todo
  anim             las 16 animaciones (webp) + emociones.png
  assets           capas listas para la app + catalogo.json (../../assets/luchi/)
  catalogo         hojas de colores, ojos, bocas, tatuajes y accesorios (../personalizacion/)
  presets          Luchis de ejemplo animados (../personalizacion/presets/)
  <emoción>        solo esa animación (p. ej. enojado)
  --frames         además guarda cada frame como PNG en frames/<emoción>/
"""
import json, math, os, shutil, sys
from PIL import Image, ImageDraw
import luchi, tatuajes, accesorios
from luchi import face, render, set_style, font, EXTRA, COLORS, color_hex, MOUTH_STYLES, ACCESSORIES, EYE_SIZE
from animaciones import ANIMS, KEY_POSES, FPS, EMOTIONS

HERE = os.path.dirname(os.path.abspath(__file__))
CAT = os.path.join(os.path.dirname(HERE), "personalizacion")
ASSETS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "assets", "luchi")

def save_webp(frames, path):
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=round(1000 / FPS),
                   loop=0, quality=92, alpha_quality=100, method=4)

CROP = (36, 70, 476, 450)          # cuerpo completo
FACE = (120, 190, 392, 330)        # primer plano de la cara
def tile(img, w=300, crop=CROP):
    c = img.crop(crop); return c.resize((w, int(w * c.height / c.width)), Image.LANCZOS)

def grid(cells, cols, path, col_titles=None, row_titles=None, w=300, crop=CROP):
    """cells: lista de (etiqueta, imagen512). Fondo transparente."""
    th = int(w * (crop[3] - crop[1]) / (crop[2] - crop[0]))
    left = 200 if row_titles else 0; top = 44 if col_titles else 0
    rows = math.ceil(len(cells) / cols)
    sh = Image.new("RGBA", (left + cols * w, top + rows * (th + 30)), (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    f, fb = font("segoeui.ttf", 20), font("segoeuib.ttf", 21)
    for i, t in enumerate(col_titles or []):
        d.text((left + i * w + w / 2, 22), t, font=fb, fill=EXTRA + (255,), anchor="mm")
    for r, t in enumerate(row_titles or []):
        d.text((left - 16, top + r * (th + 30) + th / 2), t, font=fb, fill=EXTRA + (255,), anchor="rm")
    for i, (label, img) in enumerate(cells):
        x, y = left + (i % cols) * w, top + (i // cols) * (th + 30)
        sh.alpha_composite(tile(img, w, crop), (x, y))
        if label: d.text((x + w / 2, y + th + 12), label, font=f, fill=EXTRA + (255,), anchor="mm")
    sh.save(path)

POSE = {n: (p, rk) for n, p, rk in KEY_POSES}
def pose(name): p, rk = POSE[name]; return render(face(**p), lift=3, **rk)

# ---------------------------------------------------------------- emociones
def export_anims(only=(), save_frames=False):
    set_style()
    for name, fn in ANIMS.items():
        if only and name not in only: continue
        frames = fn()
        if save_frames:
            d = os.path.join(HERE, "frames", name); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
            for i, f in enumerate(frames): f.save(os.path.join(d, f"{i:03d}.png"))
        save_webp(frames, os.path.join(HERE, f"{name}.webp"))
        print(f"  {name}: {len(frames)} frames ({len(frames) / FPS:.1f} s)")
    grid([(n, pose(n)) for n, _, _ in KEY_POSES], 5, os.path.join(HERE, "emociones.png"))
    print("  emociones.png")

# ---------------------------------------------------------------- catálogo
EYE_LABELS = {"brillo": "brillo", "punto": "punto", "ovalo": "óvalo", "pestanas": "pestañas",
              "estrellados": "estrellados", "gatunos": "gatunos"}
MOUTH_LABELS = {"linea": "línea", "gruesa": "gruesa", "dientes": "dientes", "colmillo": "colmillo",
                "labios": "labios pintados", "lengua": "lengua"}
TATTOO_LABELS = {"codigo": "</>", "llaves": "{ }", "punto_y_coma": "punto y coma", "404": "404",
                 "sudo": "sudo", "hola_mundo": "Hola, Mundo!", "bug": "bug", "cafe": "café",
                 "git": "git", "corazon": "<3"}
ACC_LABELS = {k: v[0] for k, v in accesorios.INFO.items()}
SEASON_LABELS = {"cumpleanos": "cumpleaños", "navidad": "Navidad", "halloween": "Halloween",
                 "san_valentin": "San Valentín", "verano": "verano", "graduacion": "graduación"}

def export_catalog():
    os.makedirs(CAT, exist_ok=True)
    # colores
    cells = []
    for c in COLORS:
        set_style(color=c); cells.append((f"{c}  {color_hex(c)}", pose("neutral")))
    grid(cells, 5, os.path.join(CAT, "colores.png")); print("  colores.png")
    # ojos x emociones (los párpados, la mirada y los ojos cerrados funcionan con todos los estilos)
    emo = ["neutral", "feliz", "pensando", "enojado", "cansado"]
    cells = []
    for e in EYE_SIZE:
        set_style(eyes=e); cells += [("", pose(n)) for n in emo]
    grid(cells, len(emo), os.path.join(CAT, "ojos.png"), col_titles=emo,
         row_titles=[EYE_LABELS[e] for e in EYE_SIZE], w=260, crop=FACE); print("  ojos.png")
    # bocas x emociones
    emo_m = [("neutral", {}), ("feliz", dict(mouth={"smile": 1})), ("hablando", dict(mouth={"talk": 1}, talk_open=0.85)),
             ("apenado", dict(mouth={"frown": 1})), ("bostezo", dict(mouth={"yawn": 1}, yawn=0.8))]
    cells = []
    for m in MOUTH_STYLES:
        set_style(mouth=m); cells += [("", render(face(**p), lift=3)) for _, p in emo_m]
    grid(cells, len(emo_m), os.path.join(CAT, "bocas.png"), col_titles=[n for n, _ in emo_m],
         row_titles=[MOUTH_LABELS[m] for m in MOUTH_STYLES], w=260, crop=FACE); print("  bocas.png")
    # tatuajes: patrones de cuerpo completo, flash y combinaciones
    cells = []
    for p_, (label, _) in tatuajes.PATTERNS.items():
        set_style(pattern=p_); cells.append((label, pose("neutral")))
    grid(cells, 4, os.path.join(CAT, "tatuajes_patrones.png")); print("  tatuajes_patrones.png")
    cells = []
    for fid, (label, _, cat) in tatuajes.FLASH.items():
        set_style(flash=((fid, "panza_der"),)); cells.append((label, pose("neutral")))
    grid(cells, 5, os.path.join(CAT, "tatuajes_flash.png")); print("  tatuajes_flash.png")
    combos = [("olas + Mamá + estrella", dict(pattern="olas", flash=(("mama", "panza_der"), ("estrella", "frente")))),
              ("circuito + </>", dict(pattern="circuito", flash=(("codigo", "panza_der"),))),
              ("ancla + calaverita + rayo", dict(flash=(("ancla", "panza_izq"), ("calavera", "panza_der"), ("rayo", "costado_der")))),
              ("constelaciones (azul)", dict(pattern="constelaciones", color="azul")),
              ("sakura + monte Fuji", dict(pattern="sakura", flash=(("fuji", "panza_izq"),))),
              ("tigre + onigiri (naranja)", dict(pattern="tigre", color="naranja", flash=(("onigiri", "frente"),)))]
    cells = []
    for label, st in combos:
        set_style(**st); cells.append((label, pose("neutral")))
    grid(cells, 3, os.path.join(CAT, "tatuajes_combinados.png")); print("  tatuajes_combinados.png")
    # accesorios, agrupados por categoría
    for cat, title in (("diario", "diario"), ("divertido", "divertidos"), ("temporada", "de temporada")):
        cells = []
        for a, (label, c, season, _, _) in accesorios.INFO.items():
            if c != cat: continue
            set_style(accessory=a); cells.append((label + (f" · {SEASON_LABELS[season]}" if season else ""), pose("neutral")))
        cols = 4 if cat == "temporada" else 5
        grid(cells, cols, os.path.join(CAT, f"accesorios_{cat}.png"), w=320 if cat == "temporada" else 260,
             crop=(36, 8, 476, 450))                                # más aire arriba para los accesorios altos
        print(f"  accesorios_{cat}.png")
    set_style()

PRESETS = {
    "clasica":  dict(),
    "dev":      dict(color="azul", eyes="punto", mouth="colmillo", pattern="circuito",
                     flash=(("codigo", "panza_der"),), accessory="lentes"),
    "gamer":    dict(color="violeta", eyes="estrellados", mouth="dientes",
                     flash=(("sudo", "panza_der"), ("rayo", "frente")), accessory="auriculares"),
    "sakura":   dict(color="rosa", eyes="pestanas", mouth="labios", pattern="sakura", accessory="sakura"),
    "brote":    dict(color="menta", eyes="brillo", mouth="lengua",
                     flash=(("cafe", "panza_der"), ("onigiri", "panza_izq")), accessory="brote"),
    "reina":    dict(color="amarillo", eyes="gatunos", mouth="colmillo", pattern="llamas",
                     flash=(("estrella", "frente"),), accessory="corona"),
    "rockera":  dict(color="nube", eyes="ovalo", mouth="gruesa", pattern="tribal",
                     flash=(("calavera", "panza_der"), ("mama", "frente"))),
    "ninja":    dict(color="celeste", eyes="punto", mouth="linea", pattern="olas", accessory="hachimaki"),
    "fiesta":   dict(color="naranja", eyes="estrellados", mouth="lengua", flash=(("estrella", "panza_der"),),
                     accessory="gorro_fiesta"),
}

def export_presets():
    d = os.path.join(CAT, "presets"); os.makedirs(d, exist_ok=True)
    cells = []
    for name, st in PRESETS.items():
        set_style(**st)
        save_webp(ANIMS["hablando"](), os.path.join(d, f"{name}.webp"))
        cells.append((name, pose("feliz")))
        print(f"  presets/{name}.webp")
    grid(cells, 3, os.path.join(CAT, "presets.png")); print("  presets.png")
    set_style()

# ---------------------------------------------------------------- assets para la app
def _save(img, *parts):
    path = os.path.join(ASSETS, *parts); os.makedirs(os.path.dirname(path), exist_ok=True); img.save(path, optimize=True)
    return "/".join(parts)

def export_assets():
    """Capas sueltas + catalogo.json: lo que la app necesita para dibujar y personalizar a Luchi."""
    for sub in ("cuerpo", "ojos", "accesorios", "tatuajes"):   # el README.md de la carpeta se conserva
        shutil.rmtree(os.path.join(ASSETS, sub), ignore_errors=True)
    mask = luchi.BODY
    _save(mask, "cuerpo", "mascara.png")
    colors = []
    for cid, (h, sa, v) in COLORS.items():
        body = luchi.body_base(cid).convert("RGBA"); body.putalpha(mask)
        colors.append(dict(id=cid, hex=color_hex(cid), tono=h, saturacion=sa, brillo=v,
                           archivo=_save(body, "cuerpo", f"{cid}.png")))
    eyes = [dict(id=eid, nombre=EYE_LABELS[eid], ancho=w, alto=h,
                 archivos={"izq": _save(luchi.eye_sprite(eid, "l"), "ojos", f"{eid}_izq.png"),
                           "der": _save(luchi.eye_sprite(eid, "r"), "ojos", f"{eid}_der.png")})
            for eid, (w, h) in EYE_SIZE.items()]
    accs = [dict(id=a, nombre=label, categoria=cat, temporada=season, tapa_ojos=a in accesorios.COVERS_EYES,
                 archivo=_save(luchi.accessory_layer(a), "accesorios", f"{a}.png"))
            for a, (label, cat, season, _, _) in accesorios.INFO.items()]
    pats = [dict(id=p_, nombre=label, archivo=_save(tatuajes.ink_layer(p_), "tatuajes", "patrones", f"{p_}.png"))
            for p_, (label, _) in tatuajes.PATTERNS.items()]
    flash = []
    for fid, (label, fn, cat) in tatuajes.FLASH.items():
        cv = tatuajes.Canvas(); fn(cv, 512, 512, 1.0)
        flash.append(dict(id=fid, nombre=label, categoria=cat,
                          archivo=_save(cv.done().crop((412, 412, 612, 612)), "tatuajes", "flash", f"{fid}.png")))
    _save(tatuajes._noise(), "tatuajes", "ruido.png")
    _save(tatuajes._face_clear(), "tatuajes", "mascara_cara.png")
    catalog = {
        "version": 1,
        "espacio": {
            "tamano": 1024,
            "cuerpo": {"izq": luchi.L, "der": luchi.R, "arriba": luchi.T, "abajo": luchi.B, "superelipse_n": luchi.N},
            "ojo_izq": list(luchi.EL), "ojo_der": list(luchi.ER), "boca": [511, 575],
            "mejillas": [[340, 567], [682, 567]], "sprite_ojo": luchi.ES,
            "recorte_con_accesorios": list(luchi.EXT),
        },
        "colores": colors,
        "mejillas": [dict(id=k, rgb=v) for k, v in luchi.BLUSHES.items()],
        "ojos": eyes,
        "bocas": [dict(id=m, nombre=MOUTH_LABELS[m]) for m in MOUTH_STYLES],
        "tatuajes": {
            "max_flash": tatuajes.MAX_FLASH,
            "posiciones": {k: dict(x=x, y=y, escala=sc) for k, (x, y, sc) in tatuajes.SLOTS.items()},
            "patrones": pats,
            "flash": flash,
            "realismo": {"modo_fusion": "multiply", "desenfoque_px": 0.9, "ruido": "tatuajes/ruido.png",
                         "opacidad": 0.9, "corrido": {"desenfoque_px": 3, "opacidad": 0.18},
                         "tinte_tinta": list(tatuajes.NAVY), "tinte_mezcla": 0.12,
                         "mascara_cara_patrones": "tatuajes/mascara_cara.png"},
        },
        "accesorios": accs,
        "temporadas": accesorios.SEASONS,
        "expresion_por_defecto": luchi.DEFAULT,
        "emociones": [dict(id=k, nombre=n, tipo=t, disparador=d) for k, (n, t, d) in EMOTIONS.items()],
        "presets": {k: {kk: ([list(x) for x in vv] if kk == "flash" else vv) for kk, vv in v.items()} for k, v in PRESETS.items()},
        "diseno_usuario_ejemplo": {"version": 1, "color": "azul", "blush": "rosa", "eyes": "punto", "mouth": "colmillo",
                                   "pattern": "circuito", "flash": [["codigo", "panza_der"]], "accessory": "lentes"},
    }
    with open(os.path.join(ASSETS, "catalogo.json"), "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=2)
    print(f"  {len(colors)} cuerpos, {len(eyes) * 2} ojos, {len(accs)} accesorios, {len(pats)} patrones, {len(flash)} flash, catalogo.json")

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    save_frames = "--frames" in sys.argv
    names = [a for a in args if a in ANIMS]
    todo = not args
    if todo or "anim" in args or names:
        print("emociones"); export_anims(names, save_frames)
    if todo or "catalogo" in args:
        print("catálogo"); export_catalog()
    if todo or "presets" in args:
        print("presets"); export_presets()
    if todo or "assets" in args:
        print("assets"); export_assets()
    print("ok")
