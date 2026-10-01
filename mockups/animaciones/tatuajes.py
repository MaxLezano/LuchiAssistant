"""Tatuajes de Luchi.

Dos tipos, combinables:
- PATRONES: cubren todo el cuerpo (olas, sakura, circuito...). Uno a la vez.
- FLASH: diseños chicos en una de 4 posiciones (panza, frente, costado). Hasta 3 a la vez.

Para que parezcan tatuajes de verdad:
- se dibujan como capa de tinta (líneas + rellenos de color) y se MULTIPLICAN sobre la piel,
  así conservan la textura y el sombreado del mochi;
- la tinta es irregular (ruido), un poco desenfocada y con un leve "corrido" alrededor;
- los colores se apagan un poco hacia el azul de la tinta;
- los patrones se desvanecen alrededor de la cara, para que la expresión siempre se lea.
"""
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

SS = 2                                       # supersampling de la capa de tinta
NAVY = (36, 44, 84)
BLACK = (28, 26, 34)
RED = (196, 56, 62)
YELLOW = (238, 196, 78)
TEAL = (36, 118, 124)
PINK = (238, 150, 176)
BROWN = (78, 50, 44)
ORANGE = (236, 132, 56)
CREAM = (250, 240, 214)
WHITE = (255, 255, 255)

def _font(name, size):
    try: return ImageFont.truetype("C:/Windows/Fonts/" + name, size)
    except OSError: return ImageFont.load_default()

class Canvas:
    """Capa RGBA en coordenadas 1024 con supersampling."""
    def __init__(self):
        self.im = Image.new("RGBA", (1024 * SS, 1024 * SS), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def P(self, pts): return [(x * SS, y * SS) for x, y in pts]
    def poly(self, pts, fill=None, outline=None, w=5):
        p = self.P(pts)
        if fill: self.d.polygon(p, fill=fill + (255,))
        if outline: self.line(pts + [pts[0]], outline, w)
    def line(self, pts, col, w=5):
        p = self.P(pts); r = w * SS / 2
        self.d.line(p, fill=col + (255,), width=int(w * SS), joint="curve")
        for x, y in (p[0], p[-1]): self.d.ellipse((x - r, y - r, x + r, y + r), fill=col + (255,))
    def circle(self, c, r, fill=None, outline=None, w=4):
        b = (c[0] * SS - r * SS, c[1] * SS - r * SS, c[0] * SS + r * SS, c[1] * SS + r * SS)
        if fill: self.d.ellipse(b, fill=fill + (255,))
        if outline: self.d.ellipse(b, outline=outline + (255,), width=int(w * SS))
    def arc(self, c, r, a0, a1, col, w=4):
        b = (c[0] * SS - r * SS, c[1] * SS - r * SS, c[0] * SS + r * SS, c[1] * SS + r * SS)
        self.d.arc(b, a0, a1, fill=col + (255,), width=int(w * SS))
    def text(self, xy, s, fnt_name, size, col):
        self.d.text((xy[0] * SS, xy[1] * SS), s, font=_font(fnt_name, int(size * SS)), fill=col + (255,), anchor="mm")
    def done(self): return self.im.resize((1024, 1024), Image.LANCZOS)

def _star(c, r, n=5, inner=0.45, rot=-90):
    return [(c[0] + (r if i % 2 == 0 else r * inner) * math.cos(math.radians(rot + 180 * i / n)),
             c[1] + (r if i % 2 == 0 else r * inner) * math.sin(math.radians(rot + 180 * i / n))) for i in range(n * 2)]

def _heart(c, r, n=60):
    return [(c[0] + r * 16 * math.sin(t) ** 3 / 16,
             c[1] - r * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
            for t in [math.tau * i / n for i in range(n)]]

def _blossom(cv, c, r, rot=0):
    for i in range(5):
        a = math.radians(rot - 90 + 72 * i)
        pc = (c[0] + r * 0.62 * math.cos(a), c[1] + r * 0.62 * math.sin(a))
        pts = [(pc[0] + r * 0.5 * math.cos(t) * math.cos(a) - r * 0.36 * math.sin(t) * math.sin(a),
                pc[1] + r * 0.5 * math.cos(t) * math.sin(a) + r * 0.36 * math.sin(t) * math.cos(a))
               for t in [math.tau * k / 24 for k in range(24)]]
        cv.poly(pts, fill=PINK, outline=(140, 60, 84), w=2.5)
    cv.circle(c, r * 0.18, fill=(200, 80, 110))

# ================================================================ patrones de cuerpo completo
def p_olas(cv):
    """Seigaiha: escamas de olas japonesas."""
    r = 44
    for row, y in enumerate(range(200, 880, 30)):
        off = 0 if row % 2 == 0 else r
        for x in range(120 - off, 940, 2 * r):
            cv.circle((x, y), r, fill=WHITE)
            for k, rr in enumerate((r - 3, r * 0.7, r * 0.42)):
                cv.arc((x, y), rr, 180, 360, (40, 74, 124), 3.5 if k == 0 else 2.6)

def p_sakura(cv):
    rnd = random.Random(7)
    main = [(120 + 820 * t, 860 - 560 * t - 90 * math.sin(math.pi * t * 1.4)) for t in [i / 40 for i in range(41)]]
    for i in range(len(main) - 1):
        w = 26 - 18 * i / len(main)
        cv.line([main[i], main[i + 1]], BROWN, w)
    for t0, ang, ln in ((0.25, -70, 160), (0.45, 40, 140), (0.62, -60, 150), (0.8, 30, 110)):
        p = main[int(t0 * 40)]
        sub = [(p[0] + ln * s * math.cos(math.radians(ang + 25 * s)), p[1] + ln * s * math.sin(math.radians(ang + 25 * s)))
               for s in [k / 10 for k in range(11)]]
        for i in range(10): cv.line([sub[i], sub[i + 1]], BROWN, 12 - i)
        for s in (0.5, 1.0): _blossom(cv, sub[int(s * 10)], 26, rnd.uniform(0, 72))
    for i in range(4, 40, 5): _blossom(cv, main[i], rnd.uniform(24, 34), rnd.uniform(0, 72))
    for _ in range(9):
        c = (rnd.uniform(200, 830), rnd.uniform(260, 780)); a = rnd.uniform(0, math.tau)
        pts = [(c[0] + 11 * math.cos(t) * math.cos(a) - 7 * math.sin(t) * math.sin(a),
                c[1] + 11 * math.cos(t) * math.sin(a) + 7 * math.sin(t) * math.cos(a)) for t in [math.tau * k / 16 for k in range(16)]]
        cv.poly(pts, fill=PINK, outline=(140, 60, 84), w=2)

def p_circuito(cv):
    rnd = random.Random(3)
    dirs = [(1, 0), (0, 1), (-1, 0), (0, -1), (0.707, 0.707), (-0.707, 0.707), (0.707, -0.707), (-0.707, -0.707)]
    for _ in range(46):
        x, y = rnd.uniform(170, 850), rnd.uniform(230, 800); d = rnd.randrange(4)
        pts = [(x, y)]
        for _ in range(rnd.randint(2, 4)):
            ln = rnd.uniform(30, 90); dx, dy = dirs[d]; x, y = x + dx * ln, y + dy * ln; pts.append((x, y))
            d = (d + rnd.choice((4, 5, 6, 7))) % 8 if d < 4 else rnd.randrange(4)
        cv.line(pts, TEAL, 4)
        cv.circle(pts[0], 6, fill=TEAL); cv.circle(pts[-1], 9, fill=WHITE, outline=TEAL, w=4)
    for (x, y, w, h) in ((230, 300, 90, 60), (720, 330, 70, 70), (260, 690, 80, 56), (700, 720, 96, 50)):
        cv.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill=(70, 150, 150), outline=TEAL, w=4)
        for i in range(1, 5):
            px = x + w * i / 5
            cv.line([(px, y), (px, y - 12)], TEAL, 3); cv.line([(px, y + h), (px, y + h + 12)], TEAL, 3)

def p_constelaciones(cv):
    rnd = random.Random(11)
    for _ in range(60):
        c = (rnd.uniform(170, 850), rnd.uniform(230, 800)); cv.circle(c, rnd.uniform(1.8, 3.4), fill=NAVY)
    groups = [[(240, 300), (300, 270), (360, 310), (330, 370), (390, 410)],
              [(640, 290), (700, 330), (760, 300), (790, 370)],
              [(250, 700), (320, 660), (400, 700), (460, 670), (520, 740)],
              [(640, 690), (700, 740), (780, 700)]]
    for g in groups:
        cv.line(g, NAVY, 2)
        for p in g: cv.poly(_star(p, 11, 4, 0.35), fill=NAVY)
    m = (790, 470)
    moon = [(m[0] + 46 * math.cos(t), m[1] + 46 * math.sin(t)) for t in [math.tau * k / 48 for k in range(48)]]
    cv.poly(moon, fill=YELLOW, outline=NAVY, w=4)
    cv.circle((m[0] - 20, m[1] - 14), 40, fill=WHITE)
    for p, r in (((190, 520), 16), ((560, 250), 13)): cv.poly(_star(p, r), fill=YELLOW, outline=NAVY, w=3)

def _flame(cx, base, h, w, curl):
    pts = []
    for i in range(31):
        t = i / 30
        pts.append((cx - w * (1 - t) ** 0.8 + curl * t ** 2 * 0.6 * w, base - h * t))
    for i in range(30, -1, -1):
        t = i / 30
        pts.append((cx + w * (1 - t) ** 0.8 + curl * t ** 2 * 0.6 * w + 0.15 * w * math.sin(t * 6), base - h * t))
    return pts

def p_llamas(cv):
    rnd = random.Random(5)
    for layer, (col, hs, ws) in enumerate(((RED, 1.0, 1.0), (ORANGE, 0.7, 0.66), (YELLOW, 0.42, 0.38))):
        for i, x in enumerate(range(150, 900, 62)):
            h = (230 + 150 * abs(math.sin(i * 1.7))) * hs; w = 46 * ws; curl = rnd.uniform(-0.8, 0.8)
            cv.poly(_flame(x, 830, h, w, curl), fill=col, outline=BLACK, w=4 - layer)

def p_tribal(cv):
    def spike(base_x, base_y, tip, width, bend):
        pts = []
        for i in range(25):
            t = i / 24; x = base_x + (tip[0] - base_x) * t + bend * math.sin(math.pi * t); y = base_y + (tip[1] - base_y) * t
            pts.append((x - width * (1 - t), y))
        for i in range(24, -1, -1):
            t = i / 24; x = base_x + (tip[0] - base_x) * t + bend * math.sin(math.pi * t); y = base_y + (tip[1] - base_y) * t
            pts.append((x + width * (1 - t) * 0.6, y))
        return pts
    for sg in (-1, 1):
        cx = 511 + sg * 330
        for k, (dy, ln, w) in enumerate(((800, 300, 34), (720, 230, 26), (640, 200, 22), (560, 160, 18), (470, 130, 14))):
            tip = (cx - sg * ln * 0.75, dy - ln * 0.65)
            cv.poly(spike(cx, dy, tip, w, sg * 40), fill=BLACK)
    for k in range(4):
        x = 330 + k * 120
        cv.poly(spike(x, 830, (x + 40, 680 - 30 * (k % 2)), 26, 30), fill=BLACK)

def p_tigre(cv):
    rnd = random.Random(9)
    for sg in (-1, 1):
        edge = 511 + sg * 360
        for y in range(270, 800, 58):
            ln = rnd.uniform(110, 200); w = rnd.uniform(12, 20); wob = rnd.uniform(-14, 14)
            tip = (edge - sg * ln, y + wob)
            pts = [(edge, y - w), (edge - sg * ln * 0.5, y - w * 0.6 + wob * 0.5), tip,
                   (edge - sg * ln * 0.5, y + w * 0.6 + wob * 0.5), (edge, y + w)]
            cv.poly(pts, fill=BLACK)
    for x in (430, 511, 592):
        cv.poly([(x - 12, 230), (x + 12, 230), (x + 2, 330 - abs(x - 511) * 0.4), (x - 2, 330 - abs(x - 511) * 0.4)], fill=BLACK)

PATTERNS = {"olas": ("olas (seigaiha)", p_olas), "sakura": ("rama de sakura", p_sakura),
            "circuito": ("circuito", p_circuito), "constelaciones": ("constelaciones", p_constelaciones),
            "llamas": ("llamas", p_llamas), "tribal": ("tribal", p_tribal), "tigre": ("rayas de tigre", p_tigre)}

# ================================================================ flash (diseños chicos, centrados en 0,0)
def f_codigo(cv, x, y, s): cv.text((x, y), "</>", "consolab.ttf", 46 * s, NAVY)
def f_llaves(cv, x, y, s): cv.text((x, y), "{ }", "consolab.ttf", 54 * s, NAVY)
def f_punto_y_coma(cv, x, y, s): cv.text((x, y), ";", "consolab.ttf", 74 * s, NAVY)
def f_404(cv, x, y, s):
    cv.text((x, y - 8 * s), "404", "consolab.ttf", 40 * s, NAVY); cv.text((x, y + 22 * s), "not found", "consola.ttf", 13 * s, NAVY)
def f_sudo(cv, x, y, s): cv.text((x, y), "$ sudo", "consolab.ttf", 30 * s, NAVY)
def f_hola_mundo(cv, x, y, s):
    cv.text((x - 4 * s, y - 12 * s), "Hola,", "segoeprb.ttf", 22 * s, NAVY); cv.text((x + 6 * s, y + 14 * s), "Mundo!", "segoeprb.ttf", 22 * s, NAVY)
def f_bug(cv, x, y, s):
    for dy in (-4, 8, 20):
        cv.line([(x - 18 * s, y + dy * s), (x - 32 * s, y + (dy - 6) * s)], NAVY, 4 * s)
        cv.line([(x + 18 * s, y + dy * s), (x + 32 * s, y + (dy - 6) * s)], NAVY, 4 * s)
    cv.line([(x - 5 * s, y - 27 * s), (x - 14 * s, y - 40 * s)], NAVY, 3 * s); cv.line([(x + 5 * s, y - 27 * s), (x + 14 * s, y - 40 * s)], NAVY, 3 * s)
    cv.circle((x, y - 19 * s), 11 * s, fill=NAVY)
    cv.d.ellipse(((x - 18 * s) * SS, (y - 14 * s) * SS, (x + 18 * s) * SS, (y + 26 * s) * SS), fill=RED + (255,), outline=NAVY + (255,), width=int(4 * s * SS))
    cv.line([(x, y - 12 * s), (x, y + 24 * s)], NAVY, 3 * s)
    for dx, dy in ((-8, 0), (9, 8), (-7, 15)): cv.circle((x + dx * s, y + dy * s), 3.5 * s, fill=NAVY)
def f_cafe(cv, x, y, s):
    cv.poly([(x - 24 * s, y - 10 * s), (x + 18 * s, y - 10 * s), (x + 14 * s, y + 26 * s), (x - 20 * s, y + 26 * s)], fill=(150, 98, 70), outline=NAVY, w=4 * s)
    cv.arc((x + 20 * s, y + 6 * s), 11 * s, -90, 90, NAVY, 5 * s)
    for dx in (-12, 0, 12):
        cv.line([(x + (dx - 3) * s, y - 18 * s), (x + (dx + 3) * s, y - 26 * s), (x + (dx - 3) * s, y - 34 * s), (x + (dx + 2) * s, y - 40 * s)], NAVY, 3 * s)
def f_git(cv, x, y, s):
    cv.line([(x - 16 * s, y - 16 * s), (x - 16 * s, y + 16 * s)], NAVY, 4 * s)
    cv.line([(x + 18 * s, y + 2 * s), (x + 18 * s, y + 6 * s), (x - 8 * s, y + 18 * s)], NAVY, 4 * s)
    for (px, py) in ((x - 16 * s, y - 24 * s), (x - 16 * s, y + 24 * s), (x + 18 * s, y - 6 * s)):
        cv.circle((px, py), 8 * s, fill=(240, 120, 80), outline=NAVY, w=4 * s)
def f_corazon(cv, x, y, s):
    cv.poly(_heart((x, y - 4 * s), 26 * s), fill=RED, outline=NAVY, w=4 * s)
    cv.text((x, y - 6 * s), "<3", "consolab.ttf", 16 * s, CREAM)
# --- clásicos (estilo "old school": contorno negro grueso y colores planos)
def f_ancla(cv, x, y, s):
    cv.circle((x, y - 34 * s), 9 * s, outline=BLACK, w=5 * s)
    cv.line([(x, y - 25 * s), (x, y + 32 * s)], BLACK, 7 * s)
    cv.line([(x - 20 * s, y - 12 * s), (x + 20 * s, y - 12 * s)], BLACK, 6 * s)
    cv.arc((x, y + 4 * s), 30 * s, 20, 160, BLACK, 7 * s)
    for sg in (-1, 1): cv.poly([(x + sg * 28 * s, y + 8 * s), (x + sg * 36 * s, y + 20 * s), (x + sg * 22 * s, y + 18 * s)], fill=BLACK)
    cv.arc((x - 6 * s, y - 2 * s), 26 * s, 300, 470, RED, 4 * s)
def f_mama(cv, x, y, s):
    cv.poly(_heart((x, y - 10 * s), 34 * s), fill=RED, outline=BLACK, w=5 * s)
    for sg in (-1, 1): cv.poly([(x + sg * 44 * s, y), (x + sg * 62 * s, y - 6 * s), (x + sg * 56 * s, y + 10 * s), (x + sg * 62 * s, y + 26 * s), (x + sg * 44 * s, y + 20 * s)], fill=(214, 196, 150), outline=BLACK, w=4 * s)
    cv.poly([(x - 46 * s, y - 4 * s), (x + 46 * s, y - 4 * s), (x + 46 * s, y + 22 * s), (x - 46 * s, y + 22 * s)], fill=CREAM, outline=BLACK, w=4 * s)
    cv.text((x, y + 9 * s), "Mamá", "segoeprb.ttf", 18 * s, BLACK)
def f_estrella(cv, x, y, s):
    pts = _star((x, y), 36 * s, 5, 0.42)
    for i in range(5):
        tip, l, r = pts[2 * i], pts[2 * i - 1], pts[(2 * i + 1) % 10]
        cv.poly([(x, y), l, tip], fill=BLACK); cv.poly([(x, y), tip, r], fill=RED)
    cv.poly(pts, outline=BLACK, w=4 * s)
def f_rayo(cv, x, y, s):
    cv.poly([(x + 8 * s, y - 40 * s), (x - 20 * s, y + 4 * s), (x - 2 * s, y + 4 * s), (x - 10 * s, y + 40 * s), (x + 22 * s, y - 8 * s), (x + 4 * s, y - 8 * s)],
            fill=YELLOW, outline=BLACK, w=5 * s)
def f_luna(cv, x, y, s):
    m = [(x + 34 * s * math.cos(t), y + 34 * s * math.sin(t)) for t in [math.tau * k / 40 for k in range(40)]]
    cv.poly(m, fill=YELLOW, outline=BLACK, w=5 * s)
    cv.circle((x + 15 * s, y - 10 * s), 30 * s, fill=WHITE)
    cv.arc((x + 15 * s, y - 10 * s), 30 * s, 110, 250, BLACK, 5 * s)
    cv.poly(_star((x + 34 * s, y + 18 * s), 9 * s), fill=YELLOW, outline=BLACK, w=2.5 * s)
def f_calavera(cv, x, y, s):
    head = [(x + 30 * s * math.cos(t), y - 6 * s + 28 * s * math.sin(t)) for t in [math.tau * k / 40 for k in range(40)]]
    cv.poly(head, fill=CREAM, outline=BLACK, w=5 * s)
    cv.poly([(x - 18 * s, y + 14 * s), (x + 18 * s, y + 14 * s), (x + 16 * s, y + 32 * s), (x - 16 * s, y + 32 * s)], fill=CREAM, outline=BLACK, w=5 * s)
    for sg in (-1, 1): cv.circle((x + sg * 12 * s, y - 6 * s), 9 * s, fill=BLACK)
    cv.poly([(x, y + 4 * s), (x - 5 * s, y + 12 * s), (x + 5 * s, y + 12 * s)], fill=BLACK)
    for dx in (-8, 0, 8): cv.line([(x + dx * s, y + 20 * s), (x + dx * s, y + 30 * s)], BLACK, 3 * s)
    cv.circle((x + 22 * s, y + 6 * s), 6 * s, fill=PINK)
def f_gatito(cv, x, y, s):
    head = [(x + 32 * s * math.cos(t), y + 5 * s + 26 * s * math.sin(t)) for t in [math.tau * k / 40 for k in range(40)]]
    for sg in (-1, 1): cv.poly([(x + sg * 30 * s, y - 2 * s), (x + sg * 26 * s, y - 34 * s), (x + sg * 6 * s, y - 18 * s)], fill=(120, 110, 120), outline=BLACK, w=4 * s)
    cv.poly(head, fill=(120, 110, 120), outline=BLACK, w=4 * s)
    for sg in (-1, 1):
        cv.circle((x + sg * 12 * s, y + 2 * s), 5 * s, fill=YELLOW, outline=BLACK, w=2 * s)
        cv.line([(x + sg * 16 * s, y + 14 * s), (x + sg * 44 * s, y + 10 * s)], BLACK, 2 * s)
        cv.line([(x + sg * 16 * s, y + 18 * s), (x + sg * 44 * s, y + 22 * s)], BLACK, 2 * s)
    cv.poly([(x - 4 * s, y + 11 * s), (x + 4 * s, y + 11 * s), (x, y + 16 * s)], fill=PINK)
def f_onigiri(cv, x, y, s):
    tri = [(x, y - 36 * s), (x + 38 * s, y + 28 * s), (x - 38 * s, y + 28 * s)]
    cv.poly(tri, fill=WHITE, outline=BLACK, w=6 * s)
    cv.poly([(x - 16 * s, y + 6 * s), (x + 16 * s, y + 6 * s), (x + 16 * s, y + 28 * s), (x - 16 * s, y + 28 * s)], fill=(40, 60, 50))
    for sg in (-1, 1): cv.circle((x + sg * 9 * s, y - 6 * s), 3 * s, fill=BLACK)
    cv.arc((x, y - 4 * s), 5 * s, 20, 160, BLACK, 2.5 * s)
def f_ola(cv, x, y, s):
    pts = [(x - 44 * s + 88 * s * t, y + 16 * s - 34 * s * math.sin(math.pi * t) ** 2) for t in [k / 30 for k in range(31)]]
    cv.poly(pts + [(x + 44 * s, y + 28 * s), (x - 44 * s, y + 28 * s)], fill=(70, 120, 170), outline=BLACK, w=4 * s)
    for k in range(3): cv.arc((x - 6 * s, y - 2 * s), (14 + 8 * k) * s, 180, 330, WHITE, 3 * s)
    cv.circle((x + 26 * s, y - 26 * s), 9 * s, fill=RED, outline=BLACK, w=3 * s)

FLASH = {
    # código
    "codigo": ("</>", f_codigo, "codigo"), "llaves": ("{ }", f_llaves, "codigo"),
    "punto_y_coma": ("punto y coma", f_punto_y_coma, "codigo"), "404": ("404", f_404, "codigo"),
    "sudo": ("sudo", f_sudo, "codigo"), "hola_mundo": ("Hola, Mundo!", f_hola_mundo, "codigo"),
    "bug": ("bug", f_bug, "codigo"), "cafe": ("café", f_cafe, "codigo"), "git": ("git", f_git, "codigo"),
    "corazon": ("<3", f_corazon, "codigo"),
    # clásicos y japoneses
    "ancla": ("ancla", f_ancla, "clasico"), "mama": ("Mamá", f_mama, "clasico"),
    "estrella": ("estrella náutica", f_estrella, "clasico"), "rayo": ("rayo", f_rayo, "clasico"),
    "luna": ("luna", f_luna, "clasico"), "calavera": ("calaverita", f_calavera, "clasico"),
    "gatito": ("gatito", f_gatito, "clasico"), "onigiri": ("onigiri", f_onigiri, "japones"),
    "fuji": ("monte Fuji", f_ola, "japones"),
}

SLOTS = {"panza_der": (680, 702, 1.5), "panza_izq": (342, 702, 1.5),
         "frente": (511, 318, 1.15), "costado_der": (782, 560, 1.15)}
MAX_FLASH = 3

# ================================================================ realismo
_NOISE = None
def _noise():
    global _NOISE
    if _NOISE is None:
        rnd = random.Random(1)
        n = Image.new("L", (256, 256)); n.putdata([int(200 + 55 * rnd.random()) for _ in range(256 * 256)])
        _NOISE = n.resize((1024, 1024), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.6))
    return _NOISE

_FACE_CLEAR = None
def _face_clear():
    """Máscara 255 en todo el cuerpo y 0 alrededor de la cara (los patrones no tapan la expresión)."""
    global _FACE_CLEAR
    if _FACE_CLEAR is None:
        m = Image.new("L", (1024, 1024), 255)
        ImageDraw.Draw(m).rounded_rectangle((262, 400, 762, 640), radius=110, fill=0)
        _FACE_CLEAR = m.filter(ImageFilter.GaussianBlur(26))
    return _FACE_CLEAR

def ink_layer(pattern=None, flash=()):
    """Capa RGBA de tinta (sin aplicar a la piel). flash: lista de (nombre, slot)."""
    cv = Canvas()
    if pattern and pattern != "ninguno":
        PATTERNS[pattern][1](cv)
    lay = cv.done()
    if pattern and pattern != "ninguno":
        lay.putalpha(ImageChops.multiply(lay.getchannel("A"), _face_clear()))
    if flash:
        fc = Canvas()
        for name, slot in list(flash)[:MAX_FLASH]:
            x, y, s = SLOTS[slot]
            FLASH[name][1](fc, x, y, s)
        lay.alpha_composite(fc.done())
    return lay

def apply_ink(skin, layer):
    """Multiplica la tinta sobre la piel con irregularidad, leve desenfoque y corrido."""
    a = layer.getchannel("A")
    if a.getbbox() is None: return skin
    rgb = layer.convert("RGB")
    # la tinta tira al azul, pero el blanco (zonas "sin tinta" que tapan otras líneas) queda blanco
    tinted = Image.blend(rgb, Image.new("RGB", rgb.size, NAVY), 0.12)
    white = rgb.convert("L").point(lambda v: 255 if v > 246 else 0)
    rgb = Image.composite(rgb, tinted, white)
    a_soft = a.filter(ImageFilter.GaussianBlur(0.9))
    a_ink = ImageChops.multiply(a_soft, _noise()).point(lambda v: int(v * 0.9))
    bleed = a.filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * 0.18))
    a_tot = ImageChops.lighter(a_ink, bleed)
    mult = Image.composite(rgb.filter(ImageFilter.GaussianBlur(0.6)), Image.new("RGB", rgb.size, WHITE), a_tot)
    return ImageChops.multiply(skin, mult)

_CACHE = {}
def tattoo_layer_cached(pattern, flash):
    key = (pattern, tuple(flash))
    if key not in _CACHE: _CACHE[key] = ink_layer(pattern, flash)
    return _CACHE[key]
