# Luchi como producto

> Estado: **visión acordada con el usuario** · 2026-10-01
> Se desarrolla primero para la casa del autor, pero **pensado desde el inicio para comercializarse** y que lo usen muchos usuarios.

## 1. La idea

1. Una **web de presentación** muestra qué hace Luchi (video, demos del personaje, ejemplos de órdenes, preguntas frecuentes, privacidad).
2. Desde la web se **descarga el instalador para Windows** (`.exe` / `.msi`).
3. Se instala **como cualquier app**: siguiente, siguiente, listo. La bienvenida (INTERFAZ.md §4) guía el resto: micrófono, casa y elegir su Luchi.
4. Cada usuario conecta **sus** dispositivos desde la app, sin saber qué es Home Assistant (PLAN.md §3.4, D18).

Por ahora no se cobra. El modelo de negocio se define más adelante y no cambia la arquitectura.

## 2. Requisitos que esto agrega

| Requisito | Qué significa para el desarrollo |
|---|---|
| **Instalar sin conocimientos técnicos** | Nada de terminales, `winget`, `uv` ni Python a mano. El instalador trae o descarga todo lo necesario y lo configura solo |
| **Compatible con la mayor cantidad de casas** | Por defecto se usan las **integraciones oficiales de Home Assistant** de cada marca, aunque usen la nube del fabricante (D24). Lo local es una mejora opcional, no un requisito |
| **No quemar computadoras** | Luchi se adapta al hardware de cada PC (§3): en reposo casi no consume, y libera la GPU cuando no la usa o cuando hay un juego abierto |
| **Windows Home y Pro** | Home no tiene Hyper-V. La casa no puede depender de una VM de Hyper-V para todos (§4) |
| **Actualizaciones** | La app se actualiza sola (actualizador de Tauri) y avisa antes de cambios grandes |
| **Soporte** | Estado del sistema y diagnóstico guiado (ya en el plan) para que el usuario resuelva solo lo común; registros locales que puede compartir si quiere |
| **Licencias** | Revisar que todo lo que se distribuye permita uso comercial (modelos, voces de Piper, LLM, librerías) antes de publicar |

## 3. Perfiles de hardware ("sin quemar computadoras")

La app detecta la PC en la bienvenida y elige un perfil; el usuario lo puede cambiar en Estado del sistema. **Los valores son objetivos a medir**, no promesas: se validan en F11/F13.

| Perfil | PC típica | Voz a texto | LLM | Qué cambia |
|---|---|---|---|---|
| **Completo** | GPU NVIDIA con ≥ 10 GB de VRAM (como la de desarrollo) | faster-whisper `large-v3-turbo` en GPU | `qwen3:8b` en GPU | Todo |
| **Equilibrado** | GPU con 6–8 GB | whisper `small`/`medium` en GPU | modelo de ~4B | Respuestas generales más cortas |
| **Liviano** | Sin GPU dedicada, 16 GB de RAM | whisper `small` en CPU (int8) | modelo chico en CPU, o **sin LLM**: solo router + Home Assistant | Lo frecuente (casa, música, volumen, apps) anda igual; lo raro puede no entenderse |

Reglas para todos los perfiles:

- **En reposo** solo corre el detector de "Luchi" en CPU (objetivo: < 3 % de CPU, sin GPU).
- El LLM y whisper **se descargan de la memoria** tras unos minutos sin uso (`keep_alive`) y se cargan al llamarla.
- **Modo juego automático**: con un juego en pantalla completa se libera la GPU (PLAN.md §10).
- Nunca se usa la GPU al 100 % en segundo plano; las transcripciones largas esperan o van por CPU.

## 4. La casa en PCs de usuarios

Hoy Home Assistant OS corre en una VM de **Hyper-V** (D8). Para un producto masivo eso no alcanza: Windows Home no tiene Hyper-V, y además hay que activar funciones y reiniciar. Opciones a evaluar antes de distribuir (tarea F13):

| Opción | Pros | Contras |
|---|---|---|
| VM con **VirtualBox** (gratis), Home Assistant OS oficial | Funciona en Windows Home; es un método documentado por Home Assistant | Instalar un hipervisor más; consumo de RAM de la VM (2–4 GB) |
| Hyper-V cuando existe (Pro), VirtualBox si no | Lo mejor de cada caso | Dos caminos para mantener |
| **Conectarse a un Home Assistant que el usuario ya tenga** | Cero instalación extra | Solo para usuarios que ya lo tienen |
| Sin casa | Luchi sigue sirviendo para la PC, música, apps y grabaciones | No controla dispositivos |

La bienvenida ofrece "Conectar mi Home Assistant", "Instalar uno nuevo" o "Saltear".

## 5. La web

Sitio estático (sin servidor ni base de datos), con:

- Portada con Luchi animado (los mismos assets de `assets/luchi/`), qué hace y botón **Descargar para Windows**.
- Demos: video de órdenes reales, el personaje y sus emociones, "Tu Luchi" (personalización).
- Privacidad: qué queda en la PC y qué sale a internet (las marcas en la nube, la cuenta de Google opcional).
- Requisitos y perfiles de hardware (§3), preguntas frecuentes y cómo desinstalar.
- Descargas firmadas y verificables (hash), notas de versión.

## 6. Qué cambia en las reglas del proyecto

- **"100 % local"** pasa a significar: la voz, la IA, las grabaciones y los datos personales **nunca salen de la PC**. Los dispositivos de la casa pueden usar la **nube de su fabricante** cuando es la integración oficial de Home Assistant, con aviso al usuario (PLAN.md §3.4, D24).
- **"100 % gratis"** sigue valiendo para las dependencias: nada de APIs pagas ni suscripciones de terceros. Que Luchi se venda algún día no cambia eso.
