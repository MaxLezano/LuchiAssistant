"""Accesorios de Luchi: capas RGBA en el espacio común de 1024 px.

Pueden salir del contorno del cuerpo. Se dibujan una vez por estilo y después se transforman
junto con el cuerpo (escala, altura, rotación), así acompañan todas las animaciones.

Categorías:
- diario: para usar siempre.
- divertido: los graciosos.
- temporada: se pueden activar solos en ciertas fechas (ver SEASONS).
"""
import math
from PIL import Image, ImageDraw, ImageChops, ImageFilter

S = 2
DARK = (62, 60, 74)
PINK = (240, 168, 180)
RED = (214, 58, 70)
WHITE = (250, 248, 245)
YELLOW = (246, 200, 84)
GOLD_DARK = (214, 160, 50)

class Layer:
    def __init__(self):
        self.im = Image.new("RGBA", (1024 * S, 1024 * S), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def P(self, pts): return [(x * S, y * S) for x, y in pts]
    def B(self, b): return tuple(v * S for v in b)
    def poly(self, pts, col): self.d.polygon(self.P(pts), fill=col + (255,))
    def ellipse(self, box, col): self.d.ellipse(self.B(box), fill=col + (255,))
    def circle(self, c, r, col): self.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), col)
    def rect(self, box, col, radius=0):
        if radius: self.d.rounded_rectangle(self.B(box), radius=radius * S, fill=col + (255,))
        else: self.d.rectangle(self.B(box), fill=col + (255,))
    def line(self, pts, col, w):
        p = self.P(pts); r = w * S / 2
        self.d.line(p, fill=col + (255,), width=int(w * S), joint="curve")
        for x, y in (p[0], p[-1]): self.d.ellipse((x - r, y - r, x + r, y + r), fill=col + (255,))
    def arc(self, box, a0, a1, col, w): self.d.arc(self.B(box), a0, a1, fill=col + (255,), width=int(w * S))
    def pieslice(self, box, a0, a1, col): self.d.pieslice(self.B(box), a0, a1, fill=col + (255,))
    def rot_ellipse(self, c, w, h, ang, col):
        e = Image.new("RGBA", (int(w * S) + 4, int(h * S) + 4), (0, 0, 0, 0))
        ImageDraw.Draw(e).ellipse((2, 2, w * S + 2, h * S + 2), fill=col + (255,))
        e = e.rotate(-ang, resample=Image.BICUBIC, expand=True)
        self.im.alpha_composite(e, (int(c[0] * S - e.width / 2), int(c[1] * S - e.height / 2)))
    def done(self): return self.im.resize((1024, 1024), Image.LANCZOS)

def _heart(c, r, n=48):
    return [(c[0] + r * math.sin(t) ** 3, c[1] - r * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
            for t in [math.tau * i / n for i in range(n)]]

def _taper(path, w0, w1):
    """Polígono de un trazo que se afina de w0 a w1 a lo largo de path."""
    top, bot = [], []
    for i, (x, y) in enumerate(path):
        x0, y0 = path[max(i - 1, 0)]; x1, y1 = path[min(i + 1, len(path) - 1)]
        dx, dy = x1 - x0, y1 - y0; n = math.hypot(dx, dy) or 1
        w = (w0 + (w1 - w0) * i / (len(path) - 1)) / 2
        top.append((x - dy / n * w, y + dx / n * w)); bot.append((x + dy / n * w, y - dx / n * w))
    return top + bot[::-1]

EL, ER, EY = (353, 478), (668, 478), 478

# ================================================================ diario
def a_lentes(L):
    frame = (48, 42, 54)
    for c in (EL, ER):
        L.d.ellipse(L.B((c[0] - 64, EY - 60, c[0] + 64, EY + 60)), fill=(255, 255, 255, 34))
        L.d.ellipse(L.B((c[0] - 64, EY - 60, c[0] + 64, EY + 60)), outline=frame + (255,), width=8 * S)
        L.d.line(L.P([(c[0] + 18, EY - 40), (c[0] + 38, EY - 20)]), fill=(255, 255, 255, 150), width=6 * S)
    L.arc((EL[0] + 60, EY - 34, ER[0] - 60, EY + 26), 205, 335, frame, 7)
    L.line([(EL[0] - 64, EY - 8), (190, EY - 20)], frame, 7)
    L.line([(ER[0] + 64, EY - 8), (834, EY - 20)], frame, 7)

def a_auriculares(L):
    L.arc((170, 150, 854, 850), 180, 360, DARK, 28)
    L.arc((178, 158, 846, 842), 200, 340, (108, 104, 124), 7)
    for x0 in (142, 822):
        L.rect((x0, 420, x0 + 62, 562), (70, 68, 82), 26)
        cx0 = x0 + 50 if x0 < 500 else x0 - 4
        L.rect((cx0, 432, cx0 + 16, 550), PINK, 8)
        L.circle((x0 + 27, 485), 9, PINK)

def a_mono(L):
    c = (770, 268); col = (236, 96, 128); dark = (196, 62, 96)
    for sg in (-1, 1):
        L.poly([c, (c[0] + 62 * sg, c[1] - 40), (c[0] + 70 * sg, c[1] + 26)], col)
        L.poly([c, (c[0] + 38 * sg, c[1] + 20), (c[0] + 30 * sg, c[1] + 54)], dark)
    L.circle(c, 17, dark)

def a_sakura(L):
    c = (262, 262)
    for i in range(5):
        a = math.radians(-90 + 72 * i)
        L.rot_ellipse((c[0] + 30 * math.cos(a), c[1] + 30 * math.sin(a)), 48, 70, math.degrees(a) + 90, (250, 188, 206))
    L.circle(c, 12, (236, 120, 150))
    for i in range(5):
        a = math.radians(-54 + 72 * i)
        L.circle((c[0] + 16 * math.cos(a), c[1] + 16 * math.sin(a)), 4, (250, 214, 110))

def a_brote(L):
    g1, g2 = (124, 190, 112), (96, 162, 92)
    L.line([(511, 240), (508, 212), (514, 178)], g2, 8)
    for sg, col in ((-1, g1), (1, g2)):
        pts = [(514 + sg * 66 * t, 178 - 36 * math.sin(math.pi * t) - 14 * t) for t in [i / 20 for i in range(21)]]
        pts += [(514 + sg * 66 * t, 178 + 10 * math.sin(math.pi * t) - 14 * t) for t in [i / 20 for i in range(20, -1, -1)]]
        L.poly(pts, col)

def a_orejas_gato(L):
    for sg in (-1, 1):
        bx = 511 + sg * 165
        L.poly([(bx - sg * 70, 258), (bx + sg * 45, 236), (bx - sg * 40, 120)], (72, 68, 82))
        L.poly([(bx - sg * 48, 244), (bx + sg * 22, 232), (bx - sg * 32, 150)], PINK)

def a_hachimaki(L, body):
    band = Layer()
    band.rect((150, 286, 874, 334), WHITE)
    band.line([(150, 298), (874, 298)], (228, 224, 218), 3)
    band.line([(150, 322), (874, 322)], (228, 224, 218), 3)
    band.circle((511, 310), 21, RED)
    b = band.done()
    grow = body.filter(ImageFilter.MaxFilter(7))                 # la vincha abraza el cuerpo
    b.putalpha(ImageChops.multiply(b.getchannel("A"), grow))
    L.im.alpha_composite(b.resize(L.im.size, Image.LANCZOS))
    L.poly([(838, 296), (920, 318), (930, 352), (870, 330), (836, 318)], WHITE)
    L.poly([(836, 312), (900, 360), (892, 398), (858, 352), (832, 326)], (238, 234, 228))
    L.circle((842, 312), 16, (236, 232, 226))

# ================================================================ divertido
def a_corona(L):
    gold = YELLOW
    L.poly([(442, 250), (580, 250), (592, 176), (552, 210), (511, 160), (470, 210), (430, 176)], gold)
    L.rect((442, 236, 580, 252), GOLD_DARK)
    for c in ((430, 176), (511, 160), (592, 176)): L.circle(c, 9, (240, 120, 140))

def a_orejas_conejo(L):
    L.rot_ellipse((425, 132), 74, 230, -8, WHITE)
    L.rot_ellipse((427, 140), 36, 170, -8, PINK)
    L.rot_ellipse((600, 182), 74, 120, 6, WHITE)                  # oreja doblada
    L.rot_ellipse((662, 112), 70, 130, 62, WHITE)
    L.rot_ellipse((660, 116), 32, 90, 62, PINK)

def a_antenas(L):
    for (x0, x1, col) in ((452, 404, (236, 90, 116)), (570, 618, (120, 200, 240))):
        L.line([(x0, 242), ((x0 + x1) / 2 + (x1 - x0) * 0.2, 170), (x1, 112)], DARK, 7)
        L.circle((x1, 106), 24, col)
        L.circle((x1 - 8, 98), 7, WHITE)

def a_bigote(L):
    col = (58, 40, 42)
    for sg in (-1, 1):
        path = [(511 + sg * (6 + 78 * u), 548 - 6 * math.sin(math.pi * u) - 14 * u ** 3) for u in [i / 24 for i in range(25)]]
        L.poly(_taper(path, 26, 9), col)
        cx, cy = 511 + sg * 88, 522
        L.arc((cx - 14, cy - 14, cx + 14, cy + 14), 0 if sg > 0 else 180, 270 if sg > 0 else 90, col, 8)
    L.circle((511, 546), 12, col)

def a_lentes_pixel(L):
    """Lentes "deal with it": cada cristal centrado sobre su ojo."""
    px = 16; y0 = 426
    lens = ["11111111111",
            "11221111111",
            "11112211111",
            "11111111111",
            "01111111110",
            "00111111100"]
    L.rect((EL[0] - 100, y0, ER[0] + 100, y0 + px), (20, 20, 24))
    for cx in (EL[0], ER[0]):
        x0 = cx - len(lens[0]) * px / 2
        for r, row in enumerate(lens):
            for c, ch in enumerate(row):
                if ch == "0": continue
                col = (20, 20, 24) if ch == "1" else (250, 250, 250)
                L.rect((x0 + c * px, y0 + px + r * px, x0 + (c + 1) * px, y0 + px + (r + 1) * px), col)

def a_gorro_helice(L):
    cols = [RED, YELLOW, (90, 140, 220)]
    for i in range(6):
        L.pieslice((330, 150, 692, 330), 180 + 30 * i, 210 + 30 * i, cols[i % 3])
    L.rect((330, 236, 692, 252), (70, 70, 90), 6)
    L.line([(511, 150), (511, 122)], DARK, 8)
    L.rot_ellipse((452, 116), 120, 26, -6, (90, 140, 220))
    L.rot_ellipse((570, 116), 120, 26, -6, RED)
    L.circle((511, 118), 12, YELLOW)

def a_pajarito(L):
    body, dark = (250, 214, 90), (226, 184, 62)
    L.poly([(590, 214), (560, 200), (566, 226)], dark)                # cola
    L.ellipse((592, 182, 676, 244), body)
    L.circle((680, 186), 26, body)
    L.poly([(702, 182), (726, 190), (702, 198)], (240, 140, 60))
    L.circle((684, 180), 5, (20, 20, 24))
    L.rot_ellipse((628, 212), 46, 26, -20, dark)
    L.line([(620, 242), (616, 252)], (240, 140, 60), 4); L.line([(642, 242), (646, 252)], (240, 140, 60), 4)
    L.circle((672, 198), 6, (246, 160, 160))

def a_flecha(L):
    """Flecha de broma que "atraviesa" el cuerpo: plumas a la izquierda, punta a la derecha."""
    shaft = (150, 102, 62); y = 420
    L.line([(60, y + 6), (196, y)], shaft, 14)
    for dy in (-22, 0, 22):
        L.poly([(60, y + 6), (104, y + 6 + dy * 0.15), (80, y + 6 + dy)], RED)
    L.line([(826, y - 2), (950, y - 8)], shaft, 14)
    L.poly([(940, y - 34), (994, y - 9), (940, y + 16)], (170, 170, 180))

def a_chef(L):
    L.rect((382, 196, 640, 252), WHITE, 10)
    L.line([(382, 238), (640, 238)], (225, 225, 232), 3)
    for (x, y, r) in ((430, 150, 58), (590, 150, 58), (511, 120, 70), (470, 178, 52), (552, 178, 52)):
        L.circle((x, y + 4), r, (228, 228, 236))
    for (x, y, r) in ((430, 150, 58), (590, 150, 58), (511, 120, 70), (470, 178, 52), (552, 178, 52)):
        L.circle((x, y), r, WHITE)

# ================================================================ temporada
def a_gorro_fiesta(L):
    b1, b2, apex = (238, 266), (398, 232), (292, 66)
    lerp = lambda a, b, t: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    L.poly([b1, b2, apex], (110, 190, 240))
    for t0, t1 in ((0.15, 0.3), (0.5, 0.65)):
        L.poly([lerp(b1, apex, t0), lerp(b2, apex, t0), lerp(b2, apex, t1), lerp(b1, apex, t1)], (240, 120, 160))
    for t, c in ((0.42, YELLOW), (0.78, YELLOW)):
        m = lerp(lerp(b1, apex, t), lerp(b2, apex, t), 0.5); L.circle(m, 7, c)
    L.circle(apex, 20, YELLOW)

def a_gorro_navidad(L):
    red, dark = (208, 48, 58), (176, 34, 46)
    L.poly([(360, 232), (430, 130), (540, 84), (650, 94), (742, 140), (806, 204), (716, 168), (646, 150), (672, 232)], red)
    L.poly([(646, 150), (716, 168), (806, 204), (742, 160)], dark)
    for i in range(9): L.circle((354 + i * 40, 238 + (i % 2) * 4), 26, WHITE)
    L.circle((810, 210), 28, WHITE)

def a_cuernos(L):
    red, dark = (210, 50, 60), (170, 30, 44)
    for sg in (-1, 1):
        cx = 511 + sg * 175
        pts = [(cx - sg * 46, 262), (cx - sg * 60, 210), (cx - sg * 50, 150), (cx - sg * 20, 104),
               (cx + sg * 4, 150), (cx + sg * 20, 205), (cx + sg * 44, 248)]
        L.poly(pts, red)
        L.poly([(cx - sg * 20, 104), (cx + sg * 4, 150), (cx - sg * 14, 160)], dark)

def a_sombrero_bruja(L):
    purple, band, dark = (64, 42, 86), (150, 92, 190), (46, 30, 64)
    L.poly([(382, 236), (430, 150), (470, 92), (520, 52), (600, 32), (652, 46), (588, 72), (562, 112), (600, 172), (640, 236)], purple)
    L.poly([(398, 204), (622, 204), (634, 230), (388, 230)], band)
    L.rect((494, 202, 528, 232), YELLOW, 4); L.rect((502, 210, 520, 224), band, 2)
    L.ellipse((276, 214, 746, 266), dark)
    L.ellipse((290, 212, 732, 254), purple)

def a_diadema_corazones(L):
    col = (230, 90, 130)
    L.arc((262, 196, 760, 470), 196, 344, col, 12)
    for (x0, x1) in ((440, 410), (582, 612)):
        zz = [(x0 + (x1 - x0) * i / 8 + (9 if i % 2 else -9), 236 - 14 * i) for i in range(9)]
        L.line(zz, (90, 86, 100), 4)
        L.poly(_heart((x1, 96), 30), (236, 64, 96))
        L.circle((x1 - 12, 88), 6, (255, 200, 210))

def a_sombrero_paja(L):
    straw, straw_d = (232, 196, 110), (206, 166, 84)
    L.rect((382, 132, 640, 236), straw_d, 50)
    L.rect((382, 196, 640, 226), (206, 58, 58))
    L.ellipse((238, 208, 784, 270), straw_d)
    L.ellipse((250, 204, 772, 258), straw)
    for k in range(1, 6):
        L.arc((250 + k * 30, 204 + k * 5, 772 - k * 30, 258 - k * 5), 10, 170, straw_d, 2)

def a_birrete(L):
    black, top = (36, 36, 44), (58, 58, 70)
    L.poly([(404, 214), (618, 214), (604, 258), (418, 258)], black)
    L.poly([(511, 150), (698, 192), (511, 232), (324, 192)], top)
    L.circle((511, 191), 9, YELLOW)
    L.line([(511, 191), (660, 202), (668, 270)], YELLOW, 5)
    L.rect((658, 266, 680, 306), YELLOW, 6)

# id: (nombre, categoría, temporada, función, necesita la silueta del cuerpo)
INFO = {
    "lentes": ("lentes", "diario", None, a_lentes, False),
    "auriculares": ("auriculares", "diario", None, a_auriculares, False),
    "mono": ("moño", "diario", None, a_mono, False),
    "sakura": ("flor de sakura", "diario", None, a_sakura, False),
    "brote": ("brote", "diario", None, a_brote, False),
    "orejas_gato": ("orejas de gato", "diario", None, a_orejas_gato, False),
    "hachimaki": ("hachimaki", "diario", None, a_hachimaki, True),
    "corona": ("corona", "divertido", None, a_corona, False),
    "orejas_conejo": ("orejas de conejo", "divertido", None, a_orejas_conejo, False),
    "antenas": ("antenas", "divertido", None, a_antenas, False),
    "bigote": ("bigote", "divertido", None, a_bigote, False),
    "lentes_pixel": ("lentes pixel", "divertido", None, a_lentes_pixel, False),
    "gorro_helice": ("gorro con hélice", "divertido", None, a_gorro_helice, False),
    "pajarito": ("pajarito", "divertido", None, a_pajarito, False),
    "flecha": ("flecha atravesada", "divertido", None, a_flecha, False),
    "chef": ("gorro de chef", "divertido", None, a_chef, False),
    "gorro_fiesta": ("gorro de fiesta", "temporada", "cumpleanos", a_gorro_fiesta, False),
    "gorro_navidad": ("gorro navideño", "temporada", "navidad", a_gorro_navidad, False),
    "cuernos": ("cuernitos", "temporada", "halloween", a_cuernos, False),
    "sombrero_bruja": ("sombrero de bruja", "temporada", "halloween", a_sombrero_bruja, False),
    "diadema_corazones": ("vincha de corazones", "temporada", "san_valentin", a_diadema_corazones, False),
    "sombrero_paja": ("sombrero de paja", "temporada", "verano", a_sombrero_paja, False),
    "birrete": ("birrete", "temporada", "graduacion", a_birrete, False),
}

# fechas sugeridas (MM-DD). "cumpleanos" y "graduacion" las define el usuario.
# "verano" depende del hemisferio: se elige en ajustes (por defecto sur).
SEASONS = {
    "navidad": {"desde": "12-01", "hasta": "12-31"},
    "halloween": {"desde": "10-24", "hasta": "10-31"},
    "san_valentin": {"desde": "02-07", "hasta": "02-14"},
    "verano": {"sur": {"desde": "12-21", "hasta": "03-20"}, "norte": {"desde": "06-21", "hasta": "09-22"}},
    "cumpleanos": "fecha del usuario",
    "graduacion": "manual",
}
# tapan los ojos: la emoción se lee por la boca, el cuerpo y los adornos
COVERS_EYES = {"lentes_pixel"}

def render(name, body_mask):
    L = Layer()
    _, _, _, fn, needs_body = INFO[name]
    fn(L, body_mask) if needs_body else fn(L)
    return L.done()
