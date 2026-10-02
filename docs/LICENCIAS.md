# Licencias y desarrollo propio

> Principio (D28, pedido del usuario el 2026-10-01): **Luchi es casi todo desarrollo propio.** Lo que se toma de terceros tiene que ser open source con una licencia que **permita vender** el producto. Si no existe algo así, se hace.
> Esta tabla se actualiza **cada vez que se agrega una dependencia, un modelo o un dataset**: sin veredicto ✅, no entra.

## Criterio

| Veredicto | Licencias | Qué implica |
|---|---|---|
| ✅ Se usa | MIT, BSD, Apache 2.0, ISC, Unlicense, CC0, dominio público, CC BY | Conservar los avisos de copyright y atribuir en "Acerca de" |
| ⚠️ Con cuidado | LGPL (solo enlazada dinámicamente y reemplazable), CC BY-SA (solo datos, nunca en el modelo que se distribuye) | Revisar caso por caso y anotarlo acá |
| ❌ No se usa en el producto | GPL / AGPL en lo que se distribuye, CC BY-NC (no comercial), licencias "desconocidas" | Se reemplaza o se desarrolla |

Herramientas que solo se usan en desarrollo y **no se distribuyen** (por ejemplo, Visual Studio Build Tools) no afectan al producto, pero se anotan.

## Componentes

### App y sistema

| Componente | Uso | Licencia | Veredicto |
|---|---|---|---|
| Tauri 2 | App de escritorio | MIT / Apache 2.0 | ✅ |
| Rust std y crates | Núcleo | Mayormente MIT / Apache 2.0 (se revisa cada crate) | ✅ |
| onnxruntime | Inferencia de modelos propios | MIT | ✅ |
| SQLite | Datos locales | Dominio público | ✅ |
| Home Assistant | Casa (se instala aparte, no se modifica) | Apache 2.0 | ✅ |
| Integraciones de HA (Tuya oficial, Android TV Remote, Cast…) | Dispositivos | Apache 2.0 (parte de HA) | ✅ |
| yt-dlp | Buscar videos | Unlicense | ✅ |
| ffmpeg | Mezclar y codificar audio | LGPL 2.1+ (el build "full" de gyan.dev es **GPL**) | ⚠️ Para distribuir: build LGPL con `libmp3lame` (LGPL), invocado como proceso aparte |
| Visual Studio Build Tools | Compilar (solo desarrollo) | Licencia de Microsoft | No se distribuye |

### Voz e IA

| Componente | Uso | Licencia | Veredicto |
|---|---|---|---|
| Ollama | Servidor del LLM | MIT | ✅ |
| Qwen3-8B (pesos) | LLM | Apache 2.0 | ✅ |
| faster-whisper / CTranslate2 | Voz a texto | MIT | ✅ |
| Whisper (pesos, incluido large-v3-turbo) | Voz a texto | MIT | ✅ |
| Silero VAD | Fin de frase | MIT | ✅ |
| PyAudioWPatch | Micrófono y audio del sistema | Apache 2.0 | ✅ |
| PyTorch | Entrenar modelos propios | BSD-3 | ✅ |
| **openWakeWord** (código) | Referencia | Apache 2.0 | ✅ como referencia, pero ver la fila siguiente |
| **openWakeWord** (modelos incluidos, también el de embeddings, y el dataset `openwakeword_features`) | Detector | **CC BY-NC-SA 4.0** | ❌ **Detector propio** (D29) |
| **piper-tts** (OHF-Voice/piper1-gpl) | TTS | **GPL-3.0** | ❌ en el producto. Solo en spikes. Se reemplaza por inferencia propia con onnxruntime (D30) |
| **espeak-ng** | Texto → fonemas | **GPL-3.0** | ❌ en el producto. **Fonemizador propio** para el español (D30) |
| sherpa-onnx | Alternativa de TTS | Apache 2.0, pero usa espeak-ng para los modelos de Piper | ⚠️ Solo con nuestro fonemizador |

### Voces y datos de entrenamiento

| Componente | Uso | Licencia | Veredicto |
|---|---|---|---|
| Voz es_AR-daniela-high | Voz provisoria | CC BY-SA 4.0 (dataset OpenSLR 61) | ⚠️ Provisoria hasta F9; no se usa para generar datos de entrenamiento |
| Voces es_MX-claude (Apache 2.0), es_ES-davefx (CC0), es_MX-ald (Unlicense), es_ES-carlfm (dominio público), es_ES-sharvard (CC BY 3.0), es_ES-mls_* (CC BY 4.0) | Muestras sintéticas para el detector | Permisivas | ✅ |
| piper-sample-generator + generador LibriTTS-R | Muestras sintéticas con 904 hablantes | MIT + CC BY 4.0 (LibriTTS-R) | ✅ con atribución |
| LibriSpeech (OpenSLR 12) | Negativos en inglés | CC BY 4.0 | ✅ |
| Multilingual LibriSpeech, español (OpenSLR 94) | Negativos en español | CC BY 4.0 | ✅ |
| MUSAN (OpenSLR 17) | Música, habla y ruido | CC BY 4.0 | ✅ |
| Corpus de español latinoamericano (OpenSLR 61, 71–75) | Negativos en español | CC BY-SA 4.0 | ⚠️ No por ahora (share-alike) |
| MIT environmental impulse responses | Ecos de habitaciones | Sin especificar | ❌ Se generan ecos sintéticos propios |
| Grabaciones del usuario y su familia | Validación del detector, voz de F9 | Propias, con consentimiento | ✅ Nunca a git ni a la nube (PLAN.md §8) |

## Desarrollo propio planificado

| Pieza | Qué se hace | Dónde |
|---|---|---|
| Detector de "Luchi" | Modelo propio (log-mel + red convolucional chica) entrenado en PyTorch, exportado a ONNX y ejecutado con onnxruntime; datos sintéticos + negativos con licencias ✅ | F0-10..F0-13, D29 |
| Fonemizador de español | Reglas propias (la ortografía española es casi fonética), más un diccionario propio para nombres en inglés | F2-01, D30 |
| Motor de TTS | Inferencia de modelos VITS/Piper con onnxruntime, sin piper-tts | F2-01, D30 |
| Voz de Luchi | Modelo de voz propio entrenado con grabaciones propias (F9), con el mismo fonemizador | F9 |
| Personaje, interfaz, agente, router | Ya son propios | — |
