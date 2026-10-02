# Luchi — Asistente de voz para Windows

Asistente de voz que corre **100 % local** como app de Windows. Se despierta al decir **"Luchi"** y controla la PC, la tele y las luces de la casa sin tocar teclado ni mouse; además graba, transcribe y traduce reuniones. Tiene un personaje propio (un mochi animado y personalizable) que vive en una "isla" arriba de la pantalla. **Luchi** = Luz (en honor a la hija del autor) + mochi.

## Estado

- **Diseño terminado y aprobado** (2026-10-01): plan, arquitectura, personaje (16 animaciones, catálogo de personalización, assets de producción) e interfaz completa (prototipo navegable).
- **Siguiente paso: construir la app empezando por la F0** del roadmap.

## Fuentes de verdad (leer antes de programar)

| Documento | Qué define |
|---|---|
| [PLAN.md](PLAN.md) | Arquitectura, tecnologías, estructura del proyecto, herramientas del agente, **roadmap por fases (F0–F12)**, seguridad, riesgos, decisiones (D1–D23), funciones aprobadas (§15) |
| [docs/PERSONAJE.md](docs/PERSONAJE.md) | Personaje, mapa estado de la app → emoción, reglas de interacción, personalización |
| [docs/INTERFAZ.md](docs/INTERFAZ.md) | Cada pantalla, tokens visuales, estados de la isla, bandeja, barra lateral |
| [assets/luchi/README.md](assets/luchi/README.md) | Capas del personaje, `catalogo.json` y **orden de composición** |
| [docs/PRODUCTO.md](docs/PRODUCTO.md) | Luchi como producto: web, instalador, perfiles de hardware, Windows Home |
| [docs/LICENCIAS.md](docs/LICENCIAS.md) | Licencia y veredicto de cada dependencia, modelo y dataset; qué se desarrolla propio |

Referencias visuales (abrir en el navegador):
- `mockups/animaciones/visor.html`: las 16 emociones, catálogo de personalización y presets.
- `mockups/ui/index.html`: prototipo de toda la interfaz (isla, bandeja, ventana). Enlaces directos: `#isla`, `#tuluchi`, `#casa`, `#grabaciones`, `#escenas`, `#recordatorios`, `#historial`, `#cuenta`, `#estado`, `#laboratorio`…

En los documentos, `§` significa "sección" (por ejemplo, §3.5 = sección 3.5).

## Reglas del proyecto

1. **100 % gratis y 100 % local.** Nada de suscripciones, claves pagas, "free tiers", servicios en la nube ni APIs de terceros. La voz, la IA, las grabaciones y los datos personales nunca salen de la PC. Lo único que sale a internet es lo que el usuario pide (abrir YouTube, Netflix, una búsqueda). **Excepciones:** (a) opcional, "Iniciar sesión con Google" para guardar preferencias en la carpeta oculta de la app en Drive (`drive.appdata`); sin sesión todo funciona y se guarda en la PC (PLAN.md §3.9); (b) los dispositivos de la casa pueden usar la nube de su fabricante cuando es la **integración oficial de Home Assistant**, con aviso al usuario (D24). No extender las excepciones a otros servicios sin preguntar.
2. **Solo voz.** Todo se tiene que poder hacer sin mirar la pantalla; lo importante siempre se dice también en voz.
3. **El LLM interpreta, el código ejecuta.** El modelo solo elige herramienta y argumentos de una **lista blanca**. Nunca terminal, nunca borrar archivos, nunca instalar software. Suspender/apagar siempre con confirmación en voz.
4. **Privacidad:** no se graba ni guarda audio antes de detectar "Luchi"; la isla está visible mientras escucha; grabar reuniones solo por orden explícita, con recordatorio de consentimiento e indicador visible; tokens en el Administrador de credenciales de Windows.
5. **Rápido para lo frecuente:** router sin LLM para órdenes comunes (casa vía Home Assistant Assist, "pausa", volumen); el LLM es el fallback.
6. **Es un producto.** Luchi se va a distribuir con una web y un instalador para Windows ([docs/PRODUCTO.md](docs/PRODUCTO.md)): pensar cada decisión para usuarios sin conocimientos técnicos, en Windows Home y Pro, y con hardware más modesto que el de desarrollo.
7. **Desarrollo propio primero (D28).** Lo de terceros solo si es open source y su licencia permite vender (MIT, BSD, Apache, CC0, CC BY…). Nada GPL/AGPL en lo que se distribuye ni datos/modelos no comerciales. Antes de agregar una dependencia, un modelo o un dataset, verificar la licencia y anotarla en [docs/LICENCIAS.md](docs/LICENCIAS.md).

## Arquitectura y stack

- **Screaming architecture por features, hexagonal dentro de cada una** (domain / ports / application / adapters). UI con **container/presentational** y **atomic design**. Estructura completa en PLAN.md §5.
- `apps/desktop`: **Tauri 2** + TypeScript + Vite (UI, isla, agente) y Rust (ejecutor de acciones, catálogo de apps, sistema, bandeja).
- `services/voice` (`luchi-voice`): **Python 3.12 con uv** (no la 3.14 instalada en la PC). detector propio de "Luchi" y "Oye Luchi" (D29), Silero VAD, faster-whisper en GPU, TTS con modelos tipo Piper en onnxruntime y fonemizador propio (D30), grabación con PyAudioWPatch (WASAPI loopback) + ffmpeg. Se comunica con la app por WebSocket en `127.0.0.1` con token.
- **Ollama** con `qwen3:8b` y `think: false`. **Home Assistant OS** en una VM de Hyper-V. **SQLite** para datos locales.
- Tests desde el inicio: **Vitest**, **cargo test**, **pytest**. El dominio se prueba sin micrófono ni IA.

## Personaje e interfaz: cómo implementarlos

- Luchi se **dibuja en vivo** (Canvas 2D) componiendo las capas de `assets/luchi/` en el orden de su README; **no** se usan videos ni secuencias de frames.
- El prototipo en Python es la **especificación ejecutable**: `mockups/animaciones/luchi.py` (renderer y estilos), `tatuajes.py`, `accesorios.py`, `animaciones.py` (líneas de tiempo). **Portarlo 1:1 a TypeScript** (mismos parámetros y tiempos), no rediseñarlo.
- Reglas visuales que no se negocian: **nunca dos expresiones a la vez** (la boca es un contorno que se transforma; los ojos cambian con corte limpio al ser una rendija; nada de fundidos con transparencia), **sin fondo** (solo sombra), 30 fps, transiciones de al menos 4–5 cuadros.
- *escuchando* sigue el nivel real del micrófono; *hablando* mueve la boca con la amplitud del TTS. Feedback < 150 ms al detectar "Luchi"; *pensando* solo si tarda > 400 ms.
- **Isla:** borde negro arriba al centro + Luchi flotando debajo; desaparecen juntos. *aparecer* = cae desde el borde como superhéroe; *esconderse* = mira a los costados y salta hacia arriba.
- **Interfaz:** los tokens de `mockups/ui/ui.css` pasan a `apps/desktop/src/shared/design/tokens.css`; los controles del prototipo pasan a componentes presentacionales; los textos se reutilizan tal cual (español rioplatense, de "vos").
- Tests visuales: comparar el renderer TS con frames del prototipo (`python generar.py <emoción> --frames`) con tolerancia.
- `assets/luchi/` **no se edita a mano**: se regenera desde el prototipo.

## Forma de trabajar

1. **Fase por fase** según PLAN.md §7. Al terminar cada una, mostrar que funciona según su criterio "Cuándo está lista" y **esperar aprobación** antes de seguir.
2. **Pedir OK antes de** instalar software, activar funciones de Windows (Hyper-V, tareas programadas) o tocar algo fuera del repo.
3. Lo que depende del usuario (hablarle al micrófono, inventario de dispositivos de la casa, aceptar avisos en la tele) **se le pide y se espera**.
4. Si algo del plan no es posible o hay una opción mejor, **explicarlo con evidencia** antes de cambiarlo, y registrar la decisión en PLAN.md §12.
5. El usuario evalúa mirando: cuando algo visual cambia, mostrar capturas o el resultado corriendo.
6. **Git:** commits chicos con conventional commits. **Sin "Co-Authored-By" ni atribución de IA.**
7. Responder siempre en **español**.

## Entorno

Windows 11 Pro (build 26300) · AMD Ryzen 7 5800X · 32 GB RAM · **RTX 3080 12 GB** · discos D: y E: para modelos y la VM · Node 24 · Python 3.14 instalada (usar 3.12 vía uv) · ComfyUI Desktop instalado (puerto 8188).

Ojo: hay reportes de que la captura de audio de **una sola app** (process loopback) graba silencio en el build 26200 de Windows 11; por defecto se graba todo el audio del sistema y lo de una app se prueba en un spike (PLAN.md §3.6).

## Comandos útiles

```bash
# Regenerar animaciones, catálogo, presets y assets de producción (requiere Pillow)
cd mockups/animaciones && python generar.py            # todo
python generar.py assets                               # solo assets/luchi + catalogo.json
python generar.py enojado --frames                     # una emoción + frames PNG para tests visuales

# Piezas y datos del prototipo de interfaz
cd mockups/ui && python generar_piezas.py
```
