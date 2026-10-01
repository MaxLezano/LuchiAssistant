# Luchi

![Luchi](assets/branding/luchi_portada.png)

Asistente de voz para Windows que corre **100 % local y 100 % gratis**. Se despierta al decir **"Luchi"** y controla la PC, la tele y las luces de la casa sin tocar teclado ni mouse; además graba, transcribe y traduce reuniones. Luchi es un mochi animado y personalizable que vive en una "isla" arriba de la pantalla.

**Luchi** = Luz + mochi.

## Estado

Diseño terminado. En construcción, fase por fase: ver el [backlog](BACKLOG.md) y los [issues](https://github.com/MaxLezano/LuchiAssistant/issues).

## Documentación

| Documento | Qué define |
|---|---|
| [PLAN.md](PLAN.md) | Arquitectura, tecnologías, estructura, roadmap (F0–F12), seguridad y decisiones |
| [docs/PERSONAJE.md](docs/PERSONAJE.md) | Personaje, emociones e interacción |
| [docs/INTERFAZ.md](docs/INTERFAZ.md) | Pantallas, isla, bandeja y tokens visuales |
| [assets/luchi/README.md](assets/luchi/README.md) | Capas del personaje y orden de composición |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo se trabaja: ramas, commits y PRs |

Referencias visuales: `mockups/animaciones/visor.html` y `mockups/ui/index.html` (abrir en el navegador).

## Stack

Tauri 2 + TypeScript + Rust (app) · Python 3.12 con uv (`luchi-voice`: openWakeWord, Silero VAD, faster-whisper, Piper) · Ollama (`qwen3:8b`) · Home Assistant OS en Hyper-V · SQLite.
