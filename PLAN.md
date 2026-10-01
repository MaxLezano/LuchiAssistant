# Luchi — Asistente de voz para Windows

> Plan de arquitectura, tecnologías y roadmap.
> Estado: **borrador v3.3** · Fecha: 2026-10-01
> Cambios: v1 → v2 en §13, v2 → v3 en §14.

---

## 1. Visión

**Luchi** es un asistente de voz que corre **100 % local** como app de Windows. Está siempre escuchando y se despierta cuando la llamas. Controla **la PC, la tele y las luces de la casa sin tocar teclado ni mouse**, y además **graba, transcribe y traduce** reuniones. Tiene un personaje propio, animado y personalizable, que muestra en qué está.

> "Luchi, prendé la luz del comedor"
> "Luchi, poné música de Daft Punk"
> "Luchi, poné Interestelar en Netflix en la tele"
> "Luchi, quiero jugar Hollow Knight"
> "Luchi, apagá todo"
> "Luchi, grabá esta reunión" … "Luchi, dejá de grabar" … "Traducí la última grabación al inglés"

### Principios

| Principio | Qué significa |
|---|---|
| **Solo voz** | Todo se tiene que poder hacer sin mirar la pantalla. Si Luchi necesita preguntar algo, lo pregunta **en voz alta**. La isla es un apoyo visual, no un requisito |
| **100 % gratis** | Solo software libre o gratuito, sin suscripciones, claves de pago ni planes "free tier" que puedan desaparecer |
| **100 % local** | Voz, IA, acciones y control de la casa corren en esta PC. Sin servicios en la nube ni APIs de terceros. A internet solo sale lo que tú pides (abrir YouTube, Netflix o una búsqueda). **Única excepción, opcional:** iniciar sesión con Google para guardar tus preferencias en tu Drive (§3.9) |
| **El LLM interpreta, el código ejecuta** | El modelo solo elige herramienta y argumentos. Nunca tiene acceso libre a la terminal |
| **Lista blanca de acciones** | Luchi solo puede hacer lo que está programado explícitamente |
| **Rápido para lo frecuente** | Las órdenes comunes ("apaga la luz", "pausa") se resuelven sin LLM. El LLM es para lo que no se entiende de forma directa |
| **Piezas intercambiables** | Arquitectura hexagonal: cambiar el modelo, el detector o la voz no obliga a tocar el resto |
| **El personaje es feedback** | Luchi muestra en qué estado está (escuchando, pensando, hablando, error…) con emociones animadas. Nunca es la única pista: lo importante también se dice en voz |

### El nombre

- **Luchi** = **Lu**z + mo**chi**. Luz en honor a mi hija; mochi por el personaje.
- Repo: `LuchiAssistant`. Paquetes: `luchi-desktop`, `luchi-voice`.
- **Palabra de activación: "Luchi"** (solo el nombre). A diferencia de "Luz", no choca con las órdenes de la casa ("prendé la luz"). Las palabras de dos sílabas dan más activaciones falsas, así que el spike de F0 mide los falsos positivos con TV de fondo; si son demasiados, el usuario puede pasar a **"Oye Luchi"** desde Ajustes (las dos opciones vienen entrenadas).
- Si algún día se publica hay que revisar que el nombre esté libre.

### El personaje

Un mochi blanco con forma de cuadrado redondeado, base rosada, ojos de punto y mejillas sonrojadas. Estilo minimalista japonés, cara mínima. **El diseño visual está terminado y aprobado como especificación:**

| Qué | Dónde |
|---|---|
| Diseño, mapa estado → emoción, reglas de interacción y personalización | [docs/PERSONAJE.md](docs/PERSONAJE.md) |
| 16 animaciones de referencia, catálogo y presets (abrir `visor.html`) | `mockups/animaciones/`, `mockups/personalizacion/` |
| Capas listas para la app + `catalogo.json` + orden de composición | `assets/luchi/` |
| Prototipo que define cada forma y línea de tiempo (la especificación ejecutable) | `mockups/animaciones/*.py` |
| Portada | `assets/branding/luchi_portada.png` |

Cómo se implementa en la app: §3.5.

---

## 2. Hardware y entorno

| Componente | Especificación | Uso en Luchi |
|---|---|---|
| CPU | AMD Ryzen 7 5800X (8 núcleos / 16 hilos) | Detector de palabra clave, VAD, app y lógica |
| RAM | 32 GB | App + VM de Home Assistant (2–4 GB) sin problema |
| GPU | NVIDIA RTX 3080, 12 GB de VRAM | LLM (~6 GB) + voz a texto (~1,5–3 GB) + TTS |
| Disco | C: 200 GB · D: 109 GB · E: 211 GB libres | Modelos y VM en D: o E: |
| SO | Windows 11 Pro | **Hyper-V disponible** para la VM de Home Assistant |
| Software | Node 24.12, Python 3.14 | Falta Rust, Ollama, uv + Python 3.12 |

**Limitación física:** el micrófono está en la PC. Funciona en la habitación de la PC; para hablarle desde otras habitaciones hacen falta satélites (F10).

**Grabaciones:** una hora de reunión en MP3 ocupa unos 60 MB a 128 kbps; se guardan en `Documentos\Luchi\Grabaciones` (configurable a D: o E:).

---

## 3. Arquitectura

### 3.1 Vista general

```
                    ┌────────────────────────────────────────────┐
  Micrófono ──────► │  luchi-voice  (Python, segundo plano)         │
  Parlantes ◄────── │  1. openWakeWord → detecta "Luchi"        │
                    │  2. Silero VAD   → detecta fin de la frase  │
                    │  3. faster-whisper (GPU) → texto            │
                    │  4. Piper (TTS)  → Luchi responde en voz alta │
  Audio del ──────► │  5. Grabador: micrófono + audio del sistema   │
  sistema           │     → MP3 + transcripción + traducción        │
                    └───────────────┬────────────────────────────┘
                                    │ WebSocket 127.0.0.1 + token
                                    │ wake / transcript / speak / recording
┌───────────────────────────────────▼──────────────────────────────────┐
│  luchi-desktop  (Tauri 2)                                              │
│                                                                      │
│  UI + Agente (TypeScript)                 Núcleo (Rust)              │
│  ┌──────────────────────┐   invoke()   ┌──────────────────────────┐  │
│  │ Isla + personaje     │ ───────────► │ Ejecutor (lista blanca)  │  │
│  ├──────────────────────┤              │ Catálogo de apps/juegos  │  │
│  │ Agente               │              │ Multimedia y volumen     │  │
│  │ 1. Router rápido     │              │ Navegador / deep links   │  │
│  │ 2. LLM (fallback)    │              │ Bandeja · autostart      │  │
│  └──┬────────────┬──────┘              └──────────────────────────┘  │
└─────┼────────────┼───────────────────────────────────────────────────┘
      │            │ HTTP (red local)
      │      ┌─────▼──────────────────────────┐
      │      │ Home Assistant (VM Hyper-V)    │ ──► luces, tele, enchufes
      │      │ Assist en español + REST/WS    │
      │      └────────────────────────────────┘
      │ HTTP localhost:11434
┌─────▼──────┐
│   Ollama   │  LLM local con tool calling (GPU)
└────────────┘
```

### 3.2 Flujo de una orden

1. **openWakeWord** escucha en la CPU todo el tiempo.
2. Dices **"Luchi"**: suena un tono corto, baja el borde negro de la isla, Luchi cae desde él como superhéroe (*aparecer*) y queda *escuchando*.
3. Dices "prende la luz del comedor". **Silero VAD** detecta que terminaste.
4. **faster-whisper** transcribe en la GPU → `transcript`.
5. El **router** del agente intenta resolverla sin LLM:
   - Órdenes de casa → se envían a **Home Assistant Assist** (`/api/conversation/process`), que ya entiende español y conoce tus habitaciones y dispositivos.
   - Órdenes fijas ("pausa", "sube el volumen", "siguiente") → acción directa.
6. Si el router no la resuelve, el agente manda el texto y las herramientas a **Ollama**, que responde por ejemplo `play_media({ service: "netflix", title: "Interestelar", target: "tele_sala" })`.
7. El agente valida y ejecuta (Rust para la PC, Home Assistant para la casa).
8. Luchi responde **en voz** ("Listo") y la isla muestra el resultado.
9. **Ventana de seguimiento:** durante ~6 s Luchi sigue escuchando sin necesidad de "Luchi" ("y bájale el volumen", "no, la otra").

### 3.3 Estados de la isla

```
 oculta ──"Luchi"──► escuchando ──fin de frase──► pensando ──► ejecutando ──► respondiendo ──► seguimiento (6 s) ──► oculta
                           │                            │              │                              │
                           └──── silencio 5 s ──────────┴──── error ───┴──► error (lo dice en voz) ──►┘
```

Cada estado tiene su emoción (aparecer, atento, escuchando, pensando, hablando, feliz, pregunta, apenado, dormido, esconderse…). El mapa completo y las reglas de transición están en [docs/PERSONAJE.md](docs/PERSONAJE.md) §3–4. Durante una grabación la isla queda compacta con un indicador de grabación (§3.6).

### 3.4 Dispositivos y destinos

Las órdenes de multimedia tienen un **destino**. Si no lo dices, Luchi usa el último o el predeterminado.

| Destino | Ejemplos de frase | Cómo se controla |
|---|---|---|
| `pc` | "aquí", "en la compu" | Rust: navegador, apps, teclas multimedia |
| `tele_sala` (ejemplo) | "en la tele" | Home Assistant `media_player` (encender, apagar, abrir app, volumen) |
| Luces / enchufes | "la luz del comedor" | Home Assistant por área y nombre |

El registro de dispositivos y alias (`"tele"` → `media_player.tv_sala`) vive en un archivo de configuración y se sincroniza con las áreas de Home Assistant.

**Conectar dispositivos desde la app:** cada usuario agrega sus luces, teles y enchufes en **Ajustes → Casa y dispositivos**, sin abrir Home Assistant:

1. Luchi muestra lo que **se detectó solo en la red** (Chromecast, Hue, Sonos, enchufes…) con un botón "Agregar".
2. "Agregar dispositivo" abre un asistente: marca → paso de conexión (apretar el botón del puente, aceptar en la tele, código de la tele o cuenta de la marca) → nombre, habitación y apodos → "Probalo".
3. Por debajo, la app maneja los **flujos de configuración de Home Assistant** a través de su API (`/api/config/config_entries/flow`, la misma que usa la interfaz de HA). Esa API no está documentada como pública y puede cambiar entre versiones: se fija la versión de HA y, si un flujo falla, se ofrece abrir la página de HA embebida.
4. Si es el primer uso y no hay Home Assistant, la bienvenida ofrece instalarlo en la VM con un clic.

Las marcas que solo funcionan por la **nube del fabricante** (Tuya/Smart Life, Xiaomi…) se pueden conectar igual, pero Luchi avisa antes que esas órdenes salen a internet. **Google Home no se puede conectar**: sus APIs para terceros solo funcionan en apps Android/iOS certificadas y pasan por la nube.

### 3.5 Personaje e isla

**Cómo se ve en el escritorio:** arriba al centro hay un **borde negro** (como el notch de un teléfono) y **Luchi flota justo debajo**. Cuando Luchi se esconde, el borde también desaparece. Al decir "Luchi", el borde baja y Luchi cae desde él con la animación *aparecer* (aterrizaje de superhéroe); al terminar mira a los costados y salta de vuelta hacia el borde (*esconderse*); debajo de Luchi aparece un globo con lo que escuchó y lo que responde. Durante una grabación queda solo el borde, más ancho, con un punto rojo y el tiempo. La ventana de la isla es transparente y deja pasar los clics (salvo sobre Luchi o el borde).

Luchi se **dibuja en vivo** dentro de la isla (no hay videos ni secuencias de imágenes), siguiendo la especificación de [docs/PERSONAJE.md](docs/PERSONAJE.md) y los assets de `assets/luchi/`.

| Pieza | Qué hace |
|---|---|
| **Renderer** (Canvas 2D) | Compone las capas en el orden de `assets/luchi/README.md`: sombra, cuerpo del color elegido, tatuajes (`multiply`), mejillas, ojos (sprite que se achata para parpadear), párpados, tinta (ojos cerrados, cejas), boca (un contorno que se transforma), accesorio y adornos. Después transforma todo como un bloque (squash & stretch, altura, rotación, desplazamiento) |
| **Emociones** | Cada una es una línea de tiempo de parámetros de expresión y del cuerpo, igual que en `mockups/animaciones/animaciones.py`. Se portan a TypeScript una por una |
| **Máquina de estados** | Traduce el estado de la app a una emoción (mapa de PERSONAJE.md §3) y aplica las reglas: feedback < 150 ms, *pensando* solo si tarda > 400 ms, nunca dos expresiones a la vez, vuelta a neutral entre emociones fuertes |
| **Datos en vivo** | *escuchando* usa el nivel real del micrófono; *hablando* mueve la boca con la amplitud del TTS. Ambos llegan por el WebSocket de `luchi-voice` |
| **Personalización** | Lee `catalogo.json` y el diseño del usuario (JSON chico en la PC). Cualquier combinación funciona con todas las emociones porque las animaciones solo mueven significados |
| **Accesibilidad** | Movimiento reducido (respeta la preferencia de Windows), click-through salvo al pasar el mouse, oculto en juegos a pantalla completa |

### 3.6 Grabar, transcribir y traducir reuniones

> "Luchi, grabá esta reunión" → … → "Luchi, dejá de grabar"

1. **Inicio:** Luchi confirma en voz ("Grabando. Acordate de avisarle a los demás") y la isla queda **compacta** con un punto rojo y el tiempo transcurrido. Mientras graba sigue escuchando "Luchi".
2. **Captura en dos pistas:** el **micrófono** (tu voz) y el **audio del sistema** (lo que sale por los parlantes: los demás en Meet, Zoom, Teams o cualquier app) con WASAPI loopback. Ir en dos pistas permite separar **"Yo" / "Otros"** sin modelos de identificación de voces.
3. **Fin:** se mezclan las pistas en **`audio.mp3`** y se transcribe cada pista con faster-whisper (detecta el idioma solo). Las frases se ordenan por tiempo en **`transcripcion.txt`**:
   ```
   [00:01:23] Yo: ¿Arrancamos con el tema del deploy?
   [00:01:27] Otros: Sí, ya está listo en staging.
   ```
4. Luchi avisa en voz: "Listo, guardé la grabación y la transcripción". Si la reunión fue larga, transcribe en segundo plano y avisa al terminar.
5. **Traducción, después y a pedido:** "Luchi, traducí la última grabación al inglés", o desde la lista de grabaciones con un selector de idioma → `transcripcion.en.txt`. Solo se traduce el texto, no el audio.
6. **Extra opcional:** "Luchi, resumí la reunión" → `resumen.txt` con el LLM local.

Cada grabación queda en su propia carpeta:

```
Documentos\Luchi\Grabaciones\
└─ 2026-10-01_1530_reunion\
   ├─ audio.mp3
   ├─ transcripcion.txt
   ├─ transcripcion.en.txt     # una por idioma pedido
   └─ resumen.txt              # opcional
```

| Decisión | Por qué |
|---|---|
| Audio del sistema completo por defecto | Funciona con cualquier app de reuniones. La captura de **una sola app** (process loopback de Windows) evita grabar notificaciones, pero hay reportes de que graba silencio en Windows 11 build 26200 y esta PC tiene la 26300: se prueba en un spike y queda como opción si funciona |
| Transcribir al terminar, no en vivo | Más preciso y no compite por la GPU durante la reunión |
| Traducir con el LLM local (Ollama) | Ya está cargado y traduce bien entre idiomas comunes. **Argos Translate** queda como alternativa offline más liviana |
| MP3 | Se reproduce en cualquier lado |


### 3.7 Interfaz de la app

Prototipo navegable en `mockups/ui/index.html` (se abre en el navegador; también con enlaces directos como `#tuluchi`, `#casa`, `#grabaciones`, `#bienvenida`, `#isla`). Especificación de cada pantalla en [docs/INTERFAZ.md](docs/INTERFAZ.md).

| Pantalla | Qué tiene |
|---|---|
| Isla | Borde negro + Luchi + globo de texto; estado de grabación compacto |
| Bandeja del sistema | Ajustes, Tu Luchi, Grabaciones, Dispositivos, Recordatorios, Historial, Estado del sistema, silenciar micrófono, dejar a Luchi visible, salir |
| Bienvenida (primer uso) | Hola → micrófono y prueba de "Luchi" → casa (instalar/conectar HA) → elegir un Luchi → ejemplos de órdenes |
| Barra lateral | Agrupada: **Luchi** (General, Voz y micrófono, Tu Luchi) · **Casa y PC** (Casa y dispositivos, Apps y sistema, Escenas y atajos) · **Tus cosas** (Recordatorios, Grabaciones, Historial) · **Cuenta** (Cuenta y sincronización, Privacidad, Estado del sistema, Acerca de) · **Desarrollo** (Laboratorio, solo en desarrollo) |
| Ajustes · General | Inicio con Windows, tema, idioma; posición, monitor y tamaño de la isla, sonidos, movimiento reducido, ocultar en juegos; accesibilidad (subtítulos grandes, duración, alto contraste) |
| Ajustes · Voz y micrófono | "Luchi" u "Oye Luchi", sensibilidad, prueba, atajo de teclado, micrófono con nivel, voz de Luchi, ventana de seguimiento, dictado, preguntas generales |
| Tu Luchi | Editor con vista previa (poses neutral/feliz/hablando, fondo claro/oscuro), pestañas Color, Mejillas, Ojos, Boca, Tatuajes (patrón + hasta 3 diseños por posición), Accesorios (por categoría, temporada automática, hemisferio, cumpleaños) y Presets; Sorprendeme, Restablecer, Guardar |
| Casa y dispositivos | Estado de Home Assistant, detectados en la red, dispositivos por habitación con apodos, asistente para agregar, destino de video por defecto |
| Apps y sistema | Fuentes detectadas (Menú Inicio, Steam, Epic, Riot, Battle.net, EA, Ubisoft…), apodos y permiso para abrir cada una; acciones del sistema (salida de audio, capturas, carpetas favoritas, bloquear, suspender/apagar) |
| Escenas y atajos | Lista con probar/editar, editor (frase → acciones en orden), horarios |
| Recordatorios | Vencidos con la PC apagada, próximos, nuevo, ajustes (despertar de la suspensión, avisar al prender, sonido, posponer) |
| Historial | Órdenes con lo que entendió y lo que hizo, filtros, "Esto estuvo mal", corrección por voz |
| Grabaciones | Lista, reproductor, transcripción "Yo / Otros", ver traducida en otro idioma, resumen, abrir carpeta, borrar; ajustes de grabación |
| Cuenta y sincronización | Iniciar sesión con Google, qué se sincroniza, exportar/importar `.luchi`, copia local automática |
| Estado del sistema | Estado de cada servicio y de la GPU, diagnóstico guiado, modo juego automático, latencia |
| Laboratorio (desarrollo) | Emociones, parámetros del renderer, comparación con el prototipo, tests visuales |
| Privacidad · Acerca de | Silenciar, historial, borrar datos, registros; portada y versión |


### 3.8 Recursos de diseño y cómo entran al desarrollo

Todo el diseño ya existe en el repo. Esta tabla dice qué es cada cosa y qué se hace con ella al programar.

| Recurso | Dónde | Qué se hace al desarrollar |
|---|---|---|
| Especificación del personaje | `docs/PERSONAJE.md` | Fuente de verdad del mapa estado → emoción, reglas de interacción y personalización |
| Especificación de la interfaz | `docs/INTERFAZ.md` | Fuente de verdad de cada pantalla, tokens visuales, estados de la isla y menú de la bandeja |
| Capas del personaje + `catalogo.json` | `assets/luchi/` | Se copian a `apps/desktop/public/luchi/` en cada build (script `copy-assets`). No se editan a mano: se regeneran con `generar.py assets` |
| Portada | `assets/branding/luchi_portada.png` | README de GitHub, pantalla Acerca de, bienvenida e instalador |
| Prototipo del personaje (Python) | `mockups/animaciones/luchi.py`, `tatuajes.py`, `accesorios.py`, `animaciones.py` | **Especificación ejecutable.** El renderer se porta a `character/adapters/CanvasRenderer.ts` y cada emoción a `character/domain/emotions/<nombre>.ts`, mismos parámetros y tiempos |
| Animaciones de referencia | `mockups/animaciones/*.webp`, `emociones.png`, `visor.html` | **Referencia visual y tests de regresión:** se exportan frames con `generar.py <emoción> --frames` y el renderer TS se compara cuadro por cuadro con tolerancia (§10) |
| Catálogo de personalización | `mockups/personalizacion/` | Referencia del editor "Tu Luchi" y control de calidad de combinaciones (presets) |
| Prototipo de la interfaz | `mockups/ui/index.html`, `ui.css`, `ui.js` | **Referencia de pantallas.** Los tokens de `ui.css` pasan a `apps/desktop/src/shared/design/tokens.css`; los controles (interruptor, segmentado, chip, filas de ajustes, grilla de opciones, tarjetas) pasan a componentes presentacionales (atomic design); los textos se reutilizan tal cual |
| Piezas del prototipo de UI | `mockups/ui/piezas/`, `generar_piezas.py`, `datos.js` | Solo para el prototipo (la app dibuja bocas y ojos en vivo) |
| Imágenes de origen | `mockups/animaciones/fuentes/` | Imagen elegida y cuerpo sin cara generados con ComfyUI; solo para regenerar assets |

**Pantallas por fase** (cada fase construye las pantallas que su funcionalidad necesita, siguiendo el prototipo):

| Fase | Pantallas y piezas visuales |
|---|---|
| F1 | Tokens y componentes base · isla (borde + Luchi + globo) · menú de la bandeja · Ajustes › General (lo básico) · Estado del sistema · Laboratorio del personaje |
| F2 | Ajustes › Voz y micrófono · Casa y dispositivos (estado y lista) |
| F3 | Ajustes › Voz › Preguntas generales |
| F4 | Apps y sistema (incluye acciones del sistema) |
| F5 | Casa y dispositivos: asistente para agregar, detectados en la red, video por defecto |
| F6 | Grabaciones (lista, detalle, traducción) · isla en modo grabación |
| F7 | Historial · Recordatorios · Ajustes › Voz › Dictado · isla: aviso de recordatorio y corrección |
| F8 | Escenas y atajos de voz |
| F11 | Bienvenida · Privacidad · Acerca de · Ajustes › General › Accesibilidad · interacciones extra del personaje |
| F12 | Tu Luchi (editor completo) · Cuenta y sincronización |

### 3.9 Cuenta y sincronización (opcional, con Google)

- **Sin cuenta** (por defecto): todo queda en la PC. Copia automática semanal en `Documentos\Luchi\Copias` y **exportar / importar** a un archivo `.luchi` (para llevar o compartir tu Luchi).
- **Con cuenta de Google:** botón "Iniciar sesión con Google" en Ajustes › Cuenta. Las preferencias se guardan en la **carpeta oculta de la app en tu Google Drive** (`appDataFolder`), con el permiso `drive.appdata`, que es no sensible y solo da acceso a los datos de la propia app, no al resto de tus archivos.
- **Qué se sincroniza:** diseño de Tu Luchi, ajustes, apodos de apps y dispositivos, escenas y recordatorios. **Grabaciones y transcripciones: apagado por defecto.** Nunca se suben contraseñas, tokens ni el historial de órdenes.
- **Cómo:** OAuth 2.0 para apps de escritorio (se abre el navegador y vuelve a la app por `localhost`). El token se guarda en el Administrador de credenciales de Windows. Si hay conflicto entre dos PCs, gana el cambio más reciente por sección y se avisa.
- Es gratis: usa el espacio de Drive del propio usuario.

### 3.10 Recordatorios, correcciones y otras funciones

| Función | Cómo funciona |
|---|---|
| **Temporizadores y recordatorios** | "Avisame en 10 minutos", "recordame mañana a las 9…". Se guardan en la PC; Luchi aparece y lo dice en voz (con "posponé 5 minutos" / "listo"). **Si la PC está apagada no puede avisar en el momento:** al prenderla, Luchi cuenta lo que venció. Opcional: despertar la PC de la *suspensión* con una tarea programada de Windows (no funciona si está apagada) |
| **Corregir por voz o con un botón** | Justo después de una orden se puede decir **"Luchi, eso no es lo que quería"** o **"eso está mal"**: Luchi deshace lo que se pueda (apagar lo que prendió, cerrar lo que abrió, bajar el volumen que subió), pregunta qué querías, lo hace y lo anota. En el Historial, cada orden tiene el botón **"Esto estuvo mal"**. Cada corrección entra al set de evaluación |
| **Dictado** | "Luchi, escribí: …" escribe en la app activa. En chats escribe pero no envía, salvo que digas "y mandalo" |
| **Preguntas generales** | Respuestas cortas del LLM local en voz, sin internet. Largo configurable |
| **Acciones del sistema** | Cambiar la salida de audio, capturas de pantalla, carpetas favoritas con apodos, bloquear la PC; suspender o apagar siempre con confirmación |
| **Escenas y atajos de voz** | Pantalla para crearlas sin código: frase → lista de acciones (dispositivo, app, volumen, reproducir, esperar, que Luchi diga algo), con horarios opcionales |
| **Estado del sistema** | Micrófono, detector, voz a texto, LLM, voz, Home Assistant, dispositivos y GPU/VRAM, con diagnóstico guiado y modo juego automático |
| **Laboratorio del personaje** | Herramienta de desarrollo: dispara emociones, mueve parámetros y compara el renderer de la app con el prototipo. No se incluye en la versión para usuarios |
| **Subtítulos accesibles** | Texto de Luchi más grande, más tiempo en pantalla y alto contraste |
---

## 4. Tecnologías

| Capa | Tecnología | Por qué |
|---|---|---|
| App de escritorio | **Tauri 2** | Ventana transparente siempre visible, poca RAM, deja la GPU libre para la IA |
| UI | TypeScript + Vite | Ligera. Se suma React o Svelte si crece |
| Núcleo de sistema | Rust | Lanza procesos sin `cmd`, lee el catálogo, maneja ventanas, teclas multimedia y volumen |
| LLM | **Ollama** con `qwen3:8b` como candidato | Tool calling, ~6 GB de VRAM. Usar con **thinking desactivado** (`think: false`) para no sumar latencia. Comparar 2–3 modelos en F3 |
| Palabra de activación | **openWakeWord** | Open source y 100 % offline. "Luchi" se entrena con muestras sintéticas generadas con Piper en español |
| Fin de frase | **Silero VAD** | Detecta cuándo dejaste de hablar |
| Voz a texto | **faster-whisper** (GPU), probar `large-v3-turbo` vs `medium` | Buen español; `turbo` es casi tan preciso como `large` y mucho más rápido |
| Voz de Luchi | **Piper** con una voz en español | Local, rápido, corre en CPU |
| Casa | **Home Assistant OS** en una VM de Hyper-V | Integra casi cualquier marca de luces y teles. Assist entiende español sin LLM. Es la instalación recomendada en Windows (Docker en Windows no está soportado oficialmente) |
| Comunicación voz ↔ app | WebSocket en `127.0.0.1` con token | Simple y solo local |
| Personaje | **Canvas 2D** + assets de `assets/luchi/` | Suficiente para componer capas, transformar y usar `multiply`; sin dependencias extra. Se evalúa PixiJS solo si hiciera falta rendimiento |
| Audio del sistema | **PyAudioWPatch** (WASAPI loopback) | Graba lo que suena en los parlantes; tiene wheels para Python 3.12 |
| Codificación de audio | **ffmpeg** | Mezcla las pistas y genera MP3. Libre y local |
| Traducción | **Ollama** (el mismo LLM); alternativa **Argos Translate** | Todo offline |
| Datos locales | **SQLite** | Historial, recordatorios, escenas, grabaciones (índice) y ajustes; un solo archivo en la PC |
| Cuenta opcional | **Google OAuth 2.0** + **Drive `appDataFolder`** (`drive.appdata`) | Guardar preferencias en el Drive del usuario; gratis y con el permiso más acotado |
| Recordatorios con la PC suspendida | Programador de tareas de Windows (despertar para ejecutar) | Opcional; no sirve con la PC apagada |
| YouTube | **yt-dlp** con `ytsearch1:` | ID del primer video sin API key |
| Netflix / películas | Deep links (`netflix.com/watch/<id>`) + resolución de título a ID (ver §6.1) | Netflix no tiene API pública |
| Entorno Python | **uv** + Python 3.12 | La 3.14 es muy nueva para varias librerías de audio e IA |
| Tests | Vitest · `cargo test` · pytest | El dominio se prueba con mocks, sin IA ni micrófono |

---

## 5. Estructura del proyecto

Screaming architecture por features, con hexagonal dentro de cada una.

```
LuchiAssistant/
├─ CLAUDE.md                        # contexto y reglas para Claude Code (se lee solo al abrir el proyecto)
├─ PLAN.md
├─ README.md
├─ assets/
│  ├─ luchi/                        # capas del personaje + catalogo.json (generado)
│  └─ branding/                     # portada
├─ docs/
│  └─ PERSONAJE.md                  # especificación del personaje
├─ mockups/                         # prototipo visual (Python) y previews
├─ config/
│  └─ devices.yaml                  # destinos, alias, defaults (sin secretos)
├─ apps/
│  └─ desktop/                      # luchi-desktop (Tauri)
│     ├─ src/
│     │  ├─ assistant/              # feature: interpretar y ejecutar órdenes
│     │  │  ├─ domain/              # Command, ToolCall, Target, ActionResult
│     │  │  ├─ ports/               # LlmPort, ActionPort, HomePort, VoicePort
│     │  │  ├─ application/         # handleTranscript, router, conversación
│     │  │  └─ adapters/            # OllamaLlm, TauriActions, HomeAssistant, VoiceSocket
│     │  ├─ media/                  # feature: qué reproducir y dónde
│     │  │  ├─ domain/              # MediaRequest, Service, Target
│     │  │  ├─ ports/               # TitleResolverPort, MediaTargetPort
│     │  │  └─ adapters/            # YouTube, Netflix, PcTarget, HaTvTarget
│     │  ├─ island/                 # feature: la isla
│     │  │  ├─ containers/          # máquina de estados app → emoción
│     │  │  └─ components/          # presentacionales (atomic design)
│     │  ├─ character/              # feature: el personaje
│     │  │  ├─ domain/              # Expression, BodyTransform, Style, Emotion (timelines)
│     │  │  ├─ application/         # player de emociones, transiciones, datos en vivo
│     │  │  └─ adapters/            # CanvasRenderer, CatalogLoader, DesignStore
│     │  ├─ recordings/             # feature: lista de grabaciones, abrir, traducir
│     │  │  └─ components/
│     │  ├─ reminders/              # feature: temporizadores y recordatorios
│     │  ├─ scenes/                 # feature: escenas y atajos de voz (editor + ejecución)
│     │  ├─ history/                # feature: historial, correcciones, deshacer
│     │  ├─ sync/                   # feature: cuenta de Google, exportar/importar, copias locales
│     │  ├─ status/                 # feature: estado del sistema y diagnóstico
│     │  ├─ devtools/lab/           # laboratorio del personaje (solo en desarrollo)
│     │  ├─ shared/design/          # tokens.css + componentes base (de mockups/ui)
│     │  └─ main.ts
│     ├─ public/luchi/              # copia de assets/luchi (capas + catalogo.json)
│     └─ src-tauri/src/             # Rust
│        ├─ apps/                   # catálogo + abrir/cerrar
│        │  ├─ start_menu.rs
│        │  ├─ steam.rs
│        │  └─ launcher.rs
│        ├─ system/                 # volumen, teclas multimedia, foco de ventana
│        ├─ browser.rs              # abrir URLs validadas
│        ├─ actions.rs              # comandos expuestos (lista blanca)
│        └─ lib.rs                  # ventana, bandeja, autostart
└─ services/
   └─ voice/                        # luchi-voice (Python)
      ├─ luchi_voice/
      │  ├─ listening/              # feature: wake word, VAD, transcripción de órdenes, TTS
      │  │  ├─ domain/              # Wake, Listening, Transcript, Speak
      │  │  ├─ ports/               # WakeWordPort, VadPort, SpeechToTextPort, TextToSpeechPort
      │  │  └─ adapters/            # OpenWakeWord, SileroVad, FasterWhisper, Piper
      │  ├─ recording/              # feature: grabar, transcribir y traducir reuniones
      │  │  ├─ domain/              # Recording, Track (yo/otros), Segment, Transcript
      │  │  ├─ ports/               # AudioCapturePort, EncoderPort, TranslatorPort
      │  │  └─ adapters/            # MicCapture, LoopbackCapture, Ffmpeg, OllamaTranslator, Argos
      │  ├─ shared/                 # WsServer, configuración
      │  └─ main.py
      ├─ models/                    # oye_luchi.onnx, voces Piper (no van a git)
      └─ pyproject.toml
```

### Puertos clave

| Puerto | Adaptador inicial | Alternativas futuras |
|---|---|---|
| `WakeWordPort` | openWakeWord | microWakeWord, atajo de teclado (siempre disponible) |
| `SpeechToTextPort` | faster-whisper | whisper.cpp |
| `TextToSpeechPort` | Piper | Voz de Luchi clonada (F9) |
| `LlmPort` | Ollama | LM Studio, llama.cpp |
| `HomePort` | Home Assistant (Assist + REST) | — |
| `TitleResolverPort` | Ver §6.1 | Catálogo propio de favoritos |
| `ActionPort` | Comandos Tauri | — |
| `AudioCapturePort` | Micrófono + WASAPI loopback (todo el sistema) | Loopback de una sola app |
| `TranslatorPort` | Ollama | Argos Translate |

---

## 6. Herramientas del agente

| Herramienta | Argumentos | Cómo la resuelve el código | Confirmación |
|---|---|---|---|
| `home_command` | `text` | Se pasa tal cual a Home Assistant Assist | Solo cerraduras/alarmas |
| `home_action` | `entity`, `action`, `value?` | Llamada directa a un servicio de HA (cuando Assist no alcanza) | Solo cerraduras/alarmas |
| `play_media` | `service` (youtube, netflix…), `query` o `title`, `target?` | Resuelve qué reproducir y lo abre en el destino (ver §6.1) | No |
| `media_control` | `action` (pausa, play, siguiente, pantalla completa), `target?` | PC: teclas multimedia / foco de ventana. Tele: HA `media_player` | No |
| `set_volume` | `level` o `delta`, `target?` | PC: API de audio de Windows. Tele: HA | No |
| `launch_app` | `query` | Búsqueda aproximada en el catálogo. Si hay varias, **pregunta en voz** | No |
| `close_app` | `query` | Cierre normal (`WM_CLOSE`), nunca forzado | No |
| `open_url` | `url` | Solo `http`/`https` | No |
| `web_search` | `query` | Abre los resultados en el navegador | No |
| `start_recording` | `title?` | Graba micrófono + audio del sistema en dos pistas | Recordatorio en voz de avisar a los participantes |
| `stop_recording` | — | Cierra el MP3 y transcribe (en segundo plano si es larga) | No |
| `translate_recording` | `recording?` (última por defecto), `language` | Traduce `transcripcion.txt` a `transcripcion.<idioma>.txt` | No |
| `summarize_recording` *(opcional)* | `recording?` | Resumen con el LLM local → `resumen.txt` | No |
| `open_recordings` | — | Abre la carpeta o la lista de grabaciones | No |
| `set_timer` / `set_reminder` | `duration` o `datetime`, `text`, `repeat?` | Guarda en SQLite y programa el aviso | No |
| `list_reminders` / `cancel_reminder` | `id?` | | No |
| `report_mistake` | `what_was_wanted?` | Marca la última orden como error, deshace si es reversible y pregunta qué querías | No |
| `undo_last` | — | Deshace la última acción reversible | No |
| `dictate` | `text`, `send?` | Escribe en la app activa; solo envía si se pide | No |
| `set_audio_output` | `device` | Cambia la salida de audio de Windows | No |
| `screenshot` | `area?` | Guarda en Imágenes\Capturas | No |
| `open_folder` | `name` | Carpetas favoritas por apodo | No |
| `lock_pc` | — | | No |
| `sleep_pc` / `shutdown_pc` | `delay?` | | **Sí, en voz** |
| *(F8)* `run_scene` | `name` | Secuencia de herramientas definida en la pantalla de escenas ("modo cine") | No |

Las **preguntas generales** no son una herramienta: si la orden no pide una acción, el LLM responde en voz con una respuesta corta.

**Fuera de la lista blanca, por diseño:** comandos de terminal, borrar archivos, apagar la PC sin confirmación, instalar software, compras.

### 6.1 Reproducir películas y series

| Paso | PC | Tele |
|---|---|---|
| 1. Título → ID | **Catálogo local** de títulos (`config/titles.yaml`, título + alias → ID de Netflix). Se arma a mano o se agrega por voz la primera vez ("Luchi, guarda esta película") leyendo el ID de la pestaña abierta. Sin servicios de terceros | Igual |
| 2. Abrir | Navegador en `netflix.com/watch/<id>` y pantalla completa | Depende de la marca: Android/Google TV por ADB (intent con el ID), LG webOS por comando de lanzamiento con `contentId`, otras solo abren la app |
| 3. Si no hay ID | Abre la búsqueda de Netflix con el título y lo dice en voz | Abre la app de Netflix |

Notas:
- No hay API oficial de Netflix y no se usan servicios externos de terceros, por eso el catálogo es local. Va detrás de `TitleResolverPort` y siempre hay un plan B (abrir la búsqueda de Netflix).
- YouTube en la tele: con Chromecast/Google TV se envía el ID del video desde Home Assistant.
- Qué se puede hacer en la tele depende del modelo exacto: se define en el **inventario de F0**.

---

## 7. Roadmap

Cada fase deja algo usable de punta a punta. Lo que más se usa (casa, música, tele) llega antes que el pulido.

| Fase | Entregable | Cuándo está lista |
|---|---|---|
| **F0 · Preparación** | Instalar herramientas, VM de Home Assistant, **inventario** de luces/tele/parlantes y **spike de openWakeWord** con "Luchi" | HA ve las luces y la tele; el detector reconoce "Luchi" en una prueba con < 1 falso positivo por hora de TV de fondo |
| **F1 · Escucha y personaje** | `luchi-voice` (wake + VAD + whisper + WebSocket) e isla en Tauri con el **renderer del personaje** (cuerpo, cara paramétrica, estilo por defecto) y las emociones *aparecer, atento, escuchando* (con nivel real del micrófono), *esconderse* y *dormido*. Atajo de teclado como alternativa. **Laboratorio del personaje** y tests visuales. **Estado del sistema** (micrófono y detector) | "Luchi, hola": Luchi cae desde el borde, escucha, muestra "hola" y se esconde saltando hacia arriba |
| **F2 · Casa** | Router + `home_command` vía Home Assistant Assist. Piper responde en voz. Emociones *hablando* (boca con la amplitud del TTS), *feliz*, *guiño* y *apenado* | "Luchi, prende la luz del comedor" funciona y Luchi contesta "Listo" |
| **F3 · Cerebro** | Agente con Ollama y tool calling. `play_media` (YouTube en PC), `media_control`, `set_volume`, `open_url`, `web_search`. **Preguntas generales.** Comparar modelos con el set de órdenes. Emoción *pensando* (> 400 ms) | "Luchi, pon lofi" y "pausa" funcionan |
| **F4 · Apps y sistema** | Catálogo (Menú Inicio, Steam; luego Epic/Xbox), `launch_app`, `close_app`, preguntas de aclaración por voz con la emoción *pregunta*. **Acciones del sistema:** salida de audio, capturas, carpetas, bloquear, suspender/apagar con confirmación | Abre y cierra juegos por nombre sin mirar la pantalla |
| **F5 · Tele y películas** | Destinos multimedia, encender/apagar la tele, abrir YouTube/Netflix en la tele o en la PC, `TitleResolverPort` | "Luchi, pon Interestelar en Netflix en la tele" |
| **F6 · Grabar reuniones** | Grabación en dos pistas (micrófono + audio del sistema), MP3, transcripción "Yo / Otros", traducción a pedido, lista de grabaciones con selector de idioma, isla compacta con indicador de grabación. Spike de loopback de una sola app (§3.6) | "Grabá esta reunión" → "dejá de grabar" deja `audio.mp3` y `transcripcion.txt`; "traducí la última al inglés" crea `transcripcion.en.txt` |
| **F7 · Conversación y memoria** | Ventana de seguimiento, contexto de la última orden ("bájale", "la otra"), memoria corta de preferencias. **Historial** con correcciones por voz ("eso no es lo que quería") y por botón, y deshacer. **Recordatorios y temporizadores.** **Dictado.** Emociones *mareado* (muchas órdenes a la vez), *cansado* (de noche), *amor* y *enojado* (easter eggs) | Diálogo de 2–3 turnos sin repetir "Luchi" |
| **F8 · Escenas y rutinas** | `run_scene` ("modo cine", "buenas noches"), **pantalla para crearlas sin código**, horarios, "apaga todo" | Una frase dispara varias acciones |
| **F9 · La voz de Luchi** | Clonación de voz local (ver §8) | Luchi habla con su voz |
| **F10 · Toda la casa** *(opcional)* | Micrófonos en otras habitaciones con firmware libre que envían el audio a `luchi-voice` en esta PC. Requiere comprar hardware; el software sigue siendo gratis y local | Se le habla desde el comedor sin estar en la PC |
| **F11 · Pulido** | Ajustes con UI, autostart, sensibilidad, modo juego automático (libera VRAM), movimiento reducido, **subtítulos accesibles**, bienvenida, instalador. Interacciones extra del personaje: mirada al cursor, apretarlo (squish), bailar con la música (PERSONAJE.md §9) | Uso diario sin fricción |
| **F12 · Tu Luchi** | Editor para personalizar color (10), mejillas, ojos (6), boca (6), tatuajes (7 patrones + 19 diseños, hasta 3 a la vez) y accesorios (23: diarios, divertidos y de temporada, con fechas automáticas opcionales). Vista previa animada en vivo. Diseño y assets listos en `assets/luchi/` (ver [docs/PERSONAJE.md](docs/PERSONAJE.md) §7). **Cuenta de Google opcional** para guardar preferencias en Drive, **exportar/importar** y copias locales (§3.9) | Cada usuario arma su Luchi, todas las emociones siguen funcionando y sus preferencias lo siguen a otra PC |

### Set de evaluación

Desde F2 se mantiene un archivo con **órdenes reales grabadas** y el resultado esperado. Cada cambio de modelo, prompt o router se mide contra ese set (acierto de herramienta, argumentos y latencia).

---

## 8. F9: la voz de Luchi (clonación de voz)

Objetivo: que Luchi responda con la voz de mi hija, a partir de grabaciones suyas.

### Lineamientos

- **Todo local.** Grabaciones y modelo se procesan y guardan **solo en esta PC**. Nada se sube a servicios en la nube: una vez subida, la voz de una menor queda fuera de nuestro control.
- **Las grabaciones no van a git.** Carpeta fuera del repo o ignorada (`/voice-data`), con backup cifrado.
- **Solo para este asistente.** El modelo de voz no se comparte ni se publica.
- **Su consentimiento**, de acuerdo a su edad. Que sepa para qué es y que pueda pedir que se borre.

### Enfoque técnico (se evalúa al llegar a F9)

- Motores TTS locales con clonación que corran en la RTX 3080. Revisar **licencia** y calidad en español antes de elegir.
- Grabación: 5–30 minutos de voz limpia, en un lugar silencioso, con frases variadas.
- Va detrás de `TextToSpeechPort`: reemplaza a Piper sin tocar el resto.
- La latencia importa: si el motor clonado es lento, se usa para frases fijas pregeneradas ("Listo", "Abriendo…") y Piper para el resto.

---

## 9. Seguridad y privacidad

| Riesgo | Mitigación |
|---|---|
| Micrófono siempre abierto | El detector corre local; no se graba ni guarda audio antes de "Luchi". Tono e isla visibles mientras escucha |
| El LLM ejecuta algo indebido | Lista blanca, validación de argumentos, nada de terminal |
| Activaciones falsas por la TV | Sensibilidad ajustable, opción de cambiar a "Oye Luchi", silenciar desde la bandeja o por voz ("Luchi, no escuches"). Bajar sensibilidad mientras la tele está encendida (HA sabe su estado) |
| Otros procesos en el WebSocket | Solo `127.0.0.1` y token compartido |
| Token de Home Assistant | Token de larga duración guardado en el Administrador de credenciales de Windows, no en archivos del repo |
| Datos personales en logs | Logs locales, sin audio, con rotación |
| Defender marca el ejecutable sin firma | Para uso personal basta compilarlo; si se distribuye, firmarlo |
| Grabar a otras personas | En muchos lugares hace falta el **consentimiento de todos** los participantes. Luchi lo recuerda en voz al empezar y muestra el indicador de grabación todo el tiempo. Nunca graba sin una orden explícita |
| Cuenta de Google | Opcional. Permiso `drive.appdata` (solo la carpeta de la app). Token en el Administrador de credenciales. Nunca se suben contraseñas, tokens ni historial; grabaciones solo si el usuario lo activa. Cerrar sesión borra el token local |
| Deshacer acciones | Solo se deshace lo reversible; lo que no (por ejemplo, un mensaje ya enviado) se avisa en voz |
| Grabaciones y transcripciones sensibles | Solo en la PC, en una carpeta propia; nunca se suben a ningún lado. Borrar una grabación borra su carpeta completa |

---

## 10. Riesgos técnicos

| Riesgo | Mitigación |
|---|---|
| Calidad de openWakeWord con "Luchi" en español | Spike en F0. Si no alcanza: probar microWakeWord o más muestras reales grabadas. Atajo de teclado siempre disponible |
| Latencia total (voz → acción) | Objetivo < 1,5 s con router y < 2,5 s con LLM. `keep_alive` en Ollama, whisper en memoria, `think: false` |
| VRAM compartida (LLM + whisper + juego) | Medir en F3. Modo juego: descargar el LLM o pasar whisper a CPU mientras hay un juego abierto |
| La isla no se ve sobre juegos en pantalla completa exclusiva | Por eso la respuesta principal es por voz |
| El modelo se equivoca de herramienta | Router para lo frecuente, set de evaluación, y preguntar en voz si es ambiguo |
| Whisper transcribe mal nombres de juegos o películas | Búsqueda aproximada en el catálogo; prompt inicial de whisper con nombres del catálogo y dispositivos |
| Control de la tele limitado por la marca | Se define en el inventario de F0 antes de prometer funciones |
| La PC tiene que estar encendida | Aceptado: todo corre en esta PC por diseño |
| Fuente de IDs de Netflix | Catálogo local; si falta un título, se abre la búsqueda |
| El loopback graba también notificaciones y otros sonidos | Por defecto se acepta; la captura de una sola app se prueba en F6 (posible bug en esta versión de Windows) |
| Transcribir reuniones largas | En segundo plano con la GPU al terminar; si hay un juego abierto, espera o usa la CPU |
| Recordatorios con la PC apagada | No se puede avisar en el momento: se avisa al prender y se ofrece despertar de la suspensión. Queda claro en la pantalla de Recordatorios |
| Verificación de la app en Google | Con un permiso no sensible alcanza la verificación básica; mientras tanto la app funciona en modo de prueba para pocos usuarios |
| "Yo / Otros" no distingue a cada participante | Suficiente para el uso previsto. Identificar a cada persona requeriría modelos extra; se evalúa solo si hace falta |
| Portar el personaje de Python a TypeScript | El prototipo es la especificación ejecutable: tests visuales que comparan el renderer TS con frames exportados del prototipo (diferencia por píxel con tolerancia), más el "laboratorio del personaje" (propuesta 8) para revisarlo a ojo |

---

## 11. Checklist F0

- [ ] Instalar Rust (`rustup`, toolchain MSVC) + Visual Studio Build Tools
- [ ] Instalar Ollama y descargar `qwen3:8b`
- [ ] Instalar `uv` y crear el entorno con Python 3.12
- [ ] Instalar `yt-dlp` y `ffmpeg`
- [ ] Activar Hyper-V e instalar **Home Assistant OS** en una VM (red en modo puente para descubrir dispositivos)
- [ ] **Inventario:** marca y modelo de cada luz, tele, Chromecast/Google TV y parlante; qué expone cada uno en Home Assistant
- [ ] Crear un token de larga duración en Home Assistant
- [ ] **Spike openWakeWord:** generar muestras de "Luchi" y de "Oye Luchi" con Piper en español, entrenar los dos modelos, medir aciertos y falsos positivos por hora de TV de fondo
- [ ] Elegir y descargar una voz de Piper en español
- [ ] `git init` con `.gitignore` que excluya modelos, claves, grabaciones y `voice-data/`

---

## 12. Decisiones registradas

| # | Decisión | Motivo |
|---|---|---|
| D1 | Tauri en lugar de Electron | Menos RAM, deja recursos para la IA local |
| D2 | Ollama local en lugar de API en la nube | Privacidad y costo cero. Cambiable gracias a `LlmPort` |
| D3 | Activación por voz desde el MVP | Requisito del producto |
| D4 | ~~Porcupine~~ → **openWakeWord** | Picovoice cerró su plan gratuito el 30-06-2026; además validaba la clave por internet y las palabras personalizadas gratis vencían a los 30 días |
| D5 | Servicio de voz en Python, separado de la app | Ecosistema de audio e IA más maduro |
| D6 | ~~"Oye Luchi"~~ → **"Luchi"** como palabra de activación, con "Oye Luchi" como alternativa en Ajustes | Pedido del usuario: llamarla solo por su nombre. El riesgo de falsas activaciones se mide en F0 |
| D7 | Clonación de voz solo local | Protección de la voz de una menor |
| D8 | Home Assistant OS en VM de Hyper-V | Soporta casi todas las marcas, Assist en español, instalación recomendada en Windows |
| D9 | Router antes del LLM | Menos latencia y menos errores en las órdenes frecuentes |
| D10 | Respuesta por voz desde F2 | El objetivo es usarlo sin mirar la pantalla |
| D11 | La casa antes que las apps | Es el caso de uso principal y valida toda la cadena temprano |
| D12 | 100 % gratis y 100 % local | Requisito del proyecto. Se descarta cualquier dependencia de pago, nube o API de terceros |
| D13 | El proyecto pasa de "Luz" a **Luchi** (`LuchiAssistant`) | Luz + mochi; no se confunde con "la luz" en las órdenes de la casa |
| D14 | El personaje se dibuja en vivo (Canvas 2D) con capas + parámetros, no con videos | Permite emociones conectadas a datos reales (micrófono, TTS), transiciones sin saltos y personalización sin rehacer animaciones |
| D15 | El diseño visual se cerró antes de programar | El desarrollo se enfoca en la funcionalidad; `docs/PERSONAJE.md` y `assets/luchi/` son la especificación |
| D16 | Grabación en dos pistas (micrófono / sistema) | Separa "Yo / Otros" sin modelos de identificación de voces |
| D17 | Traducción con el LLM local | Sin dependencias nuevas; Argos Translate como alternativa |
| D18 | Los dispositivos se conectan desde la propia app, con Home Assistant por debajo | El usuario no necesita abrir ni entender Home Assistant. Google Home no se puede integrar: sus APIs solo funcionan en apps Android/iOS certificadas y pasan por la nube |
| D19 | Isla = borde negro arriba + Luchi flotando debajo | Mínima y reconocible; cuando Luchi se esconde, el borde también desaparece |
| D20 | Sincronización opcional con Google Drive (`appDataFolder`) y guardado local sin cuenta | Pedido del usuario. Única excepción al 100 % local, opcional y con el permiso más acotado |
| D21 | Recordatorios locales: aviso al prender si vencieron con la PC apagada; despertar de la suspensión opcional | Sin servicios externos no hay forma de avisar con la PC apagada |
| D22 | Correcciones por voz además del botón, con deshacer | Corregir tiene que ser tan fácil como pedir; cada corrección mejora el set de evaluación |
| D23 | SQLite para los datos locales | Un archivo, sin servidor, fácil de respaldar y sincronizar |

---

## 13. Cambios respecto a v1

1. **Porcupine reemplazado por openWakeWord** (D4).
2. **Casa y tele adelantadas** de F6 a F2/F5; Home Assistant en VM de Hyper-V.
3. **Router + Home Assistant Assist** antes del LLM para órdenes frecuentes.
4. **Voz de respuesta (Piper) desde F2**, no en F5: sin ella, las preguntas de aclaración obligan a mirar la pantalla.
5. **Destinos multimedia** (`pc`, `tele_sala`…) y estrategia para Netflix/películas (§6.1).
6. **Control de reproducción** (pausa, volumen, pantalla completa) como parte del núcleo.
7. **Ventana de seguimiento** y conversación de varios turnos (hoy F7).
8. Nuevas fases: **escenas** (hoy F8) y **satélites por habitación** (hoy F10).
9. `qwen3` con thinking desactivado; whisper `large-v3-turbo` como candidato.
10. Set de evaluación con órdenes reales desde F2.
11. Regla **100 % gratis y local** (D12): fuera las APIs en la nube y los servicios de terceros; catálogo local de títulos para Netflix.
12. Personaje mochi, animaciones y diseño de interacción ([docs/PERSONAJE.md](docs/PERSONAJE.md)); portada en `assets/branding/`.
13. Nuevo nombre: **Luchi** / `LuchiAssistant`, con la palabra de activación "Oye Luchi" (D13).

---

## 14. Cambios en v3

1. **Personaje integrado al plan:** §3.5 (cómo se implementa), tabla de dónde está cada pieza del diseño (§1), feature `character/` en la estructura, y cada fase del roadmap dice qué emociones agrega.
2. **Nueva capacidad: grabar, transcribir y traducir reuniones** (§3.6, herramientas en §6, fase **F6**).
3. Las fases siguientes se renumeran: Conversación F7, Escenas F8, Voz de Luchi F9, Toda la casa F10, Pulido F11, Tu Luchi F12.
4. Nuevas decisiones D14–D17, riesgos de grabación y consentimiento en §9 y §10, `ffmpeg` en el checklist de F0.

### Cambios en v3.1

1. Palabra de activación **"Luchi"** (solo el nombre), con "Oye Luchi" como alternativa en Ajustes (D6).
2. Isla definida: **borde negro arriba + Luchi flotando debajo**, que desaparecen juntos (§3.5, D19).
3. **Dispositivos conectados desde la app** con Home Assistant por debajo; Google Home descartado con motivo (§3.4, D18).
4. **Interfaz completa diseñada** (§3.7): prototipo en `mockups/ui/` y especificación en `docs/INTERFAZ.md`.

### Cambios en v3.2

1. *aparecer* y *esconderse* pasan a ser verticales: cae desde el borde como superhéroe y se va saltando hacia arriba.
2. Nueva §3.8: dónde está cada recurso de diseño, cómo entra al desarrollo y qué pantallas se construyen en cada fase.
3. Nueva §15 con propuestas para aprobar.

---

## 15. Funciones aprobadas (v3.3)

Todas las propuestas de v3.2 quedaron aprobadas, con estos ajustes del usuario:

| # | Función | Ajuste | Dónde quedó | Fase |
|---|---|---|---|---|
| 1 | Temporizadores y recordatorios | Aceptado que con la PC apagada no avisa en el momento: se avisa al prender | §3.10 · D21 | F7 |
| 2 | Dictado | — | §3.10 | F7 |
| 3 | Preguntas generales | — | §3.10 | F3 |
| 4 | Acciones del sistema | — | §3.10 · §6 | F4 |
| 5 | Escenas y atajos de voz (pantalla) | — | §3.10 | F8 |
| 6 | Historial | Además del botón, se corrige **por voz**: "Luchi, eso no es lo que quería" / "eso está mal" | §3.10 · D22 | F7 |
| 7 | Estado del sistema | — | §3.10 | F1 |
| 8 | Laboratorio del personaje | — | §3.10 · §3.8 | F1 |
| 9 | Guardar preferencias | **Con cuenta de Google** (Drive) y también **guardado local** sin iniciar sesión | §3.9 · D20 | F12 |
| 10 | Subtítulos accesibles | — | §3.10 | F11 |

Todas tienen su pantalla en el prototipo (`mockups/ui/index.html`) y su especificación en `docs/INTERFAZ.md`.

### Cambios en v3.3

1. Funciones aprobadas incorporadas a la arquitectura (§3.9, §3.10), herramientas (§6), tecnologías (SQLite, Google OAuth + Drive), estructura (`reminders/`, `scenes/`, `history/`, `sync/`, `status/`, `devtools/lab/`), roadmap, seguridad, riesgos y decisiones D20–D23.
2. Prototipo de interfaz ampliado: barra lateral agrupada, pantallas de Recordatorios, Escenas, Historial, Cuenta y sincronización, Estado del sistema y Laboratorio; Accesibilidad, Dictado, Preguntas generales y Acciones del sistema en sus pantallas; nuevas demos de la isla (recordatorio, corrección, dictado, pregunta).
