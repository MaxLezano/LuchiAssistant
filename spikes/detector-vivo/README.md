# Detector de "Luchi" en vivo (F0-12)

Prueba el detector propio con el micrófono en Windows, con **el mismo frontend en numpy** que va a usar `luchi-voice` (`spikes/wakeword/frontend.py`) y onnxruntime. No necesita PyTorch.

```powershell
cd D:\TRABAJO\LuchiAssistant\spikes\detector-vivo
uv run python escuchar.py                              # en vivo, hasta Ctrl+C
uv run python escuchar.py --minutos 60 --nota tele     # falsos positivos con la TV de fondo
uv run python escuchar.py --umbral 0.8                 # otro umbral
uv run python escuchar.py --archivo toma1.wav toma2.wav  # pasar grabaciones por el mismo camino
```

- Cada 80 ms evalúa la última ventana de 1,6 s; después de una detección ignora 2 s.
- Muestra el nivel del micrófono y la probabilidad de "Luchi" y "Oye Luchi" en vivo.
- Deja un CSV y un reporte `.md` en `E:\Luchi\pruebas-detector\` (fuera de git).
- Modelo por defecto: `E:\Luchi\models\detector\v2\detector.onnx`, umbral 0,7.

## Verificado (2026-10-02)

| Prueba | Resultado |
|---|---|
| Tomas reales de Luz no usadas para entrenar ("Luchi" normal, bajito, como pregunta) | Detectadas (0,84–0,86) |
| "Oye Luchi" normal y bajito | Detectadas como "Oye Luchi" (0,73–0,86) |
| "Luz", "prendé la luz", "lucha" | No se activa (máximo 0,08) |
| 15 s de micrófono en silencio | 0 detecciones |
| **Costo** | **1,0 ms por evaluación cada 80 ms (1,3 % de un núcleo)**, un solo hilo |
