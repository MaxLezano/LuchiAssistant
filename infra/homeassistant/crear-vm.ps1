#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Crea (o completa) la VM de Home Assistant OS en Hyper-V. Idempotente: se puede correr varias veces.

.DESCRIPTION
  1. Switch externo en modo puente sobre la placa de red con salida a internet (la VM queda en la red de la casa
     para descubrir dispositivos). Si ya existe un switch externo, lo reutiliza.
  2. Descarga y descomprime el VHDX oficial de HAOS (GitHub de home-assistant/operating-system).
  3. Crea la VM Gen2 sin Secure Boot, con memoria fija, inicio automático con Windows y sin puntos de control.
  4. La arranca y espera a que Home Assistant responda en el puerto 8123.

.EXAMPLE
  .\crear-vm.ps1
  .\crear-vm.ps1 -Version 18.3 -Raiz E:\Luchi\vm -MemoriaGB 4 -Cpus 2
#>
param(
  [string]$Version = "18.3",
  [string]$Raiz = "E:\Luchi\vm",
  [string]$Nombre = "HomeAssistant",
  [string]$Switch = "Luchi-Puente",
  [int]$MemoriaGB = 4,
  [int]$Cpus = 2,
  [int]$EsperaMinutos = 15
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # Invoke-WebRequest es mucho más rápido sin barra de progreso

function Paso($texto) { Write-Host "`n== $texto" -ForegroundColor Cyan }

# --- 1. Switch externo ------------------------------------------------------
Paso "Switch de red"
$externo = Get-VMSwitch -SwitchType External -ErrorAction SilentlyContinue | Select-Object -First 1
if ($externo) {
  $Switch = $externo.Name
  Write-Host "Uso el switch externo existente: $Switch"
} else {
  $placa = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq "Up" } |
    Select-Object -First 1 -ExpandProperty NetAdapter
  if (-not $placa) { throw "No encontré una placa de red conectada con puerta de enlace." }
  Write-Host "Creo '$Switch' sobre '$($placa.Name)'. La red de la PC se corta unos segundos."
  New-VMSwitch -Name $Switch -NetAdapterName $placa.Name -AllowManagementOS $true | Out-Null
}

# --- 2. Disco de HAOS -------------------------------------------------------
Paso "Disco de Home Assistant OS $Version"
$dir = Join-Path $Raiz $Nombre
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$vhdx = Join-Path $dir "haos_ova-$Version.vhdx"
if (Test-Path $vhdx) {
  Write-Host "Ya está: $vhdx"
} else {
  $zip = Join-Path $Raiz "haos_ova-$Version.vhdx.zip"
  if (-not (Test-Path $zip)) {
    $url = "https://github.com/home-assistant/operating-system/releases/download/$Version/haos_ova-$Version.vhdx.zip"
    Write-Host "Descargo $url"
    Invoke-WebRequest -Uri $url -OutFile "$zip.part"
    Move-Item "$zip.part" $zip
  }
  Write-Host "Descomprimo en $dir"
  Expand-Archive -Path $zip -DestinationPath $dir -Force
  if (-not (Test-Path $vhdx)) { throw "El zip no tenía $vhdx" }
}

# --- 3. VM ------------------------------------------------------------------
Paso "Máquina virtual '$Nombre'"
$vm = Get-VM -Name $Nombre -ErrorAction SilentlyContinue
if ($vm) {
  Write-Host "Ya existe (estado: $($vm.State))."
} else {
  $vm = New-VM -Name $Nombre -Generation 2 -MemoryStartupBytes ($MemoriaGB * 1GB) -VHDPath $vhdx `
               -SwitchName $Switch -Path $Raiz
  Set-VMFirmware -VM $vm -EnableSecureBoot Off
  Set-VMProcessor -VM $vm -Count $Cpus
  Set-VMMemory -VM $vm -DynamicMemoryEnabled $false
  Set-VM -VM $vm -AutomaticStartAction Start -AutomaticStartDelay 10 -AutomaticStopAction ShutDown `
         -CheckpointType Disabled -Notes "Home Assistant OS para Luchi (infra/homeassistant/crear-vm.ps1)"
  Write-Host "Creada: Gen2, $Cpus vCPU, $MemoriaGB GB fijos, Secure Boot apagado, inicio automático."
}

# --- 4. Arranque y espera ---------------------------------------------------
Paso "Arranque"
if ($vm.State -ne "Running") { Start-VM -VM $vm; Write-Host "VM iniciada." }

$limite = (Get-Date).AddMinutes($EsperaMinutos)
$ip = $null
while ((Get-Date) -lt $limite) {
  $ip = (Get-VMNetworkAdapter -VM $vm).IPAddresses | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' } | Select-Object -First 1
  if ($ip) {
    try {
      $r = Invoke-WebRequest -Uri "http://${ip}:8123" -UseBasicParsing -TimeoutSec 5
      if ($r.StatusCode -eq 200) { break }
    } catch { }
  }
  Start-Sleep -Seconds 10
}

if ($ip) {
  Write-Host "`nHome Assistant: http://${ip}:8123  (también http://homeassistant.local:8123)" -ForegroundColor Green
  $mac = (Get-VMNetworkAdapter -VM $vm).MacAddress -replace '(..)(?!$)', '$1:'
  Write-Host "MAC de la VM: $mac (para reservarle la IP en el router)"
} else {
  Write-Warning "La VM arrancó pero no respondió en $EsperaMinutos minutos. El primer arranque puede tardar más: probá http://homeassistant.local:8123"
}
