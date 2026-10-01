<#
.SYNOPSIS
  Verifica que el token guardado en el Administrador de credenciales funcione contra Home Assistant.

.DESCRIPTION
  Lee "Luchi/HomeAssistant", llama a /api/ y /api/config, y muestra versión, ubicación, idioma y
  cantidad de entidades. Nunca imprime el token.
#>
param([string]$Url = "http://homeassistant.local")

$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "credencial.psm1") -Force

$token = Get-LuchiCredencial -Destino "Luchi/HomeAssistant"
if (-not $token) { Write-Error "No hay token guardado. Corré .\guardar-token.ps1"; exit 1 }

$h = @{ Authorization = "Bearer $token" }
$api = Invoke-RestMethod -Uri "$Url/api/" -Headers $h -TimeoutSec 10
$cfg = Invoke-RestMethod -Uri "$Url/api/config" -Headers $h -TimeoutSec 10
$estados = Invoke-RestMethod -Uri "$Url/api/states" -Headers $h -TimeoutSec 10

Write-Host $api.message -ForegroundColor Green
Write-Host "Home Assistant $($cfg.version) · '$($cfg.location_name)' · idioma $($cfg.language) · zona $($cfg.time_zone) · $($estados.Count) entidades"
