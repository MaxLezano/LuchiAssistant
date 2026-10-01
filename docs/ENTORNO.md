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
