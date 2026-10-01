<#
.SYNOPSIS
  Instala (o actualiza) la integración Tuya Local en Home Assistant, sin HACS. Idempotente.

.DESCRIPTION
  1. Instala el add-on oficial "Samba share" y lo limita a la carpeta config y a esta PC, con un usuario
     "luchi" y una contraseña aleatoria guardada en el Administrador de credenciales (Luchi/HomeAssistantSamba).
  2. Descarga la última versión de make-all/tuya-local y copia custom_components\tuya_local a config.
  3. Reinicia Home Assistant y vuelve a apagar Samba.
  La vinculación de cada interruptor se hace después desde Home Assistant con el QR de la app Smart Life.

.EXAMPLE
  .\instalar-tuya-local.ps1
#>
param([string]$Url = "http://homeassistant.local", [string]$Version = "latest")

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
Import-Module (Join-Path $PSScriptRoot "credencial.psm1") -Force
$ws = Join-Path $PSScriptRoot "ha-ws.ps1"

function Paso($t) { Write-Host "`n== $t" -ForegroundColor Cyan }
function Supervisor([string]$Endpoint, [string]$Metodo = "post", $Datos = $null) {
  $cmd = @{ type = "supervisor/api"; endpoint = $Endpoint; method = $Metodo }
  if ($Datos) { $cmd.data = $Datos }
  $tmp = New-TemporaryFile
  try {
    [IO.File]::WriteAllText($tmp, ($cmd | ConvertTo-Json -Depth 10 -Compress))
    $salida = & $ws $tmp.FullName $Url
    $r = $salida | ConvertFrom-Json
    if (-not $r.success) { throw "Supervisor $Endpoint falló: $($r.error | ConvertTo-Json -Compress)" }
    return $r.result
  } finally { Remove-Item $tmp }
}

# --- 1. Samba ---------------------------------------------------------------
Paso "Add-on Samba share"
$info = Supervisor "/addons/core_samba/info" "get"
if (-not $info.version) { Write-Host "Instalando..."; Supervisor "/addons/core_samba/install" | Out-Null }

$pass = Get-LuchiCredencial -Destino "Luchi/HomeAssistantSamba"
if (-not $pass) {
  $bytes = New-Object byte[] 24; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  $pass = [Convert]::ToBase64String($bytes) -replace '[+/=]', 'x'
  Set-LuchiCredencial -Destino "Luchi/HomeAssistantSamba" -Usuario "luchi" -Secreto $pass
}
$miIp = (Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway } | Select-Object -First 1).IPv4Address.IPAddress
$opciones = $info.options
$opciones.username = "luchi"
$opciones.password = $pass
$opciones.enabled_shares = @("config")
$opciones.allow_hosts = @("$miIp/32")
$opciones.apple_compatibility_mode = $false
Supervisor "/addons/core_samba/options" "post" @{ options = $opciones } | Out-Null
Supervisor "/addons/core_samba/start" | Out-Null
Write-Host "Samba activo solo para $miIp, carpeta config."

# --- 2. Tuya Local ----------------------------------------------------------
Paso "Tuya Local"
$rel = if ($Version -eq "latest") { Invoke-RestMethod "https://api.github.com/repos/make-all/tuya-local/releases/latest" }
       else { Invoke-RestMethod "https://api.github.com/repos/make-all/tuya-local/releases/tags/$Version" }
Write-Host "Versión $($rel.tag_name)"
$dir = Join-Path $env:TEMP "tuya-local-$($rel.tag_name)"
if (-not (Test-Path $dir)) {
  $zip = "$dir.zip"
  Invoke-WebRequest -Uri $rel.zipball_url -OutFile $zip -Headers @{ "User-Agent" = "Luchi" }
  Expand-Archive -Path $zip -DestinationPath $dir -Force
}
$origen = Get-ChildItem $dir -Recurse -Directory -Filter "tuya_local" | Where-Object { $_.Parent.Name -eq "custom_components" } | Select-Object -First 1
if (-not $origen) { throw "No encontré custom_components\tuya_local en la descarga." }

$hostHa = ([Uri]$Url).Host
$ip = ([Net.Dns]::GetHostAddresses($hostHa) | Where-Object AddressFamily -eq "InterNetwork" | Select-Object -First 1).IPAddressToString
$recurso = "\\$ip\config"
$listo = $false
for ($i = 0; $i -lt 12 -and -not $listo; $i++) {
  net use $recurso /user:luchi $pass /persistent:no 2>$null | Out-Null
  $listo = $LASTEXITCODE -eq 0
  if (-not $listo) { Start-Sleep 5 }
}
if (-not $listo) { throw "No pude conectarme a $recurso." }
try {
  $destino = Join-Path $recurso "custom_components\tuya_local"
  if (Test-Path $destino) { Remove-Item $destino -Recurse -Force }
  New-Item -ItemType Directory -Force -Path (Split-Path $destino) | Out-Null
  Copy-Item $origen.FullName $destino -Recurse
  $manifest = Get-Content (Join-Path $destino "manifest.json") -Raw | ConvertFrom-Json
  Write-Host "Copiada en $destino (manifest $($manifest.version))."
} finally { net use $recurso /delete /y | Out-Null }

# --- 3. Reinicio y cierre ---------------------------------------------------
Paso "Reinicio"
Supervisor "/addons/core_samba/stop" | Out-Null
Write-Host "Samba apagado."
Supervisor "/core/restart" | Out-Null
Write-Host "Reiniciando Home Assistant..."
$limite = (Get-Date).AddMinutes(5)
Start-Sleep 15
do {
  try { Invoke-WebRequest "$Url/api/" -UseBasicParsing -TimeoutSec 5 | Out-Null } catch {
    if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 401) { break }
  }
  Start-Sleep 5
} while ((Get-Date) -lt $limite)
Write-Host "Listo. Agregá cada interruptor en Ajustes > Dispositivos > Agregar integración > Tuya Local." -ForegroundColor Green
