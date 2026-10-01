<#
.SYNOPSIS
  Ejecuta comandos de la API WebSocket de Home Assistant con el token del Administrador de credenciales.

.EXAMPLE
  .\ha-ws.ps1 comandos.json
  .\ha-ws.ps1 '{"type":"get_config"}'
#>
param([Parameter(Mandatory)][string]$Comandos, [string]$Url = "http://homeassistant.local")

Import-Module (Join-Path $PSScriptRoot "credencial.psm1") -Force
$env:LUCHI_HA_TOKEN = Get-LuchiCredencial -Destino "Luchi/HomeAssistant"
if (-not $env:LUCHI_HA_TOKEN) { Write-Error "No hay token guardado. Corré .\guardar-token.ps1"; exit 1 }
# Windows PowerShell 5.1 les saca las comillas a los argumentos de programas nativos: el JSON siempre viaja por archivo.
$tmp = $null
if (Test-Path $Comandos) { $arg = "@" + (Resolve-Path $Comandos) }
else { $tmp = New-TemporaryFile; [IO.File]::WriteAllText($tmp, $Comandos); $arg = "@$tmp" }
try { node (Join-Path $PSScriptRoot "ha-ws.mjs") $arg $Url; exit $LASTEXITCODE }
finally { Remove-Item Env:LUCHI_HA_TOKEN; if ($tmp) { Remove-Item $tmp } }
