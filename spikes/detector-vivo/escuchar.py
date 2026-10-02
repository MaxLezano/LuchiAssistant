"""F0-12: prueba el detector propio de "Luchi" en vivo con el micrófono (Windows, sin PyTorch).

Usa el mismo frontend en numpy que va a usar luchi-voice (spikes/wakeword/frontend.py) y onnxruntime.
Cada 80 ms evalúa la última ventana de 1,6 s; tras una detección ignora 2 s (como la app).

Uso:
  uv run python escuchar.py                          # en vivo, hasta Ctrl+C
  uv run python escuchar.py --minutos 60 --nota tele # prueba de falsos positivos con la TV de fondo
  uv run python escuchar.py --modelo E:/Luchi/models/detector/v2/detector.onnx --umbral 0.7

Deja un CSV con cada detección y un reporte .md en E:/Luchi/pruebas-detector/ (fuera de git).
"""
import argparse
import csv
import datetime as dt
import queue
import sys
import time
from math import gcd
from pathlib import Path

import numpy as np
import onnxruntime as ort
import sounddevice as sd
from scipy.signal import resample_poly

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wakeword"))
import frontend  # noqa: E402

CUADROS = 160
VENTANA = frontend.WIN + (CUADROS - 1) * frontend.HOP   # 25.840 muestras a 16 kHz
PASO = 8 * frontend.HOP                                  # 80 ms
CLASES = ["nada", "luchi", "oye_luchi"]
SALIDA = Path(r"E:\Luchi\pruebas-detector")


def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()


def barra(v, ancho=20):
    n = int(min(1.0, v) * ancho)
    return "█" * n + "·" * (ancho - n)


def detectar(modelo, audio16: np.ndarray, umbral: float):
    """Mismo recorrido que en vivo (ventana de 1,6 s cada 80 ms, 2 s de bloqueo) sobre audio ya a 16 kHz."""
    audio16 = np.concatenate([np.zeros(VENTANA, dtype=np.float32), audio16, np.zeros(PASO * 6, dtype=np.float32)])
    maximos, dets, bloqueado = np.zeros(3), [], -1.0
    for ini in range(0, len(audio16) - VENTANA + 1, PASO):
        p = softmax(modelo.run(None, {"logmel": frontend.logmel_np(audio16[ini:ini + VENTANA])[None]})[0][0])
        maximos = np.maximum(maximos, p)
        k = int(np.argmax(p[1:])) + 1
        t = ini / frontend.SR
        if p[k] >= umbral and t > bloqueado:
            dets.append((CLASES[k], float(p[k])))
            bloqueado = t + 2.0
    return maximos, dets


def probar_archivos(args):
    import soundfile as sf

    modelo = ort.InferenceSession(str(args.modelo), providers=["CPUExecutionProvider"])
    for f in args.archivo:
        a, sr = sf.read(f, dtype="float32")
        if a.ndim > 1:
            a = a.mean(axis=1)
        g = gcd(frontend.SR, sr)
        a16 = resample_poly(a, frontend.SR // g, sr // g).astype(np.float32)
        maximos, dets = detectar(modelo, a16, args.umbral)
        print(f"{f.name}: máx Luchi {maximos[1]:.2f} · Oye Luchi {maximos[2]:.2f} · detecciones {dets}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", type=Path, default=Path(r"E:\Luchi\models\detector\v3\detector.onnx"))
    ap.add_argument("--umbral", type=float, default=0.8)
    ap.add_argument("--minutos", type=float, default=0, help="0 = hasta Ctrl+C")
    ap.add_argument("--nota", default="en-vivo", help="etiqueta de la prueba (ej. tele, distancia-3m)")
    ap.add_argument("--dispositivo", default=None, help="micrófono (nombre o índice); por defecto el de Windows")
    ap.add_argument("--archivo", nargs="+", type=Path, help="pasar WAV por el mismo camino que el micrófono (sin tiempo real)")
    args = ap.parse_args()
    if args.archivo:
        return probar_archivos(args)

    sesion = ort.SessionOptions()
    sesion.intra_op_num_threads = 1          # el detector tiene que ser liviano: un solo hilo
    modelo = ort.InferenceSession(str(args.modelo), sesion, providers=["CPUExecutionProvider"])
    info = sd.query_devices(args.dispositivo, kind="input")
    sr = int(info["default_samplerate"])
    g = gcd(frontend.SR, sr)
    arriba, abajo = frontend.SR // g, sr // g

    SALIDA.mkdir(parents=True, exist_ok=True)
    marca = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    archivo_csv = SALIDA / f"{marca}_{args.nota}.csv"
    cola: queue.Queue = queue.Queue()

    def callback(datos, frames, tiempo, status):
        cola.put(datos[:, 0].copy())

    buffer = np.zeros(VENTANA, dtype=np.float32)
    pendiente = np.zeros(0, dtype=np.float32)
    bloqueado_hasta = 0.0
    detecciones = []
    inferencias, t_inferencia = 0, 0.0
    inicio = time.time()
    fin = inicio + args.minutos * 60 if args.minutos else float("inf")

    print(f"Micrófono: {info['name']} ({sr} Hz) · modelo {args.modelo.name} · umbral {args.umbral}")
    print("Decí \"Luchi\" u \"Oye Luchi\". Ctrl+C para terminar.\n")
    with archivo_csv.open("w", newline="", encoding="utf-8") as f, \
            sd.InputStream(device=args.dispositivo, samplerate=sr, channels=1, dtype="float32",
                           blocksize=int(sr * 0.04), callback=callback):
        w = csv.writer(f)
        w.writerow(["hora", "segundo", "clase", "probabilidad"])
        try:
            while time.time() < fin:
                bloque = cola.get()
                pendiente = np.concatenate([pendiente, resample_poly(bloque, arriba, abajo).astype(np.float32)])
                while len(pendiente) >= PASO:
                    buffer = np.concatenate([buffer[PASO:], pendiente[:PASO]])
                    pendiente = pendiente[PASO:]
                    t0 = time.perf_counter()
                    feats = frontend.logmel_np(buffer)[None].astype(np.float32)
                    p = softmax(modelo.run(None, {"logmel": feats})[0][0])
                    t_inferencia += time.perf_counter() - t0
                    inferencias += 1
                    ahora = time.time() - inicio
                    k = int(np.argmax(p[1:])) + 1
                    nivel = float(np.sqrt(np.mean(buffer[-PASO:] ** 2)) * 10)
                    print(f"\r nivel {barra(nivel, 12)}  Luchi {barra(p[1])} {p[1]:.2f}  Oye Luchi {barra(p[2])} {p[2]:.2f} ",
                          end="", flush=True)
                    if p[k] >= args.umbral and ahora > bloqueado_hasta:
                        bloqueado_hasta = ahora + 2.0
                        hora = dt.datetime.now().strftime("%H:%M:%S")
                        detecciones.append((hora, ahora, CLASES[k], float(p[k])))
                        w.writerow([hora, f"{ahora:.1f}", CLASES[k], f"{p[k]:.3f}"])
                        f.flush()
                        print(f"\n  ✓ {hora}  {CLASES[k]}  ({p[k]:.2f})")
        except KeyboardInterrupt:
            pass

    duracion = (time.time() - inicio) / 60
    ms = t_inferencia / max(1, inferencias) * 1000
    por_hora = len(detecciones) / max(duracion / 60, 1e-9)
    reporte = SALIDA / f"{marca}_{args.nota}.md"
    reporte.write_text(
        f"# Prueba del detector · {args.nota}\n\n"
        f"- Fecha: {marca} · duración: {duracion:.1f} min\n"
        f"- Modelo: `{args.modelo}` · umbral {args.umbral}\n"
        f"- Micrófono: {info['name']} ({sr} Hz)\n"
        f"- Detecciones: **{len(detecciones)}** ({por_hora:.2f} por hora)\n"
        f"- Costo: {ms:.1f} ms por evaluación cada 80 ms ({ms / 80 * 100:.1f} % de un núcleo)\n\n"
        "| Hora | Segundo | Clase | Probabilidad |\n|---|---|---|---|\n"
        + "".join(f"| {h} | {s:.1f} | {c} | {p:.2f} |\n" for h, s, c, p in detecciones),
        encoding="utf-8")
    print(f"\n\n{len(detecciones)} detecciones en {duracion:.1f} min ({por_hora:.2f}/h) · {ms:.1f} ms por evaluación")
    print(f"Reporte: {reporte}")


if __name__ == "__main__":
    main()
