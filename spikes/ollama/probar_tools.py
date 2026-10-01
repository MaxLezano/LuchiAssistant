"""Spike F0-02: tool calling con Ollama + qwen3:8b y think=false.

Uso: python spikes/ollama/probar_tools.py [modelo]
Solo librería estándar. Mide latencia en frío y en caliente y la VRAM usada.
"""
import json
import subprocess
import sys
import time
import urllib.request

URL = "http://127.0.0.1:11434"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3:8b"

TOOLS = [
    {"type": "function", "function": {
        "name": "play_media",
        "description": "Reproduce música o video en un servicio y destino.",
        "parameters": {"type": "object", "properties": {
            "service": {"type": "string", "enum": ["youtube", "netflix"]},
            "query": {"type": "string", "description": "Qué buscar o el título"},
            "target": {"type": "string", "enum": ["pc", "tele_sala"]},
        }, "required": ["service", "query"]}}},
    {"type": "function", "function": {
        "name": "set_volume",
        "description": "Cambia el volumen. level 0-100 o delta relativo.",
        "parameters": {"type": "object", "properties": {
            "level": {"type": "integer"}, "delta": {"type": "integer"},
            "target": {"type": "string", "enum": ["pc", "tele_sala"]},
        }}}},
    {"type": "function", "function": {
        "name": "launch_app",
        "description": "Abre una app o juego instalado por nombre aproximado.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
]

SYSTEM = ("Sos Luchi, un asistente de voz para Windows. Elegí una herramienta y sus argumentos "
          "para cumplir la orden. Si la orden no pide una acción, respondé en una frase corta.")

CASES = [
    ("poné música de Daft Punk", "play_media"),
    ("poné Interestelar en Netflix en la tele", "play_media"),
    ("subí el volumen", "set_volume"),
    ("quiero jugar Hollow Knight", "launch_app"),
]


def post(path, body):
    req = urllib.request.Request(URL + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def vram_mib():
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout.strip()
    used, total = (int(x) for x in out.split(","))
    return used, total


def ask(text):
    t0 = time.perf_counter()
    r = post("/api/chat", {
        "model": MODEL, "stream": False, "think": False, "keep_alive": "10m",
        "options": {"temperature": 0},
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
        "tools": TOOLS,
    })
    ms = (time.perf_counter() - t0) * 1000
    calls = r["message"].get("tool_calls") or []
    return ms, calls, r["message"].get("content", "")


def main():
    post("/api/generate", {"model": MODEL, "keep_alive": 0})  # descargar para medir en frío
    time.sleep(2)
    base, total = vram_mib()
    print(f"modelo: {MODEL} · VRAM base {base} / {total} MiB\n")
    ok = 0
    for i, (text, expected) in enumerate(CASES):
        ms, calls, content = ask(text)
        got = calls[0]["function"] if calls else None
        hit = bool(got) and got["name"] == expected
        ok += hit
        tag = "frío" if i == 0 else "caliente"
        print(f"[{'OK' if hit else 'X '}] {ms:7.0f} ms ({tag}) · {text!r}")
        print(f"       → {json.dumps(got, ensure_ascii=False) if got else repr(content)}")
    used, _ = vram_mib()
    print(f"\naciertos: {ok}/{len(CASES)} · VRAM con el modelo cargado: {used - base} MiB (+ base {base})")
    sys.exit(0 if ok == len(CASES) else 1)


if __name__ == "__main__":
    main()
