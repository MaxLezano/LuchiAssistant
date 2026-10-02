# Spike: detector propio de "Luchi" (D29)

Detector de palabra de activación **propio**: frontend log-mel, red convolucional chica en PyTorch, exportada a ONNX y ejecutada con onnxruntime. Solo usa datos y voces con licencia que permite vender ([docs/LICENCIAS.md](../../docs/LICENCIAS.md)). openWakeWord queda como referencia; sus modelos y datos no se usan porque son no comerciales.

Se entrena en **WSL Ubuntu 24.04** (en `E:\Luchi\wsl`, con la RTX 3080). El código vive acá y el entorno y los datos en el disco de Ubuntu:

```bash
# dentro de WSL, como root
cd /mnt/d/TRABAJO/LuchiAssistant/spikes/wakeword
export UV_PROJECT_ENVIRONMENT=/root/luchi-wakeword/.venv HF_HOME=/root/luchi-wakeword/hf
uv sync
D=/root/luchi-wakeword/data
bash descargar.sh $D 10                       # negativos (~22 GB, CC BY 4.0), reanudable
python generar.py --datos $D --procesos 14    # ~153 mil clips sintéticos (≈ 25 min)
python calidad.py --datos $D                  # filtro con Whisper: descarta lo que no dice "Luchi"
python preparar_negativos.py --datos $D       # ~500 h de negativos → log-mel
python entrenar.py --datos $D                 # F0-11: entrena y exporta detector.onnx
python -m pytest test_frontend.py
```

## Piezas

| Archivo | Qué hace |
|---|---|
| `generar.py` | Muestras sintéticas de "Luchi", "Oye Luchi" y negativos parecidos ("luz", "Lucho", "Lucía"…) con voces de Piper de licencia permisiva. Los 904 hablantes de `en_US-libritts_r` reciben **fonemas del español** (`[[ lˈutʃi ]]`) para decirlo como acá |
| `variantes.py` | Mide qué escritura y qué voz pronuncian mejor cada frase (con Whisper) |
| `calidad.py` | Control de calidad: transcribe cada clip con faster-whisper y descarta los que no dicen la frase (o los negativos que suenan a "Luchi") |
| `descargar.sh` | LibriSpeech train-clean-100, Multilingual LibriSpeech en español (10 partes + dev/test) y MUSAN |
| `frontend.py` | Log-mel propio (40 bandas, 25 ms / 10 ms) en numpy (para la app) y PyTorch (para entrenar), probados como equivalentes |
| `preparar_negativos.py` | Negativos generales → features float16 en disco, con 10 % de validación por archivo |
| `entrenar.py` | F0-11: entrenamiento, validación (aciertos, voces reales, falsos positivos por hora) y exportación a ONNX |

## Decisiones medidas (F0-10)

Escucha del usuario sobre una muestra de 48 clips, y medición con Whisper sobre 40 clips por variante:

| Voz | "Luchi" | "Oye Luchi" | Uso |
|---|---|---|---|
| en_US-libritts_r (904 hablantes) con `[[ lˈutʃi ]]` | **85–90 %** | 25–35 % (`[[ ˈoʊ jˈeɪ lˈutʃi ]]`) | Principal para "Luchi"; validación con los hablantes 800–903 |
| es_ES-sharvard (2 hablantes) | ~45 % | **90–100 %** | Principal para "Oye Luchi" |
| es_ES-davefx | ~30 % | 60–80 % | Ambas |
| es_MX-claude, es_MX-ald | 0 % ("Loche") | ~0 % | Solo negativos |
| carlfm, mls_9972, mls_10246 | ininteligibles | — | Descartadas |

- Variación acotada (velocidad 0,85–1,25, ruido 0,5–0,75, ritmo 0,6–0,9): con más variación las voces deforman las palabras cortas.
- 1 hilo de onnxruntime por proceso: con 14 procesos de 16 hilos cada uno la generación bajaba a 18 clips/s; con 1 hilo, 104 clips/s.
- La validación en español la dan las **grabaciones reales** de la familia (`spikes/grabar-voz`, nunca a git).

## Dataset resultante (F0-10)

| Clase | Generados | Revisados con Whisper | Aceptados para entrenar | Validación aceptada |
|---|---|---|---|---|
| "Luchi" | 43.000 (39.000 + 3.900) | 15.000 | **10.875** (72 %) | 3.281 / 3.900 (84 %) |
| "Oye Luchi" | 66.000 (60.000 + 6.000) | 15.000 | **7.519** (50 %; sharvard 66 %, davefx 47 %, libritts 25 %) | 1.674 / 6.000 (28 %) |
| Negativos parecidos | 44.000 | Parcial: solo ~0,3 % sonaba a "Luchi" | **39.866** | 4.000 |
| Negativos generales | — | — | **496 h** | 41 h |

Whisper large-v3-turbo revisa ~9 clips/s en esta PC (probado uno a uno, por lotes, en float16 e int8): por eso se revisa una parte de los positivos. Los rechazados quedan en `data/rechazados/` para escucharlos.

## Entrenamiento (F0-11)

`python entrenar.py --datos $D [--real-train] [--pasos 30000]` → `modelos/<versión>/detector.onnx` (289 KB, 73 mil parámetros) + `reporte.json`. 30.000 pasos ≈ 30 min en la RTX 3080. Las versiones entrenadas se copian a `E:\Luchi\models\detector\<versión>\` (fuera de git).

| Versión | Datos | "Luchi" real (frases no vistas) | "Oye Luchi" real | Real que no es "Luchi" | Falsos positivos/h (20 h no vistas) | Sintético Luchi / Oye |
|---|---|---|---|---|---|---|
| v1 (umbral 0,7) | Solo sintéticos | **0/33** | 0/14 | 0/15 | 0,05 | 98,5 % / 99,0 % |
| **v2** (umbral 0,7) | + mitad de las frases reales de Luz (18 / 5 / 7 tomas) | **14/15** | 5/9 | 0/8 | 0,25 | 96,9 % / 96,9 % |

**Lección:** con solo positivos sintéticos, todo lo real que vio el modelo era negativo y aprendió en parte a reconocer "voz de computadora". Unas pocas tomas reales, aumentadas en cada lote, alcanzan para cambiarlo. Normalizar el volumen no influyó; la voz real tiene menos graves (micrófono de auricular) y es infantil (más aguda).

Próximo: voces reales de **otras personas** (para medir con alguien que el modelo no escuchó), más tomas de "Oye Luchi" y minería de negativos difíciles. Plan B si no alcanza: frontend con el `speech_embedding` de Google (Apache 2.0, convertido por nosotros desde el original).
