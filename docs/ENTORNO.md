# Entorno de desarrollo

Qué está instalado en la PC de desarrollo, con qué versión y cómo se verificó. Se actualiza en cada tarea de F0.

## Compilación

| Herramienta | Versión | Instalación | Verificación |
|---|---|---|---|
| Visual Studio Build Tools 2022 | 17.14.23 · MSVC 14.44.35207 · Windows SDK 10.0.26100 | `winget install Microsoft.VisualStudio.2022.BuildTools` con la carga `VCTools` (ver abajo) | `vswhere -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64` |
| rustup | 1.29.1 | `winget install Rustlang.Rustup` | `rustup show active-toolchain` |
| Rust | 1.99.0 · `stable-x86_64-pc-windows-msvc` | `rustup default stable-x86_64-pc-windows-msvc` | `cargo new` + `cargo test` pasa y `cargo run` enlaza con MSVC |

Instalar Build Tools (en una terminal de administrador para evitar el aviso de UAC):

```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools --source winget --override "--passive --wait --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --add Microsoft.VisualStudio.Component.Windows11SDK.26100"
```

> Si una instalación anterior se canceló, queda una instancia incompleta y `install` falla con "ya se ha instalado" (código 1). Se completa con:
> `setup.exe modify --installPath "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools" --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --passive --norestart`

## Ollama

| Qué | Valor |
|---|---|
| Versión | 0.35.0 (`winget install Ollama.Ollama`), arranca con Windows desde su app de la bandeja |
| Modelos | `E:\Luchi\models\ollama` (variable de usuario `OLLAMA_MODELS`) |
| Nube | **Desactivada** (`OLLAMA_NO_CLOUD=1`; el log dice `cloud disabled: true`). Regla 100 % local |
| Escucha | `127.0.0.1:11434` |
| Modelo | `qwen3:8b` (5,2 GB en disco, 5,6 GB en memoria con contexto 4096, **100 % GPU**) |

Prueba de tool calling con `think: false` y temperatura 0 ([spikes/ollama](../spikes/ollama/)):

| Medición | Resultado |
|---|---|
| Aciertos de herramienta y argumentos | 4/4 (`play_media` YouTube y Netflix con destino tele, `set_volume`, `launch_app`) |
| Latencia en caliente | 220–395 ms |
| Latencia en frío (modelo descargado de la GPU) | ≈ 3 s; la **primera carga** después de descargar el modelo tardó 60 s |
| VRAM del modelo | ≈ 5,5 GB |

> **Ojo con la VRAM:** con ComfyUI abierto, el escritorio y las apps ya usan ≈ 6,2 GB de los 12 GB, y con el LLM cargado quedan ≈ 0,6 GB libres: no entra faster-whisper. Mientras se use Luchi hay que cerrar ComfyUI (o liberar su VRAM). Se tiene en cuenta para el modo juego y el riesgo de VRAM compartida (PLAN.md §10, F3).
