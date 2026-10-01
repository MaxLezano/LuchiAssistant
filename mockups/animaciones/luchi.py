"""Renderer de Luchi: cuerpo + cara paramétrica + estilo personalizable.

Dos capas de datos, separadas a propósito:
- Parámetros de EXPRESIÓN (cambian cada frame): apertura de ojos, mirada, boca, cejas, párpados...
  Las animaciones solo tocan esto.
- ESTILO (lo elige el usuario): color, mejillas, ojos, boca, tatuaje, accesorio.
  Cualquier estilo responde a los mismos parámetros, así todas las animaciones funcionan con todos.
"""
import math, os
from dataclasses import dataclass, replace
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_SIZE = 512
K = 2                      # supersampling del lienzo
CAN = OUT_SIZE * K

ORIG = Image.open(os.path.join(HERE, "fuentes", "11_mochi_squircle_3.png")).convert("RGB")
BLANK = Image.open(os.path.join(HERE, "fuentes", "22_luchi_sin_cara.png")).convert("RGB")

INK = (22, 18, 20)
WHITE = (252, 250, 247)
EXTRA = (150, 132, 175)    # adornos: lavanda media, se lee en fondos claros y oscuros
EL, ER, EY = (353, 478), (668, 478), 478

# ================================================================ utilidades
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(a, b, x):
    t = clamp((x - a) / (b - a)) if b != a else float(x >= b)
    return t * t * (3 - 2 * t)
def ease_io(t): t = clamp(t); return 0.5 - 0.5 * math.cos(math.pi * t)
def bump(t, a, b, fade=0.15):
    """1 entre a y b, con entradas y salidas suaves de duración fade."""
    return smooth(a, a + fade, t) * (1 - smooth(b - fade, b, t))

def font(name, size):
    try: return ImageFont.truetype("C:/Windows/Fonts/" + name, size)
    except OSError: return ImageFont.load_default()

class Ink:
    """Capa de tinta con supersampling: líneas con puntas redondas, polígonos, elipses."""
    SS = 2
    def __init__(self, size=1024):
        self.size = size
        self.l = Image.new("L", (size * self.SS, size * self.SS), 0); self.d = ImageDraw.Draw(self.l)
    def _p(self, pts): return [(x * self.SS, y * self.SS) for x, y in pts]
    def line(self, pts, w=7, a=1.0):
        if a <= 0.01 or len(pts) < 2: return
        f = int(255 * a); p = self._p(pts); r = w * self.SS / 2
        self.d.line(p, fill=f, width=max(1, int(w * self.SS)), joint="curve")
        for x, y in (p[0], p[-1]): self.d.ellipse((x - r, y - r, x + r, y + r), fill=f)
    def arc(self, c, rx, ry, a0, a1, w=7, a=1.0, n=28):
        self.line([(c[0] + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                    c[1] + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)], w, a)
    def poly(self, pts, a=1.0):
        if a > 0.01 and len(pts) > 2: self.d.polygon(self._p(pts), fill=int(255 * a))
    def ellipse(self, box, a=1.0, outline=None):
        if a <= 0.01: return
        b = [v * self.SS for v in box]
        if outline: self.d.ellipse(b, outline=int(255 * a), width=int(outline * self.SS))
        else: self.d.ellipse(b, fill=int(255 * a))
    def text(self, xy, s, fnt, anchor="mm"):
        self.d.text((xy[0] * self.SS, xy[1] * self.SS), s, font=fnt, fill=255, anchor=anchor)
    def mask(self): return self.l.resize((self.size, self.size), Image.LANCZOS)
    def apply(self, img, color=INK):
        img.paste(Image.new("RGB", img.size, color), (0, 0), self.mask())

def heart_pts(c, r, n=64):
    pts = []
    for i in range(n):
        t = math.tau * i / n
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((c[0] + x * r / 16, c[1] + y * r / 16))
    return pts

def star_pts(c, r, points=5, inner=0.45, rot=-90):
    return [(c[0] + (r if i % 2 == 0 else r * inner) * math.cos(math.radians(rot + 180 * i / points)),
             c[1] + (r if i % 2 == 0 else r * inner) * math.sin(math.radians(rot + 180 * i / points)))
            for i in range(points * 2)]

# ================================================================ estilo
@dataclass(frozen=True)
class Style:
    color: str = "rosa"
    blush: str = "rosa"
    eyes: str = "brillo"
    mouth: str = "linea"
    pattern: str = "ninguno"                 # tatuaje de cuerpo completo
    flash: tuple = ()                        # tatuajes chicos: ((nombre, slot), ...), hasta 3
    accessory: str = "ninguno"

STYLE = Style()
def set_style(**kw):
    global STYLE
    STYLE = replace(Style(), **kw)

# colores del cuerpo: tono (0-1), multiplicador de saturación, de brillo
COLORS = {
    "rosa":     (None, 1.0, 1.0),
    "rojo":     (0.985, 2.3, 0.98),
    "naranja":  (0.065, 2.0, 1.0),
    "amarillo": (0.14, 2.0, 1.0),
    "verde":    (0.30, 1.6, 0.97),
    "menta":    (0.45, 1.25, 1.0),
    "celeste":  (0.54, 1.35, 1.0),
    "azul":     (0.62, 1.9, 0.96),
    "violeta":  (0.76, 1.6, 0.97),
    "nube":     (0.0, 0.0, 0.96),
}
BLUSHES = {"rosa": (240, 165, 175), "coral": (245, 150, 130), "durazno": (250, 190, 150),
           "lavanda": (200, 170, 235), "ninguno": None}

# ================================================================ cuerpo base
def _clean_blank():
    base = BLANK.copy(); o = ORIG.load()
    mask = Image.new("L", (1024, 1024), 0)
    ImageDraw.Draw(mask).rounded_rectangle((268, 395, 758, 630), radius=90, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(14))
    grad = Image.new("RGB", (1024, 1024)); g = grad.load()
    for y in range(1024):
        c1, c2 = o[235, y], o[790, y]
        for x in range(1024):
            t = clamp((x - 235) / 555)
            g[x, y] = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
    grad = grad.filter(ImageFilter.GaussianBlur(10))
    tex = ImageChops.subtract(base, base.filter(ImageFilter.GaussianBlur(3)), offset=128)
    return Image.composite(ImageChops.add(grad, tex, offset=-128), base, mask)

BASE = _clean_blank()
_TINT = {}
def body_base(color=None):
    """Cuerpo sin cara en el color pedido: cambia el tono y conserva brillo y textura."""
    color = color or STYLE.color
    if color not in _TINT:
        hue, sat, val = COLORS[color]
        if hue is None: _TINT[color] = BASE
        else:
            h, s, v = BASE.convert("HSV").split()
            h = Image.new("L", BASE.size, int(hue * 255) % 256)
            s = s.point(lambda x: min(255, int(x * sat)))
            v = v.point(lambda x: min(255, int(x * val)))
            _TINT[color] = Image.merge("HSV", (h, s, v)).convert("RGB")
    return _TINT[color]

def color_hex(color):
    r, g, b = body_base(color).getpixel((511, 765)); return f"#{r:02x}{g:02x}{b:02x}"

# ================================================================ ojos (sprites por estilo)
ES = 140                    # tamaño del sprite de ojo; centro en (70, 70)
EYE_SIZE = {"brillo": (94, 94), "punto": (60, 60), "ovalo": (62, 94), "pestanas": (94, 94),
            "estrellados": (102, 102), "gatunos": (96, 70)}
_EYES = {}

def _sprite_canvas(): return Image.new("RGBA", (ES * 3, ES * 3), (0, 0, 0, 0))
def _down(im): return im.resize((ES, ES), Image.LANCZOS)

def eye_sprite(style, side):
    key = (style, side)
    if key in _EYES: return _EYES[key]
    c = ES * 3 / 2; S = 3
    if style in ("brillo", "pestanas"):
        spr = Image.new("RGBA", (ES, ES), (0, 0, 0, 0))
        crop = ORIG.crop((EL[0] - 52, EY - 52, EL[0] + 52, EY + 52)).convert("RGBA")
        m = Image.new("L", (104, 104), 0); ImageDraw.Draw(m).ellipse((5, 5, 99, 99), fill=255)
        crop.putalpha(m.filter(ImageFilter.GaussianBlur(1)))
        spr.alpha_composite(crop, (18, 18))
        if style == "pestanas":
            lay = _sprite_canvas(); d = ImageDraw.Draw(lay)
            sg = 1 if side == "r" else -1
            for ang in (-18, -42, -66):
                a = math.radians(ang)
                x0, y0 = c + sg * 44 * S * math.cos(a), c + 44 * S * math.sin(a)
                x1, y1 = c + sg * 64 * S * math.cos(a - 0.15), c + 64 * S * math.sin(a - 0.15)
                d.line((x0, y0, x1, y1), fill=INK + (255,), width=6 * S)
                d.ellipse((x1 - 3 * S, y1 - 3 * S, x1 + 3 * S, y1 + 3 * S), fill=INK + (255,))
            spr.alpha_composite(_down(lay))
    else:
        lay = _sprite_canvas(); d = ImageDraw.Draw(lay)
        if style == "punto":
            r = 30 * S; d.ellipse((c - r, c - r, c + r, c + r), fill=INK + (255,))
        elif style == "ovalo":
            d.ellipse((c - 31 * S, c - 47 * S, c + 31 * S, c + 47 * S), fill=INK + (255,))
            d.ellipse((c + 2 * S, c - 36 * S, c + 22 * S, c - 14 * S), fill=WHITE + (255,))
            d.ellipse((c - 16 * S, c + 18 * S, c - 6 * S, c + 28 * S), fill=WHITE + (255,))
        elif style == "estrellados":
            r = 51 * S
            for i in range(r, 0, -S):                                  # degradado vertical
                t = 1 - i / r
                col = tuple(int(INK[k] * (1 - t) + (78, 52, 120)[k] * t) for k in range(3))
                d.ellipse((c - i, c - r + (r - i) * 1.6, c + i, c + r), fill=col + (255,))
            d.polygon(star_pts((c + 16 * S, c - 18 * S), 17 * S, 4, 0.32, -90), fill=WHITE + (255,))
            d.ellipse((c - 26 * S, c + 14 * S, c - 14 * S, c + 26 * S), fill=WHITE + (255,))
            d.ellipse((c + 20 * S, c + 18 * S, c + 26 * S, c + 24 * S), fill=WHITE + (230,))
        elif style == "gatunos":
            w, h = 48 * S, 35 * S
            pts = [(c + w * math.cos(t), c + h * math.sin(t) * (0.75 + 0.25 * abs(math.cos(t))))
                   for t in [math.tau * i / 80 for i in range(80)]]
            d.polygon(pts, fill=(226, 168, 62, 255))
            d.ellipse((c - 24 * S, c - 14 * S, c + 24 * S, c + 35 * S), fill=(240, 196, 92, 255))
            d.polygon(pts, outline=INK + (255,), width=6 * S)
            d.ellipse((c - 7 * S, c - 30 * S, c + 7 * S, c + 30 * S), fill=INK + (255,))
            d.ellipse((c + 12 * S, c - 22 * S, c + 24 * S, c - 10 * S), fill=WHITE + (255,))
        spr = _down(lay)
    _EYES[key] = spr
    return spr

# ================================================================ bocas como contornos
MOUTH_N = 48

def _stroke(center, w):
    """Línea de grosor w -> (borde superior, borde inferior) con las normales."""
    top, bot = [], []
    for i, (x, y) in enumerate(center):
        x0, y0 = center[max(i - 1, 0)]; x1, y1 = center[min(i + 1, len(center) - 1)]
        dx, dy = x1 - x0, y1 - y0; n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n * w / 2, dx / n * w / 2
        top.append((x - nx, y - ny)); bot.append((x + nx, y + ny))
    return top, bot

def _filled(cx, cy, rx, ry_top, ry_bot):
    top, bot = [], []
    for i in range(MOUTH_N):
        th = math.pi * (1 - i / (MOUTH_N - 1))
        x = cx + rx * math.cos(th); s_ = math.sin(th)
        top.append((x, cy - ry_top * s_)); bot.append((x, cy + ry_bot * s_))
    return top, bot

def _arc_center(cx, cy, rx, ry, a0, a1):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / (MOUTH_N - 1))),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / (MOUTH_N - 1)))) for i in range(MOUTH_N)]

def _u(i): return i / (MOUTH_N - 1)

def mouth_shape(name, mx, my, p, w):
    if name == "w":
        return _stroke([(mx - 70 + 140 * _u(i), my + 14 * abs(math.sin(2 * math.pi * _u(i)))) for i in range(MOUTH_N)], w)
    if name == "smile": return _stroke(_arc_center(mx, my - 16, 46, 34, 160, 20), w)
    if name == "frown": return _stroke(_arc_center(mx, my + 26, 32, 18, 200, 340), w)
    if name == "flat": return _stroke([(mx - 26 + 52 * _u(i), my + 6 - 3 * _u(i)) for i in range(MOUTH_N)], w)
    if name == "wavy":
        ph = p["wave_phase"]
        return _stroke([(mx - 44 + 88 * _u(i), my + 4 + 7 * math.sin(math.tau * (1.5 * _u(i) + ph))) for i in range(MOUTH_N)], w)
    if name == "angry":
        return _stroke(_arc_center(mx, my + 22, 26, 10, 200, 340), w)
    if name == "grin":
        top = [(mx - 44 + 88 * _u(i), my - 6 - 8 * (1 - math.sin(math.pi * _u(i)))) for i in range(MOUTH_N)]
        bot = [(x, y + 32 * math.sin(math.pi * _u(i))) for i, (x, y) in enumerate(top)]
        return top, bot
    if name == "dot": return _filled(mx, my, 12, 9, 9)
    if name == "talk":
        h = 8 + 40 * p["talk_open"]; return _filled(mx, my + 4, 28, h / 2, h / 2)
    if name == "o":
        r = 14 + 6 * p["o_size"]; return _filled(mx, my, r, r * 1.15, r * 1.15)
    if name == "yawn":
        y = p["yawn"]; return _filled(mx, my + 8, 18 + 16 * y, 10 + 30 * y, 10 + 30 * y)
    raise ValueError(name)

MOUTH_STYLES = ["linea", "gruesa", "dientes", "colmillo", "labios", "lengua"]
LIPS = (205, 55, 88)
TONGUE = (236, 112, 132)

def mouth_outline(weights, mx, my, p):
    st = STYLE.mouth
    w = 11 if st == "gruesa" else 10 if st == "labios" else 7
    if st == "dientes": weights = {("grin" if k == "smile" else k): v for k, v in weights.items()}
    tot = sum(v for v in weights.values() if v > 0) or 1
    top = [(0.0, 0.0)] * MOUTH_N; bot = [(0.0, 0.0)] * MOUTH_N
    for name, wgt in weights.items():
        if wgt <= 0: continue
        t2, b2 = mouth_shape(name, mx, my, p, w); f = wgt / tot
        top = [(a[0] + f * b[0], a[1] + f * b[1]) for a, b in zip(top, t2)]
        bot = [(a[0] + f * b[0], a[1] + f * b[1]) for a, b in zip(bot, b2)]
    return top, bot

def _caps(ink, top, bot):
    for i in (0, -1):
        (x1, y1), (x2, y2) = top[i], bot[i]
        r = math.hypot(x2 - x1, y2 - y1) / 2
        if r > 0.5: ink.ellipse(((x1 + x2) / 2 - r, (y1 + y2) / 2 - r, (x1 + x2) / 2 + r, (y1 + y2) / 2 + r))

def _clip_paste(img, mask_shape, mask_clip, color):
    m = ImageChops.multiply(mask_shape, mask_clip)
    img.paste(Image.new("RGB", img.size, color), (0, 0), m)

def draw_mouth(img, p):
    st = STYLE.mouth
    mx = 511 + p["look_x"] * 0.4; my = 575
    top, bot = mouth_outline(p["mouth"], mx, my, p)
    thick = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(top, bot)]
    open_ = max(thick) > 13                     # boca abierta (rellena) vs. línea

    ink = Ink(); ink.poly(top + bot[::-1]); _caps(ink, top, bot)
    mouth_mask = ink.mask()
    img.paste(Image.new("RGB", img.size, LIPS if st == "labios" else INK), (0, 0), mouth_mask)

    if st == "labios" and open_:                # interior oscuro dentro del labio
        inner = Ink(); it, ib = [], []
        for (a, b), th in zip(zip(top, bot), thick):
            k = clamp((th - 10) / th) if th > 10 else 0
            mxp, myp = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            it.append((mxp + (a[0] - mxp) * k, myp + (a[1] - myp) * k))
            ib.append((mxp + (b[0] - mxp) * k, myp + (b[1] - myp) * k))
        inner.poly(it + ib[::-1]); inner.apply(img, (70, 22, 34))
        gl = Ink(); gl.arc((mx + 8, my - 2), 12, 4, 200, 320, 3); gl.apply(img, (250, 210, 220))

    if st == "dientes" and open_:               # banda de dientes pegada al borde superior
        band = Ink(); bb = []
        for (a, b), th in zip(zip(top, bot), thick):
            k = min(11, th * 0.42) / th if th > 0 else 0
            bb.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
        band.poly(top + bb[::-1])
        _clip_paste(img, band.mask(), mouth_mask, WHITE)
        gaps = Ink()
        for frac in (0.35, 0.5, 0.65):
            i = int(frac * (MOUTH_N - 1)); a, b2 = top[i], bb[i]
            if thick[i] > 13: gaps.line([a, b2], 2)
        _clip_paste(img, gaps.mask(), mouth_mask, (200, 190, 190))

    if st == "colmillo":                        # yaeba: colmillo a un costado
        i = int(0.66 * (MOUTH_N - 1))
        if open_: ax, ay = top[i]; down = 1
        else: ax, ay = bot[i]; down = 1
        tri = [(ax - 7, ay - 1), (ax + 7, ay - 1), (ax + 1, ay + 13 * down)]
        f = Ink(); f.poly(tri); m = f.mask()
        if open_: _clip_paste(img, m, mouth_mask, WHITE)
        else: img.paste(Image.new("RGB", img.size, WHITE), (0, 0), m)
        o = Ink(); o.line([tri[0], tri[2], tri[1]], 3); o.apply(img)

    if st == "lengua":
        i = MOUTH_N // 2
        if open_:
            cx, cy = (top[i][0] + bot[i][0]) / 2, bot[i][1]
            h = thick[i]
            t = Ink(); t.ellipse((cx - 16, cy - h * 0.55, cx + 16, cy + 6))
            _clip_paste(img, t.mask(), mouth_mask, TONGUE)
        else:
            cx, cy = bot[i][0] + 6, bot[i][1] - 2
            t = Ink(); t.ellipse((cx - 13, cy - 6, cx + 13, cy + 20)); t.apply(img, TONGUE)
            o = Ink(); o.arc((cx, cy + 7), 13, 13, 0, 180, 3); o.line([(cx, cy + 1), (cx, cy + 10)], 2); o.apply(img, (150, 60, 75))

# ================================================================ tatuajes (ver tatuajes.py)
import tatuajes

def draw_tattoos(img):
    if STYLE.pattern == "ninguno" and not STYLE.flash: return img
    return tatuajes.apply_ink(img, tatuajes.tattoo_layer_cached(STYLE.pattern, STYLE.flash))

# ================================================================ accesorios (ver accesorios.py)
import accesorios
ACCESSORIES = ["ninguno"] + list(accesorios.INFO)
_ACC = {}

def accessory_layer(name):
    if name not in _ACC: _ACC[name] = accesorios.render(name, BODY)
    return _ACC[name]

# ================================================================ cara paramétrica
DEFAULT = dict(open_l=1.0, open_r=1.0, closed_l="line", closed_r="line", look_x=0.0, look_y=0.0,
               eye_scale=1.0, heart=0.0, heart_scale=1.0, spiral=0.0, spiral_rot=0.0,
               lid_l=0.0, lid_r=0.0, lid_tilt=0.0, blush=1.0,
               brow_sad=0.0, brow_up=0.0, brow_angry=0.0,
               mouth={"w": 1.0}, talk_open=0.0, o_size=0.0, wave_phase=0.0, yawn=0.0, tear=0.0)

def _lid(img, base, cx, cy, ew, eh, cov, tilt, inner_sign, ink):
    """Párpado: tapa la parte superior del ojo con piel y dibuja la línea del párpado.
    tilt > 0 baja el lado interno (enojado); tilt < 0 baja el externo (cansado)."""
    if cov <= 0.01: return
    y0 = cy - eh / 2 + cov * eh
    m = math.tan(math.radians(tilt)) * inner_sign
    yx = lambda x: y0 + (x - cx) * m
    x0, x1 = cx - ew / 2 - 14, cx + ew / 2 + 14
    lid = Ink(); lid.poly([(x0, cy - eh / 2 - 40), (x1, cy - eh / 2 - 40), (x1, yx(x1)), (x0, yx(x0))])
    img.paste(base, (0, 0), lid.mask())
    ink.line([(x0 + 8, yx(x0 + 8)), (x1 - 8, yx(x1 - 8))], 7)

def draw_face(p):
    st = STYLE; base = body_base()
    img = draw_tattoos(base.copy()); ink = Ink()
    blush_col = BLUSHES[st.blush]
    if blush_col:
        lay = Image.new("L", img.size, 0); d = ImageDraw.Draw(lay)
        for cx in (340, 682):
            d.ellipse((cx - 38, 567 - 17, cx + 38, 567 + 17), fill=int(clamp(150 * p["blush"], 0, 255)))
        img.paste(Image.new("RGB", img.size, blush_col), (0, 0), lay.filter(ImageFilter.GaussianBlur(7)))

    ew0, eh0 = EYE_SIZE[st.eyes]
    for side, c in (("l", EL), ("r", ER)):
        o = p["open_" + side]; shape = p["closed_" + side]
        cx, cy = c[0] + p["look_x"], c[1] + p["look_y"]
        s = p["eye_scale"]
        closed = o < 0.2
        if p["heart"] > 0.5:
            ink.poly(heart_pts((cx, cy + 4), 44 * p["heart_scale"]))
        elif p["spiral"] > 0.5:
            rot = math.radians(p["spiral_rot"]) * (1 if side == "r" else -1)
            pts = [(cx + (4 + 36 * t) * math.cos(rot + t * 2.6 * math.tau),
                    cy + (4 + 36 * t) * math.sin(rot + t * 2.6 * math.tau)) for t in [i / 90 for i in range(91)]]
            ink.line(pts, 6)
        elif not closed:
            spr = eye_sprite(st.eyes, side)
            w = max(2, int(ES * s)); h = max(2, int(ES * s * o))
            img.paste(spr.resize((w, h), Image.LANCZOS), (int(cx - w / 2), int(cy - h / 2)),
                      spr.resize((w, h), Image.LANCZOS))
            lid = p["lid_" + side]
            if lid > 0.01:
                _lid(img, base, cx, cy, ew0 * s, eh0 * s * o, lid, p["lid_tilt"], 1 if side == "l" else -1, ink)
        else:
            if shape == "line":
                ink.line([(cx - 38, cy + 4), (cx + 38, cy + 4)], 8)
                if st.eyes == "pestanas":
                    sg = 1 if side == "r" else -1
                    for dx in (26, 38): ink.line([(cx + sg * dx, cy + 6), (cx + sg * (dx + 8), cy + 18)], 5)
            if shape == "happy": ink.arc((cx, cy + 20), 40, 36, 200, 340, 9)
            if shape == "sleep": ink.arc((cx, cy - 6), 36, 18, 20, 160, 8)
            if shape == "squeeze":                                     # > <
                sg = 1 if side == "l" else -1
                ink.line([(cx - 30 * sg, cy - 22), (cx + 26 * sg, cy + 2), (cx - 30 * sg, cy + 24)], 8)

    if p["tear"] > 0.01:                                               # lagrimita (bostezo)
        t = p["tear"]; tx, ty = EL[0] - 48, EY + 16 + 26 * t
        tear = Ink()
        tear.poly([(tx, ty - 16 * t), (tx + 8.5 * t, ty + 1), (tx - 8.5 * t, ty + 1)])
        tear.ellipse((tx - 9 * t, ty - 6 * t, tx + 9 * t, ty + 10 * t)); tear.apply(img, (150, 200, 240))

    k = p["brow_sad"]
    if k > 0.05:
        for c, sg in ((EL, -1), (ER, 1)):
            mxb, myb = c[0] + 4 * sg, EY - 69
            hx, hy = 26 * sg * k, -7 * k
            ink.line([(mxb + hx, myb - hy), (mxb - hx, myb + hy)], 6)
    k = p["brow_angry"]
    if k > 0.05:
        for c, sg in ((EL, -1), (ER, 1)):
            mxb, myb = c[0] - 2 * sg, EY - 66
            hx, hy = 30 * sg * k, 11 * k
            ink.line([(mxb + hx, myb - hy), (mxb - hx, myb + hy)], 9)
    k = p["brow_up"]
    if k > 0.05:
        ink.arc((ER[0] + p["look_x"], EY - 70), 30 * k, 12 * k, 200, 340, 6)
    ink.apply(img)
    draw_mouth(img, p)
    return img

def face(**kw):
    p = dict(DEFAULT); p.update(kw); return draw_face(p)

def mix(a, b, t):
    keys = set(a) | set(b)
    return {k: a.get(k, 0) * (1 - t) + b.get(k, 0) * t for k in keys}

# ================================================================ cuerpo, sprite y lienzo
L, R, T, B, N = 176, 846, 234, 797, 3.3
_cx, _cy, _a, _b = (L + R) / 2, (T + B) / 2, (R - L) / 2, (B - T) / 2
BODY = Image.new("L", (1024, 1024), 0); _px = BODY.load()
for y in range(T - 5, B + 5):
    for x in range(L - 5, R + 5):
        _px[x, y] = 255 if abs((x - _cx) / _a) ** N + abs((y - _cy) / _b) ** N <= 1 else 0
BODY = BODY.filter(ImageFilter.GaussianBlur(1.2))
BODY_BOX_W, BODY_BOX_H = (R - L) + 16, (B - T) + 16
EXT = (L - 8 - 110, T - 8 - 200, R + 8 + 110, B + 8 + 12)      # margen para accesorios
SPR_W, SPR_H = EXT[2] - EXT[0], EXT[3] - EXT[1]
ANCHOR_Y = (B + 8) - EXT[1]
BODY_W = 300 * K
BODY_H = BODY_W * BODY_BOX_H / BODY_BOX_W
GROUND = int(395 * K)

def sprite(img):
    s = img.crop(EXT).convert("RGBA"); s.putalpha(BODY.crop(EXT))
    if STYLE.accessory != "ninguno":
        s.alpha_composite(accessory_layer(STYLE.accessory).crop(EXT))
    return s.convert("RGBa")

def shadow_layers(body, sx, lift, dx=0.0):
    g = Image.new("L", (CAN, CAN), 0); d = ImageDraw.Draw(g)
    w = max(1.0, BODY_W * sx * (0.40 - lift / (1000 * K))); a = int(70 * (1 - 0.6 * clamp(lift / (40 * K))))
    if lift > 120 * K: a = 0                     # fuera de pantalla: sin sombra
    cx = CAN / 2 + dx
    d.ellipse((cx - w, GROUND - 8 * K, cx + w, GROUND + 12 * K), fill=a)
    under = g.filter(ImageFilter.GaussianBlur(12 * K))
    contour = body.getchannel("A").point(lambda v: v * 50 // 255)
    contour = ImageChops.offset(contour, 0, 5 * K).filter(ImageFilter.GaussianBlur(9 * K))
    return Image.merge("RGBA", (*Image.new("RGB", (CAN, CAN), (40, 25, 35)).split(), ImageChops.lighter(under, contour)))

def render(face_img, sx=1.0, sy=1.0, lift=0.0, rot=0.0, dx=0.0, extras=None, t=0.0, under=None):
    """Un frame de 512x512 con fondo transparente. lift/dx en px finales; rot en grados."""
    spr = sprite(face_img)
    base_s = BODY_W / BODY_BOX_W
    Sx, Sy = base_s * sx, base_s * sy
    px, py = CAN / 2 + dx * K, GROUND - lift * K
    ax, ay = SPR_W / 2, ANCHOR_Y
    th = math.radians(rot); cs, sn = math.cos(th), math.sin(th)
    a, b = cs / Sx, sn / Sx; c = ax - (cs * px + sn * py) / Sx
    d, e = -sn / Sy, cs / Sy; f = ay - (-sn * px + cs * py) / Sy
    body = spr.transform((CAN, CAN), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BICUBIC).convert("RGBA")
    canvas = shadow_layers(body, sx, lift * K, dx * K)
    if under: under(canvas, t)                   # efectos detrás del cuerpo (estela, líneas de velocidad)
    canvas.alpha_composite(body)
    if extras: extras(canvas, t)
    return canvas.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
