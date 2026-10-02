"""Grabar la voz propia de Luchi (F9-02) y muestras reales de "Luchi" (F0-13).

Uso:  cd spikes/grabar-voz && uv run python grabar.py [--persona luz] [--seccion detector|voz]
Teclas: Espacio = grabar una toma / cortar · 1 2 3 = elegir y escuchar una toma · D = borrar la elegida
        E = escuchar la elegida · Enter = guardar y seguir · S = saltear

Hasta 3 tomas por frase: se guardan todas (NNNN_t1.wav…) y la elegida también como NNNN.wav
(48 kHz, mono, 16 bits). metadata.csv: "id|texto|indicación|toma elegida|cantidad de tomas".
Carpeta: E:/Luchi/voice-data/<persona>/<sección>. Nada de esto va a git ni sale de la PC (PLAN.md §8).
Retoma donde quedó: las frases ya guardadas no se vuelven a pedir.
"""
import argparse
import csv
import queue
import re
import tkinter as tk
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

SR = 48000
MAX_TOMAS = 3
RAIZ = Path(r"E:\Luchi\voice-data")
FRASES = Path(__file__).with_name("frases.txt")

FONDO, TEXTO, SECUNDARIO, ACENTO, PELIGRO, OK = "#13141b", "#ece8f0", "#9a93a8", "#f0a5b4", "#e5566b", "#7fd1a8"


def leer_frases():
    secciones, actual = {}, None
    for linea in FRASES.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or (linea.startswith("#") and not linea.startswith("##")):
            continue
        if linea.startswith("##"):
            actual = linea[2:].strip()
            secciones[actual] = []
        else:
            m = re.match(r"^(.*?)\s*(\[(.*)\])?$", linea)
            secciones[actual].append((m.group(1).strip(), (m.group(3) or "").strip()))
    return secciones


class Grabador:
    def __init__(self, raiz: tk.Tk, carpeta: Path, frases):
        self.raiz, self.carpeta, self.frases = raiz, carpeta, frases
        self.carpeta.mkdir(parents=True, exist_ok=True)
        self.meta = self.carpeta / "metadata.csv"
        hechas = set()
        if self.meta.exists():
            with self.meta.open(encoding="utf-8") as f:
                hechas = {int(r[0]) for r in csv.reader(f, delimiter="|") if r}
        self.pendientes = [i for i in range(len(frases)) if i not in hechas]
        self.total = len(frases)
        self.cola: queue.Queue = queue.Queue()
        self.tomas: list = []
        self.elegida = -1
        self.grabando = False
        self.nivel = 0.0
        self._ui()
        self._mostrar()

    # --- interfaz -------------------------------------------------------------
    def _ui(self):
        r = self.raiz
        r.title("Grabar la voz de Luchi")
        r.configure(bg=FONDO)
        r.geometry("1150x680")
        self.progreso = tk.Label(r, bg=FONDO, fg=SECUNDARIO, font=("Segoe UI", 14))
        self.progreso.pack(pady=(24, 0))
        self.texto = tk.Label(r, bg=FONDO, fg=TEXTO, font=("Segoe UI Semibold", 40), wraplength=1050, justify="center")
        self.texto.pack(expand=True)
        self.indicacion = tk.Label(r, bg=FONDO, fg=ACENTO, font=("Segoe UI", 22))
        self.indicacion.pack()
        self.medidor = tk.Canvas(r, width=600, height=18, bg="#232633", highlightthickness=0)
        self.medidor.pack(pady=18)
        self.barra = self.medidor.create_rectangle(0, 0, 0, 18, fill=OK, width=0)
        self.estado = tk.Label(r, bg=FONDO, fg=SECUNDARIO, font=("Segoe UI", 18))
        self.estado.pack()
        fila = tk.Frame(r, bg=FONDO)
        fila.pack(pady=(14, 0))
        self.casillas = []
        for k in range(MAX_TOMAS):
            c = tk.Label(fila, bg="#1b1d26", fg=SECUNDARIO, font=("Segoe UI", 15), padx=18, pady=8, cursor="hand2")
            c.pack(side="left", padx=6)
            c.bind("<Button-1>", lambda e, k=k: self.elegir(k))
            self.casillas.append(c)
        botones = tk.Frame(r, bg=FONDO)
        botones.pack(pady=20)
        for texto, accion in [("● Grabar toma  [Espacio]", self.alternar), ("▶ Escuchar  [E]", self.escuchar),
                              ("🗑 Borrar toma  [D]", self.borrar), ("✓ Guardar y seguir  [Enter]", self.guardar),
                              ("Saltear  [S]", self.saltear)]:
            tk.Button(botones, text=texto, command=accion, font=("Segoe UI", 13), bg="#232633", fg=TEXTO,
                      activebackground="#2c3040", relief="flat", padx=14, pady=8).pack(side="left", padx=6)
        r.bind("<space>", lambda e: self.alternar())
        r.bind("<Return>", lambda e: self.guardar())
        r.bind("<e>", lambda e: self.escuchar())
        r.bind("<s>", lambda e: self.saltear())
        r.bind("<d>", lambda e: self.borrar())
        for k in range(MAX_TOMAS):
            r.bind(str(k + 1), lambda e, k=k: self.elegir(k))
        tk.Label(r, text=f"Micrófono: {sd.query_devices(kind='input')['name']} · se guarda en {self.carpeta}",
                 bg=FONDO, fg=SECUNDARIO, font=("Segoe UI", 10)).pack(side="bottom", pady=8)
        self._animar()

    def _mostrar(self):
        self.tomas, self.elegida = [], -1
        self._casillas()
        if not self.pendientes:
            self.texto.config(text="¡Terminaste! Muchas gracias 💗")
            self.indicacion.config(text="")
            self.estado.config(text="Podés cerrar la ventana.", fg=OK)
            self.progreso.config(text=f"{self.total} de {self.total}")
            return
        frase, ind = self.frases[self.pendientes[0]]
        self.texto.config(text=frase)
        self.indicacion.config(text=ind)
        self.progreso.config(text=f"{self.total - len(self.pendientes) + 1} de {self.total}")
        self.estado.config(text="Apretá Espacio y leé la frase", fg=SECUNDARIO)

    def _casillas(self):
        for k, c in enumerate(self.casillas):
            if k < len(self.tomas):
                elegida = k == self.elegida
                c.config(text=f"Toma {k + 1}: {len(self.tomas[k]) / SR:.1f} s{'  ✓' if elegida else ''}",
                         bg="#2c3040" if elegida else "#1b1d26", fg=OK if elegida else TEXTO)
            else:
                c.config(text=f"Toma {k + 1}: —", bg="#1b1d26", fg=SECUNDARIO)

    def _animar(self):
        ancho = int(min(1.0, self.nivel * 1.2) * 600)
        color = PELIGRO if self.nivel > 0.95 else (ACENTO if self.grabando else OK)
        self.medidor.coords(self.barra, 0, 0, ancho, 18)
        self.medidor.itemconfig(self.barra, fill=color)
        self.nivel *= 0.85
        self.raiz.after(33, self._animar)

    # --- audio ----------------------------------------------------------------
    def _callback(self, datos, frames, tiempo, status):
        self.cola.put(datos.copy())
        self.nivel = max(self.nivel, float(np.abs(datos).max()))

    def alternar(self):
        if not self.pendientes:
            return
        if not self.grabando:
            if len(self.tomas) >= MAX_TOMAS:
                self.estado.config(text="Ya hay 3 tomas: elegí una (1 2 3) y guardá, o borrá una con D", fg=PELIGRO)
                return
            sd.stop()
            self.cola = queue.Queue()
            self.stream = sd.InputStream(samplerate=SR, channels=1, dtype="float32", callback=self._callback)
            self.stream.start()
            self.grabando = True
            self.estado.config(text=f"● Grabando toma {len(self.tomas) + 1}… (Espacio para cortar)", fg=PELIGRO)
        else:
            self.stream.stop()
            self.stream.close()
            self.grabando = False
            partes = []
            while not self.cola.empty():
                partes.append(self.cola.get())
            self._revisar(np.concatenate(partes)[:, 0] if partes else None)

    def _revisar(self, audio):
        if audio is None or len(audio) < SR * 0.3:
            self.estado.config(text="Muy corto, probá de nuevo", fg=PELIGRO)
            return
        self.tomas.append(audio)
        self.elegida = len(self.tomas) - 1
        self._casillas()
        pico = float(np.abs(audio).max())
        if pico > 0.98:
            self.estado.config(text="Saturó: alejá un poquito el micrófono (podés borrarla con D)", fg=PELIGRO)
        elif pico < 0.05:
            self.estado.config(text="Quedó muy bajito: hablá un poco más fuerte (podés borrarla con D)", fg=PELIGRO)
        else:
            self.estado.config(text=f"Toma {len(self.tomas)} bien. Espacio = otra toma · 1 2 3 = elegir · Enter = guardar", fg=OK)

    def elegir(self, k):
        if k < len(self.tomas) and not self.grabando:
            self.elegida = k
            self._casillas()
            self.escuchar()

    def escuchar(self):
        if 0 <= self.elegida < len(self.tomas) and not self.grabando:
            sd.stop()
            sd.play(self.tomas[self.elegida], SR)

    def borrar(self):
        if 0 <= self.elegida < len(self.tomas) and not self.grabando:
            sd.stop()
            self.tomas.pop(self.elegida)
            self.elegida = len(self.tomas) - 1
            self._casillas()
            self.estado.config(text="Toma borrada", fg=SECUNDARIO)

    def guardar(self):
        if self.grabando or not self.tomas or not self.pendientes:
            return
        sd.stop()
        i = self.pendientes.pop(0)
        for k, audio in enumerate(self.tomas):
            sf.write(self.carpeta / f"{i:04d}_t{k + 1}.wav", audio, SR, subtype="PCM_16")
        sf.write(self.carpeta / f"{i:04d}.wav", self.tomas[self.elegida], SR, subtype="PCM_16")
        with self.meta.open("a", encoding="utf-8", newline="") as f:
            csv.writer(f, delimiter="|").writerow([f"{i:04d}", self.frases[i][0], self.frases[i][1],
                                                   f"t{self.elegida + 1}", len(self.tomas)])
        self._mostrar()

    def saltear(self):
        if self.pendientes and not self.grabando:
            self.pendientes.append(self.pendientes.pop(0))
            self._mostrar()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--persona", default="luz")
    ap.add_argument("--seccion", default="detector", choices=["detector", "voz"])
    args = ap.parse_args()
    raiz = tk.Tk()
    Grabador(raiz, RAIZ / args.persona / args.seccion, leer_frases()[args.seccion])
    raiz.mainloop()


if __name__ == "__main__":
    main()
