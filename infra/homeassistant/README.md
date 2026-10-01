# Home Assistant OS en Hyper-V

Home Assistant corre en una VM de Hyper-V en esta PC (PLAN.md §4, D8). La VM está en modo puente para quedar en la red de la casa y descubrir dispositivos.

## Requisitos

- Windows 11 Pro con **Hyper-V activado** (`Microsoft-Hyper-V-All`) y reinicio hecho.
- Terminal de PowerShell **como administrador**.

## Crear la VM

```powershell
cd infra\homeassistant
.\crear-vm.ps1                      # HAOS 18.3 en E:\Luchi\vm, 2 vCPU, 4 GB
```

Es idempotente: si se corta o ya existe algo, lo reutiliza y sigue. Al terminar muestra la URL (`http://<ip>:8123`) y la MAC de la VM para reservarle la IP en el router.

| Qué | Valor |
|---|---|
| VM | `HomeAssistant`, Gen2, Secure Boot apagado, memoria fija, sin puntos de control |
| Disco | `E:\Luchi\vm\HomeAssistant\haos_ova-<versión>.vhdx` (no va a git) |
| Red | Switch externo `Luchi-Puente` (o el externo que ya exista) |
| Inicio | Arranca sola con Windows y se apaga ordenadamente con la PC |

> Crear el switch externo corta la red de la PC unos segundos.
