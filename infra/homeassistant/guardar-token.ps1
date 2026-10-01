<#
.SYNOPSIS
  Guarda el token de larga duración de Home Assistant en el Administrador de credenciales de Windows.

.DESCRIPTION
  Pide el token sin mostrarlo en pantalla, lo prueba contra la API y lo guarda como credencial genérica
  "Luchi/HomeAssistant". El token nunca se escribe en archivos ni en el repo (PLAN.md §9).
  No necesita permisos de administrador.

.EXAMPLE
  .\guardar-token.ps1
  .\guardar-token.ps1 -Url http://192.168.100.188
#>
param([string]$Url = "http://homeassistant.local")

$ErrorActionPreference = "Stop"
Import-Module (Join-Path $PSScriptRoot "credencial.psm1") -Force

$seguro = Read-Host "Pegá el token de larga duración de Home Assistant" -AsSecureString
$token = [Runtime.InteropServices.Marshal]::PtrToStringUni([Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($seguro))
if (-not $token) { throw "No pegaste ningún token." }

try {
  $r = Invoke-RestMethod -Uri "$Url/api/" -Headers @{ Authorization = "Bearer $token" } -TimeoutSec 10
} catch {
  throw "Home Assistant rechazó el token o no respondió en $Url ($($_.Exception.Message)). No guardé nada."
}

Set-LuchiCredencial -Destino "Luchi/HomeAssistant" -Usuario $Url -Secreto $token
Write-Host "Token válido ($($r.message)) y guardado en el Administrador de credenciales como 'Luchi/HomeAssistant'." -ForegroundColor Green
