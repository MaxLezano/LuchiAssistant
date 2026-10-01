"""Líneas de tiempo de cada emoción. Solo manejan parámetros de expresión y del cuerpo:
funcionan igual con cualquier estilo (color, ojos, boca, tatuaje, accesorio)."""
import math
from PIL import Image, ImageDraw, ImageFilter
from luchi import (face, mix, render, clamp, smooth, ease_io, bump, font, heart_pts, star_pts,
                   K, CAN, GROUND, BODY_H, EXTRA, BLUSHES)

FPS = 30

def frames_of(T): return [i / FPS for i in range(int(round(T * FPS)))]

def voice(t, T):
    """Amplitud de voz simulada, periódica en T para que el loop no salte."""
    u = t / T
    a = 0.55 + 0.25 * math.sin(math.tau * 3 * u) + 0.18 * math.sin(math.tau * 7 * u + 1.3) \
        + 0.12 * math.sin(math.tau * 13 * u + 2.1)
    gate = 0.5 + 0.5 * math.sin(math.tau * 2 * u - 0.6)
    return clamp(a * smooth(0.15, 0.45, gate))

def blink_curve(t, at, close=0.07, hold=0.05, open_=0.11):
    """1 abierto -> 0 cerrado -> 1; abre más lento de lo que cierra."""
    if t < at or t > at + close + hold + open_: return 1.0
    if t < at + close: return 1 - ease_io((t - at) / close)
    if t < at + close + hold: return 0.0
    return ease_io((t - at - close - hold) / open_)

def heartbeat(u):
    return math.exp(-((u - 0.12) / 0.07) ** 2) + 0.6 * math.exp(-((u - 0.34) / 0.07) ** 2)

# ================================================================ adornos (lienzo 2x)
def _layer(c): return Image.new("RGBA", c.size, (0, 0, 0, 0))
BODY_CY = GROUND - BODY_H / 2

def ex_zzz(T):
    fnt = [font("segoeuisl.ttf", int(s * K)) for s in (22, 30, 38)]
    def f(c, t):
        lay = _layer(c); d = ImageDraw.Draw(lay)
        for i in range(3):
            p = ((t / T) * 2 + i / 3) % 1
            a = int(230 * math.sin(math.pi * p) ** 1.5)
            x = (370 + 40 * p + 8 * math.sin(p * math.tau)) * K; y = (175 - 95 * p) * K
            d.text((x, y), "z", font=fnt[min(2, int(p * 3))], fill=EXTRA + (a,))
        c.alpha_composite(lay)
    return f

def ex_hearts(T):
    def f(c, t):
        lay = _layer(c); d = ImageDraw.Draw(lay)
        for i, x0 in enumerate((165, 350, 258)):
            p = ((t / T) + i / 3) % 1
            a = int(220 * math.sin(math.pi * p))
            r = (9 + 6 * p) * K; x = (x0 + 12 * math.sin(p * math.tau)) * K; y = (175 - 115 * p) * K
            d.polygon(heart_pts((x, y), r), fill=(240, 140, 165, a))
        c.alpha_composite(lay)
    return f

def ex_dots(T):
    def f(c, t):
        lay = _layer(c); d = ImageDraw.Draw(lay)
        for i in range(3):
            ph = ((t / T) - i * 0.18) % 1
            a = smooth(0.0, 0.15, ph) * (1 - smooth(0.7, 0.9, ph))
            yb = math.sin(math.pi * clamp(ph / 0.3)) * 6
            x, y, r = (355 + i * 24) * K, (128 - yb) * K, 6 * K
            d.ellipse((x - r, y - r, x + r, y + r), fill=EXTRA + (int(255 * a),))
        c.alpha_composite(lay)
    return f

def ex_rings(T, amp_fn):
    def f(c, t):
        lay = _layer(c); d = ImageDraw.Draw(lay)
        amp = amp_fn(t); col = BLUSHES["rosa"]
        for i in range(3):
            p = ((t / T) * 2 + i / 3) % 1
            rw = (165 + 70 * p) * K; rh = rw * 0.84
            a = int(150 * (1 - p) ** 1.5 * (0.35 + 0.65 * amp))
            d.rounded_rectangle((CAN / 2 - rw, BODY_CY - rh, CAN / 2 + rw, BODY_CY + rh), radius=int(rw * 0.46),
                                outline=col + (a,), width=int(3 * K))
        c.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1.2)))
    return f

def ex_question(alpha_fn):
    fnt = font("segoeuisl.ttf", int(64 * K))
    def f(c, t):
        a = alpha_fn(t)
        if a < 0.01: return
        lay = _layer(c); d = ImageDraw.Draw(lay)
        yb = math.sin(t * math.tau / 1.2) * 4
        d.text((372 * K, (88 + yb - 12 * (1 - a)) * K), "?", font=fnt, fill=EXTRA + (int(255 * a),))
        c.alpha_composite(lay)
    return f

def ex_vein(scale_fn):
    """Marca de enojo estilo manga (💢): cuatro arcos que laten. Aparece por escala, sin fundidos."""
    def f(c, t):
        s = scale_fn(t)
        if s < 0.05: return
        lay = _layer(c); d = ImageDraw.Draw(lay)
        cx, cy = 392 * K, 118 * K; r = 18 * K * s; col = (226, 72, 86, 255)
        # cuatro curvas que se doblan hacia el centro sin tocarse (forma de 💢)
        for (qx, qy), start in (((-1, -1), 0), ((1, -1), 90), ((1, 1), 180), ((-1, 1), 270)):
            ox, oy = cx + qx * r * 1.25, cy + qy * r * 1.25
            d.arc((ox - r, oy - r, ox + r, oy + r), start + 10, start + 80, fill=col, width=max(2, int(7 * K * s)))
        c.alpha_composite(lay)
    return f

def ex_stars(T):
    """Estrellitas girando sobre la cabeza (mareado). Las de atrás, más chicas y tenues."""
    def f(c, t):
        lay = _layer(c); d = ImageDraw.Draw(lay)
        for i in range(3):
            a = math.tau * (t / T + i / 3)
            x = (256 + 78 * math.cos(a)) * K; y = (126 + 16 * math.sin(a)) * K
            depth = 0.5 + 0.5 * math.sin(a)
            r = (7 + 5 * depth) * K
            d.polygon(star_pts((x, y), r, 5, 0.45, math.degrees(a) * 0.5),
                      fill=(250, 214, 92, int(140 + 115 * depth)))
        c.alpha_composite(lay)
    return f

# ================================================================ emociones
def a_idle():
    T = 4.0; out = []
    for t in frames_of(T):
        u = t / T; b = math.sin(math.tau * u)
        o = blink_curve(t, 2.6)
        look = 9 * bump(t, 0.9, 1.9, 0.3) - 9 * bump(t, 3.1, 3.8, 0.25)
        out.append(render(face(open_l=o, open_r=o, look_x=look), 1 + 0.014 * b, 1 - 0.014 * b,
                          lift=3 + 3 * math.sin(math.tau * u + 0.8), t=t))
    return out

def a_atento():
    T = 2.2; out = []
    for t in frames_of(T):
        ta = t - 0.35
        squash = 0.05 * smooth(0.0, 0.16, ta) * (1 - smooth(0.16, 0.32, ta))
        stretch = 0.07 * smooth(0.18, 0.34, ta) * (1 - smooth(0.34, 0.7, ta))
        settle = -0.025 * smooth(0.5, 0.7, ta) * (1 - smooth(0.7, 1.0, ta))
        lift = 18 * smooth(0.2, 0.38, ta) * (1 - smooth(0.38, 0.7, ta))
        back = smooth(1.6, 2.05, t)
        k = smooth(0.15, 0.4, ta) * (1 - back)
        sy = 1 - squash + stretch + settle; sx = 1 + 0.8 * squash - 0.5 * stretch - 0.6 * settle
        o = blink_curve(t, 1.2)
        f = face(open_l=o, open_r=o, eye_scale=1 + 0.08 * k, mouth=mix({"w": 1}, {"dot": 1}, k))
        out.append(render(f, sx, sy, lift=lift + 3, t=t))
    return out

def a_escuchando():
    T = 3.0; out = []; amp = lambda t: voice(t, T)
    rings = ex_rings(T, amp)
    for t in frames_of(T):
        v = amp(t); o = blink_curve(t, 2.2)
        f = face(open_l=o, open_r=o, eye_scale=1.06, mouth={"dot": 1}, look_y=-2)
        out.append(render(f, 1 + 0.012 * v, 1 + 0.022 * v, lift=3 + 2 * v, extras=rings, t=t))
    return out

def a_pensando():
    T = 3.2; out = []; dots = ex_dots(1.6)
    for t in frames_of(T):
        u = t / T
        lx = 16 * math.sin(math.tau * u); ly = -10 - 3 * math.cos(math.tau * 2 * u)
        o = blink_curve(t, 1.55)
        f = face(open_l=o, open_r=o, look_x=lx, look_y=ly, mouth={"flat": 1})
        out.append(render(f, rot=2.5 * math.sin(math.tau * u), lift=3 + 2 * math.sin(math.tau * 2 * u),
                          extras=dots, t=t))
    return out

def a_hablando():
    T = 3.0; out = []
    for t in frames_of(T):
        v = voice(t + 0.4, T)
        o = blink_curve(t, 1.9)
        talk = smooth(0.08, 0.3, v)
        f = face(open_l=o, open_r=o, mouth=mix({"smile": 0.85}, {"talk": 1}, talk), talk_open=v)
        out.append(render(f, 1 - 0.006 * v, 1 + 0.012 * v, lift=3 + 2 * v, t=t))
    return out

def a_feliz():
    T = 2.4; out = []
    for t in frames_of(T):
        ta = t - 0.25
        antic = 0.06 * smooth(0.0, 0.14, ta) * (1 - smooth(0.14, 0.26, ta))
        hop_t = clamp((ta - 0.2) / 0.5)
        lift = 32 * math.sin(math.pi * hop_t) ** 1.2 if 0 < hop_t < 1 else 0
        stretch = 0.05 * smooth(0.16, 0.3, ta) * (1 - smooth(0.3, 0.55, ta))
        land = 0.06 * smooth(0.64, 0.74, ta) * (1 - smooth(0.74, 0.98, ta))
        rebound = 0.02 * smooth(0.9, 1.02, ta) * (1 - smooth(1.02, 1.25, ta))
        sy = 1 - antic + stretch - land + rebound; sx = 1 + 0.9 * antic - 0.5 * stretch + 0.8 * land - 0.5 * rebound
        k = smooth(0.1, 0.28, ta) * (1 - smooth(1.55, 1.85, t))
        f = face(open_l=1 - k, open_r=1 - k, closed_l="happy", closed_r="happy",
                 mouth=mix({"w": 1}, {"smile": 1}, k), blush=1 + 0.4 * k)
        out.append(render(f, sx, sy, lift=lift + 3, t=t))
    return out

def a_pregunta():
    T = 2.6; out = []
    for t in frames_of(T):
        k = smooth(0.15, 0.55, t) * (1 - smooth(2.0, 2.45, t))
        o = blink_curve(t, 1.3)
        f = face(open_l=o, open_r=o, look_x=8 * k, look_y=-9 * k, brow_up=k,
                 mouth=mix({"w": 1}, {"flat": 1}, k))
        q = ex_question(lambda tt, kk=k: kk)
        out.append(render(f, 1 + 0.01 * k, 1 - 0.01 * k, rot=-5 * k, lift=3, dx=-4 * k, extras=q, t=t))
    return out

def a_apenado():
    T = 2.6; out = []
    for t in frames_of(T):
        k = smooth(0.2, 0.6, t) * (1 - smooth(1.9, 2.4, t))
        sigh = bump(t, 0.9, 1.6, 0.35)
        o = 1 - 0.12 * k
        f = face(open_l=o, open_r=o, look_y=10 * k, brow_sad=k, blush=1 - 0.3 * k,
                 mouth=mix({"w": 1}, {"frown": 1}, k))
        sy = 1 - 0.035 * k - 0.02 * sigh; sx = 1 + 0.025 * k + 0.012 * sigh
        out.append(render(f, sx, sy, lift=3 - 2 * k, rot=1.5 * math.sin(math.tau * t / 1.3) * k, t=t))
    return out

def a_dormido():
    T = 4.0; out = []; z = ex_zzz(T)
    for t in frames_of(T):
        b = math.sin(math.tau * t / T)
        f = face(open_l=0, open_r=0, closed_l="sleep", closed_r="sleep",
                 mouth=mix({"dot": 0.6}, {"o": 0.9}, 0.5 + 0.5 * b), o_size=-0.4 + 0.3 * b)
        out.append(render(f, 1 + 0.03 * b, 1 - 0.035 * b, lift=2, extras=z, t=t))
    return out

def a_amor():
    T = 2.4; out = []; h = ex_hearts(T)
    for t in frames_of(T):
        beat = heartbeat((t / 1.2) % 1)
        f = face(heart=1, heart_scale=1 + 0.14 * beat, blush=1.5, mouth={"smile": 1})
        out.append(render(f, 1 + 0.02 * beat, 1 + 0.02 * beat, lift=3 + 2 * math.sin(math.tau * t / T), extras=h, t=t))
    return out

def a_guino():
    T = 2.0; out = []
    for t in frames_of(T):
        k = smooth(0.35, 0.55, t) * (1 - smooth(1.25, 1.5, t))
        f = face(open_r=1 - k, closed_r="happy", mouth=mix({"w": 1}, {"smile": 1}, k), blush=1 + 0.3 * k)
        pop = 0.025 * smooth(0.38, 0.5, t) * (1 - smooth(0.5, 0.75, t))
        out.append(render(f, 1 + pop, 1 - pop, rot=-5 * k, lift=3 + 4 * k, t=t))
    return out

def a_enojado():
    """Se infla, frunce el ceño y tiembla. Dos 'pisotones'. La marca 💢 late."""
    T = 2.6; out = []
    k_of = lambda t: smooth(0.2, 0.5, t) * (1 - smooth(2.05, 2.45, t))
    vein = ex_vein(lambda t: k_of(t) * (1 + 0.18 * math.sin(math.tau * t / 0.5)))
    for t in frames_of(T):
        k = k_of(t)
        stomp = 0.04 * (bump(t, 0.75, 0.95, 0.08) + bump(t, 1.25, 1.45, 0.08))
        shake = 1.6 * k * math.sin(math.tau * 7.5 * t)
        f = face(lid_l=0.36 * k, lid_r=0.36 * k, lid_tilt=24, brow_angry=k, look_y=-2 * k,
                 blush=1 + 0.7 * k, mouth=mix({"w": 1}, {"angry": 1}, k))
        sx = 1 + 0.035 * k + stomp; sy = 1 - 0.02 * k - stomp
        out.append(render(f, sx, sy, lift=3, dx=shake, extras=vein, t=t))
    return out

def a_mareado():
    """Ojos en espiral, boca ondulada, se tambalea en círculo y le giran estrellitas."""
    T = 2.4; out = []; stars = ex_stars(1.2)
    for t in frames_of(T):
        a = math.tau * t / 1.2
        f = face(spiral=1, spiral_rot=360 * t / 0.8, mouth={"wavy": 1}, wave_phase=t / 0.6, blush=0.8)
        out.append(render(f, 1 + 0.015 * math.sin(2 * a), 1 - 0.015 * math.sin(2 * a), rot=6 * math.sin(a),
                          dx=7 * math.cos(a), lift=3 + 3 * (0.5 + 0.5 * math.sin(2 * a)), extras=stars, t=t))
    return out

def a_cansado():
    """Párpados caídos, bostezo con estiramiento, lagrimita y se desinfla."""
    T = 4.4; out = []
    for t in frames_of(T):
        y_in = smooth(1.0, 1.6, t); y_out = smooth(2.3, 2.9, t)
        yawn = y_in * (1 - y_out)
        shut = smooth(1.2, 1.45, t) * (1 - smooth(2.25, 2.5, t))     # ojos apretados en el bostezo
        o = (1 - shut) * blink_curve(t, 3.7, 0.18, 0.12, 0.3) * 0.98
        tear = smooth(2.3, 2.8, t) * (1 - smooth(3.4, 3.8, t))
        f = face(open_l=o, open_r=o, closed_l="squeeze" if shut > 0.5 else "line",
                 closed_r="squeeze" if shut > 0.5 else "line",
                 lid_l=0.46, lid_r=0.46, lid_tilt=-8, look_y=5, blush=0.8,
                 mouth=mix({"flat": 1}, {"yawn": 1}, smooth(0.0, 0.25, yawn)), yawn=yawn, tear=tear)
        stretch = 0.06 * smooth(1.0, 1.6, t) * (1 - smooth(1.9, 2.5, t))
        slump = 0.035 * smooth(2.3, 2.9, t) * (1 - smooth(3.6, 4.3, t))
        breath = 0.01 * math.sin(math.tau * t / T)
        out.append(render(f, 1 - 0.5 * stretch + 0.7 * slump + breath, 1 + stretch - slump - breath,
                          lift=2 + 6 * stretch / 0.06, rot=-1.5 * slump / 0.035, t=t))
    return out

# ---------------------------------------------------------------- efectos estilo animé
DUST_FILL = (240, 235, 245)
DUST_LINE = (168, 156, 192)

def _cloud(d, x, y, r, a, rot=0.0, swirl=True):
    """Nube de polvo de caricatura: bolitas con contorno y un rulo adentro."""
    if a <= 0 or r < 1: return
    pts = [(-0.55, 0.15, 0.62), (0.0, -0.25, 0.75), (0.55, 0.1, 0.6), (0.15, 0.35, 0.55), (-0.2, 0.3, 0.5)]
    for ox, oy, rr in pts:
        cx, cy, R = x + ox * r, y + oy * r, rr * r
        d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=DUST_LINE + (a,))
    for ox, oy, rr in pts:
        cx, cy, R = x + ox * r, y + oy * r, rr * r - 2.5 * K
        if R > 0: d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=DUST_FILL + (a,))
    if swirl and r > 8 * K:
        sp = [(x + (0.05 + 0.4 * u) * r * math.cos(rot + u * 2.2 * math.tau),
               y + (0.05 + 0.4 * u) * r * math.sin(rot + u * 2.2 * math.tau)) for u in [k / 30 for k in range(31)]]
        d.line(sp, fill=DUST_LINE + (a,), width=max(1, int(2.2 * K)))

def body_x(dx): return CAN / 2 + dx * K

def ex_run_trail(xpos, t_start, t_stop, direction=1):
    """Estela de polvo en remolino + líneas de velocidad detrás del cuerpo mientras corre.
    xpos(t) -> dx del cuerpo (px finales). direction: 1 = corre hacia la derecha."""
    spawn = [t_start + 0.04 * k for k in range(int((t_stop - t_start) / 0.04) + 1)]
    def f(c, t):
        lay = _layer(c); d = ImageDraw.Draw(lay)
        # nubes que quedan atrás, crecen y se desvanecen
        for ts in spawn:
            age = (t - ts) / 0.6
            if not 0 <= age <= 1: continue
            x0 = body_x(xpos(ts)) - direction * 120 * K
            r = (30 + 30 * age) * K
            x = x0 - direction * 40 * age * K; y = GROUND - (26 + 46 * age) * K
            _cloud(d, x, y, r, int(245 * (1 - age) ** 1.2), rot=ts * 9 + age * 4)
        # remolino marcado pegado a la espalda mientras corre
        if t_start <= t <= t_stop + 0.1:
            k = smooth(t_start, t_start + 0.08, t) * (1 - smooth(t_stop, t_stop + 0.1, t))
            bx = body_x(xpos(t)) - direction * 175 * K; by = GROUND - 85 * K
            for j in range(3):
                rot = -direction * t * 24 + j * math.tau / 3
                sp = [(bx + (10 + 72 * u) * K * math.cos(rot + u * 1.5 * math.tau) * 1.2,
                       by + (10 + 72 * u) * K * math.sin(rot + u * 1.5 * math.tau) * 0.8) for u in [q / 50 for q in range(51)]]
                d.line(sp, fill=DUST_LINE + (int(240 * k),), width=int(5 * K))
            # ráfagas de viento: líneas onduladas que viajan hacia atrás y se afinan en la punta
            for i in range(6):
                y0 = GROUND - (52 + 38 * i) * K
                ln = (100 + 110 * abs(math.sin(i * 2.3 + t * 30))) * K
                xa = body_x(xpos(t)) - direction * (165 + 12 * (i % 2)) * K
                amp = (7 + 3 * (i % 3)) * K; wl = (70 + 14 * (i % 2)) * K
                ph = t * 22 + i * 1.7
                n = 24
                for j in range(n):
                    u0, u1 = j / n, (j + 1) / n
                    p0 = (xa - direction * ln * u0, y0 + amp * math.sin(ph + ln * u0 / wl * math.tau) * (0.4 + 0.6 * u0))
                    p1 = (xa - direction * ln * u1, y0 + amp * math.sin(ph + ln * u1 / wl * math.tau) * (0.4 + 0.6 * u1))
                    w = max(1, int((4.5 - 3 * u0) * K))
                    d.line([p0, p1], fill=(160, 150, 192, int(235 * k * (1 - 0.6 * u0))), width=w)
        c.alpha_composite(lay)
    return f

def ex_skid(t0, xpos, direction=1):
    """Frenada: nube de polvo delante y abajo."""
    def f(c, t):
        age = (t - t0) / 0.55
        if not 0 <= age <= 1: return
        lay = _layer(c); d = ImageDraw.Draw(lay)
        x = body_x(xpos(t0)) + direction * (120 + 50 * age) * K
        for j, (ox, sc) in enumerate(((0, 1.0), (40, 0.7), (-30, 0.6))):
            _cloud(d, x + direction * ox * K, GROUND - (18 + 24 * age + 10 * j) * K, (22 + 28 * age) * sc * K,
                   int(230 * (1 - age) ** 1.2), rot=age * 5 + j)
        c.alpha_composite(lay)
    return f

def ex_sweat(k_fn):
    """Gota de sudor de animé al costado de la cabeza (aparece por escala)."""
    def f(c, t):
        k = k_fn(t)
        if k < 0.05: return
        lay = _layer(c); d = ImageDraw.Draw(lay)
        x, y = 392 * K, (150 + 4 * math.sin(t * 9)) * K; r = 11 * K * k
        d.polygon([(x, y - 2.2 * r), (x + 0.85 * r, y - 0.2 * r), (x - 0.85 * r, y - 0.2 * r)], fill=(150, 200, 240, 255))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(150, 200, 240, 255))
        d.ellipse((x - 0.35 * r, y - 0.5 * r, x + 0.05 * r, y - 0.1 * r), fill=(235, 245, 255, 255))
        c.alpha_composite(lay)
    return f

def ex_poof(t0, x_fn):
    """Bocanada de humo ninja donde estaba (desaparición misteriosa)."""
    def f(c, t):
        age = (t - t0) / 0.7
        if not 0 <= age <= 1: return
        lay = _layer(c); d = ImageDraw.Draw(lay)
        x0 = body_x(x_fn(t0)); y0 = GROUND - 110 * K
        a = int(240 * (1 - age) ** 1.4)
        for j in range(7):
            ang = j / 7 * math.tau + 0.4
            rr = (40 + 90 * ease_io(min(1, age * 1.6))) * K
            _cloud(d, x0 + math.cos(ang) * rr * 0.9, y0 + math.sin(ang) * rr * 0.6, (34 + 26 * age) * K, a, rot=ang + age * 3)
        _cloud(d, x0, y0, (60 + 40 * age) * K, a, rot=age * 4)
        c.alpha_composite(lay)
    return f

def _chain(*fs):
    def f(c, t):
        for g in fs: g(c, t)
    return f

def body_top(lift, sy):
    """Borde superior del cuerpo en el lienzo 2x."""
    return GROUND - BODY_H * sy - lift * K

def ex_vertical_wind(k_fn, top_fn, up=True):
    """Ráfagas onduladas verticales: detrás del cuerpo según hacia dónde se mueve.
    up=True: el cuerpo sube, las líneas quedan abajo. up=False: cae, quedan arriba."""
    def f(c, t):
        k = k_fn(t)
        if k < 0.02: return
        lay = _layer(c); d = ImageDraw.Draw(lay)
        top, bottom = top_fn(t)
        for i in range(6):
            x0 = CAN / 2 + (-125 + 50 * i) * K
            ln = (90 + 90 * abs(math.sin(i * 1.9 + t * 30))) * K
            ya = (top - 14 * K) if not up else (bottom + 14 * K)
            sgn = -1 if not up else 1
            amp = (6 + 2 * (i % 3)) * K; wl = 70 * K; ph = t * 22 + i * 1.3
            n = 22
            for j in range(n):
                u0, u1 = j / n, (j + 1) / n
                p0 = (x0 + amp * math.sin(ph + ln * u0 / wl * math.tau) * (0.4 + 0.6 * u0), ya + sgn * ln * u0)
                p1 = (x0 + amp * math.sin(ph + ln * u1 / wl * math.tau) * (0.4 + 0.6 * u1), ya + sgn * ln * u1)
                d.line([p0, p1], fill=(160, 150, 192, int(235 * k * (1 - 0.6 * u0))), width=max(1, int((4.5 - 3 * u0) * K)))
        c.alpha_composite(lay)
    return f

def ex_impact(t0):
    """Aterrizaje de superhéroe: onda expansiva en el piso, líneas de impacto y polvo a los costados."""
    def f(c, t):
        age = (t - t0) / 0.7
        if not 0 <= age <= 1: return
        lay = _layer(c); d = ImageDraw.Draw(lay)
        a = int(230 * (1 - age) ** 1.3)
        # onda expansiva
        rx = (60 + 230 * ease_io(min(1, age * 1.4))) * K; ry = rx * 0.16
        d.ellipse((CAN / 2 - rx, GROUND - ry, CAN / 2 + rx, GROUND + ry), outline=DUST_LINE + (a,), width=max(1, int(5 * K * (1 - age))))
        # líneas de impacto radiales (solo al principio)
        if age < 0.45:
            ka = 1 - age / 0.45
            for j in range(10):
                ang = math.pi + j / 9 * math.pi                 # semicírculo de arriba
                r0, r1 = (170 + 30 * age) * K, (215 + 70 * age) * K
                cx, cy = CAN / 2, GROUND - 40 * K
                d.line([(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang) * 0.7),
                        (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang) * 0.7)],
                       fill=(176, 166, 204, int(230 * ka)), width=int(4 * K))
        # polvo hacia los costados
        for sg in (-1, 1):
            for j, (dx, sc) in enumerate(((120, 1.0), (175, 0.8), (225, 0.6))):
                x = CAN / 2 + sg * (dx + 60 * age) * K
                _cloud(d, x, GROUND - (14 + 22 * age + 6 * j) * K, (20 + 22 * age) * sc * K, a, rot=age * 4 + j + sg)
        c.alpha_composite(lay)
    return f

def a_aparecer():
    """Cae desde el borde superior como superhéroe: estirado y con viento, impacta, se queda agachado
    con cara decidida y se levanta; al final vuelve a su cara de siempre."""
    T = 2.8; out = []
    t0, t_land, t_rise, t_up = 0.12, 0.42, 0.85, 1.25
    def lift_of(t):
        if t < t0: return 400
        if t < t_land: u = (t - t0) / (t_land - t0); return 400 * (1 - u * u)
        return 0
    def shape(t):
        if t < t_land:
            k = smooth(t0, t0 + 0.08, t); return 1 - 0.1 * k, 1 + 0.14 * k            # estirado al caer
        if t < t_land + 0.06:
            u = (t - t_land) / 0.06; return 1 + 0.26 * u, 1 - 0.3 * u                 # impacto
        if t < t_rise:
            u = (t - t_land - 0.06) / (t_rise - t_land - 0.06)
            return 1.26 - 0.08 * u, 0.7 + 0.1 * u                                    # agachado (pose de héroe)
        if t < t_up:
            u = ease_io((t - t_rise) / (t_up - t_rise)); return 1.18 - 0.22 * u, 0.8 + 0.26 * u   # se levanta y pasa de largo
        e = math.exp(-6 * (t - t_up)) * math.cos(math.tau * 1.8 * (t - t_up))
        return 1 + 0.04 * e, 1 + 0.06 * e
    shake = lambda t: (3.5 * math.exp(-14 * (t - t_land)) * math.sin(t * 90)) if t >= t_land else 0
    wind = ex_vertical_wind(lambda t: smooth(t0, t0 + 0.05, t) * (1 - smooth(t_land - 0.02, t_land + 0.05, t)),
                            lambda t: (body_top(lift_of(t), shape(t)[1]), GROUND - lift_of(t) * K), up=False)
    impact = ex_impact(t_land)
    for t in frames_of(T):
        sx, sy = shape(t)
        hero = 1 - smooth(t_up - 0.05, t_up + 0.25, t)                                 # cara decidida
        o = blink_curve(t, 1.9)
        f = face(open_l=o, open_r=o, lid_l=0.34 * hero, lid_r=0.34 * hero, lid_tilt=16 * hero,
                 brow_angry=0.55 * hero if t >= t_land else 0, look_y=-3 * hero,
                 mouth=mix({"flat": 1}, {"w": 1}, 1 - hero), blush=1)
        out.append(render(f, sx, sy, lift=lift_of(t) + 3, dx=shake(t), under=wind, extras=impact, t=t))
    return out

def a_esconderse():
    """Mira a todos lados con sospecha (gota de sudor), se agacha y salta hacia arriba hasta desaparecer,
    dejando una bocanada de humo."""
    T = 3.0; out = []
    t_crouch, t_jump = 1.6, 1.9
    def lift_of(t):
        if t < t_jump: return 0
        u = (t - t_jump) / 0.32; return 420 * min(1, u) ** 2
    look_k = lambda t: smooth(0.2, 0.4, t) * (1 - smooth(t_crouch, t_crouch + 0.1, t))
    sweat = ex_sweat(lambda t: smooth(0.5, 0.65, t) * (1 - smooth(t_crouch, t_crouch + 0.1, t)))
    poof = ex_poof(t_jump + 0.02, lambda tt: 0)
    def shape(t):
        crouch = smooth(0.25, 0.45, t) * 0.04
        if t < t_crouch: return 1 + crouch, 1 - crouch * 1.2
        if t < t_jump:
            u = smooth(t_crouch, t_jump, t); return 1.04 + 0.12 * u, 0.95 - 0.13 * u    # anticipación
        u = smooth(t_jump, t_jump + 0.08, t); return 1.16 - 0.3 * u, 0.82 + 0.38 * u    # estirado hacia arriba
    wind = ex_vertical_wind(lambda t: smooth(t_jump, t_jump + 0.05, t) * (1 - smooth(t_jump + 0.4, t_jump + 0.6, t)),
                            lambda t: (body_top(lift_of(t), shape(t)[1]), GROUND - lift_of(t) * K), up=True)
    for t in frames_of(T):
        k = look_k(t)
        look = (-18 * bump(t, 0.45, 0.85, 0.08) + 18 * bump(t, 0.95, 1.3, 0.08) - 18 * bump(t, 1.35, 1.55, 0.05))
        sx, sy = shape(t)
        f = face(look_x=look, lid_l=0.3 * k, lid_r=0.3 * k, lid_tilt=0,
                 mouth=mix({"w": 1}, {"flat": 1}, k), blush=1)
        turn = look * 0.3 if t < t_crouch else 0
        out.append(render(f, sx, sy, lift=lift_of(t) + 3, rot=turn, dx=look * 0.5 if t < t_crouch else 0,
                          extras=sweat, under=_chain(poof, wind), t=t))
    return out

ANIMS = {
    "idle": a_idle, "atento": a_atento, "escuchando": a_escuchando, "pensando": a_pensando,
    "hablando": a_hablando, "feliz": a_feliz, "pregunta": a_pregunta, "apenado": a_apenado,
    "dormido": a_dormido, "amor": a_amor, "guino": a_guino,
    "enojado": a_enojado, "mareado": a_mareado, "cansado": a_cansado,
    "aparecer": a_aparecer, "esconderse": a_esconderse,
}

# metadatos de cada emoción: (nombre, tipo, disparador). Fuente única para docs y catálogo.
EMOTIONS = {
    "aparecer":   ("Aparece", "una vez", "Se detecta \"Luchi\" con la isla oculta: cae desde arriba como superhéroe y encadena a atento"),
    "atento":     ("Atento", "una vez", "Detección del wake word; encadena a escuchando"),
    "escuchando": ("Escuchando", "loop", "Mientras escucha la orden; las ondas siguen el nivel del micrófono"),
    "pensando":   ("Pensando", "loop", "Procesando, solo si tarda más de 400 ms"),
    "hablando":   ("Hablando", "loop", "Mientras suena el TTS; la boca sigue la amplitud del audio"),
    "feliz":      ("Feliz", "una vez", "Acción hecha (90 % de las veces)"),
    "guino":      ("Guiño", "una vez", "Acción hecha (10 % de las veces)"),
    "pregunta":   ("Pregunta", "loop", "Orden ambigua o confirmación; espera la respuesta"),
    "apenado":    ("Apenado", "una vez", "Error, dispositivo no disponible o no entendió"),
    "cansado":    ("Cansado", "una vez", "Primera orden después de medianoche, al terminar (nunca retrasa la escucha)"),
    "mareado":    ("Mareado", "una vez", "Le dan muchas órdenes al mismo tiempo (3 o más en pocos segundos o encimadas)"),
    "enojado":    ("Enojado", "una vez", "Le dicen algo feo o \"Luchi, enojate\" (easter egg; nunca por errores)"),
    "dormido":    ("Dormido", "loop", "Micrófono silenciado"),
    "amor":       ("Amor", "una vez", "\"Gracias, Luchi\" o \"te quiero\""),
    "idle":       ("Reposo", "loop", "Modo compañía (Luchi visible sin órdenes)"),
    "esconderse": ("Se esconde", "una vez", "Fin de la interacción: mira a todos lados con sospecha y salta hacia arriba hasta desaparecer"),
}

# poses clave para hojas estáticas: (nombre, parámetros de cara, kwargs de render)
KEY_POSES = [
    ("neutral", {}, {}),
    ("atento", dict(eye_scale=1.08, mouth={"dot": 1}), {}),
    ("escuchando", dict(eye_scale=1.06, mouth={"dot": 1}), {}),
    ("pensando", dict(look_x=14, look_y=-10, mouth={"flat": 1}), {}),
    ("hablando", dict(mouth={"talk": 1}, talk_open=0.7), {}),
    ("feliz", dict(open_l=0, open_r=0, closed_l="happy", closed_r="happy", mouth={"smile": 1}, blush=1.4), {}),
    ("pregunta", dict(look_x=8, look_y=-9, brow_up=1, mouth={"flat": 1}), dict(rot=-5)),
    ("apenado", dict(look_y=10, brow_sad=1, mouth={"frown": 1}, open_l=0.88, open_r=0.88), {}),
    ("dormido", dict(open_l=0, open_r=0, closed_l="sleep", closed_r="sleep", mouth={"dot": 0.6}), {}),
    ("amor", dict(heart=1, blush=1.5, mouth={"smile": 1}), {}),
    ("guino", dict(open_r=0, closed_r="happy", mouth={"smile": 1}, blush=1.3), {}),
    ("enojado", dict(lid_l=0.36, lid_r=0.36, lid_tilt=24, brow_angry=1, blush=1.7, mouth={"angry": 1}), {}),
    ("mareado", dict(spiral=1, spiral_rot=40, mouth={"wavy": 1}, wave_phase=0.1), dict(rot=5)),
    ("cansado", dict(lid_l=0.46, lid_r=0.46, lid_tilt=-8, look_y=5, mouth={"flat": 1}, blush=0.8), {}),
]
