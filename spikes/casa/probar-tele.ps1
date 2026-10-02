<#
.SYNOPSIS
  F0-17: prueba lo que se puede hacer con una tele Android/Google TV y una luz desde Home Assistant.

.DESCRIPTION
  Llama a cada servicio por la API REST y mide cuánto tarda en reflejarse el estado. Primero silencia la
  tele (pruebas de noche) y al final deja todo apagado. No prueba subir/bajar volumen porque en Android TV
  eso desactiva el silencio. Solo toca las entidades que se le pasan.

.EXAMPLE
  .\probar-tele.ps1                                   # Tele Comedor + Luz Comedor
#>
param(
  [string]$Tele = "media_player.tele_comedor",
  [string]$Remoto = "remote.tele_comedor",
  [string]$Luz = "light.luz_comedor",
  [string]$Url = "http://homeassistant.local"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Import-Module (Join-Path $PSScriptRoot "..\..\infra\homeassistant\credencial.psm1") -Force
$h = @{ Authorization = "Bearer " + (Get-LuchiCredencial "Luchi/HomeAssistant") }
$resultados = @()

function Estado($id) { Invoke-RestMethod "$Url/api/states/$id" -Headers $h }
function Servicio($dominio, $servicio, $datos) {
  $b = [Text.Encoding]::UTF8.GetBytes(($datos | ConvertTo-Json -Compress -Depth 5))
  Invoke-RestMethod -Method Post "$Url/api/services/$dominio/$servicio" -Headers $h -ContentType "application/json; charset=utf-8" -Body $b | Out-Null
}
function Paso($nombre, [scriptblock]$accion, [scriptblock]$listo, [int]$limite = 20) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $err = $null
  try { & $accion } catch { $err = $_.Exception.Message; if ($_.ErrorDetails) { $err += " " + $_.ErrorDetails.Message } }
  $ok = $false
  while (-not $err -and $sw.Elapsed.TotalSeconds -lt $limite) {
    try { if (& $listo) { $ok = $true; break } } catch { }
    Start-Sleep -Milliseconds 250
  }
  $ms = [int]$sw.Elapsed.TotalMilliseconds
  $detalle = try { $e = Estado $Remoto; "app: $($e.attributes.current_activity)" } catch { "" }
  $fila = [pscustomobject]@{ paso = $nombre; ok = $ok; ms = $ms; detalle = $(if ($err) { "ERROR $err" } else { $detalle }) }
  $script:resultados += $fila
  "{0,-46} {1,-5} {2,6} ms  {3}" -f $nombre, $(if ($ok) { "OK" } else { "FALLA" }), $ms, $fila.detalle
}
function App($paquete) { (Estado $Remoto).attributes.current_activity -like "$paquete*" }

"== Luz"
Paso "Prender luz" { Servicio light turn_on @{ entity_id = $Luz } } { (Estado $Luz).state -eq "on" }
Paso "Apagar luz" { Servicio light turn_off @{ entity_id = $Luz } } { (Estado $Luz).state -eq "off" }

"== Tele"
Paso "Encender desde standby" { Servicio media_player turn_on @{ entity_id = $Tele } } { (Estado $Tele).state -ne "off" } 30
Paso "Silenciar" { Servicio media_player volume_mute @{ entity_id = $Tele; is_volume_muted = $true } } { (Estado $Tele).attributes.is_volume_muted -eq $true } 8
Start-Sleep 3
# Medido en F0-17 (TCL Google TV): abrir por nombre de paquete no funciona, los links https de Netflix abren el
# diálogo "abrir con…" y Cast + YouTube depende de una API en la nube que falló. Lo que anda son los deep links:
Paso "YouTube (link https)" { Servicio media_player play_media @{ entity_id = $Tele; media_content_type = "url"; media_content_id = "https://www.youtube.com" } } { App "com.google.android.youtube" }
Start-Sleep 3
Paso "YouTube: video exacto (watch?v=ID)" { Servicio media_player play_media @{ entity_id = $Tele; media_content_type = "url"; media_content_id = "https://www.youtube.com/watch?v=rFZHOHl-L8A" } } { App "com.google.android.youtube" }
Start-Sleep 4
Paso "Pausa" { Servicio media_player media_pause @{ entity_id = $Tele } } { $true } 2
Paso "Inicio (tecla HOME)" { Servicio remote send_command @{ entity_id = $Remoto; command = "HOME" } } { App "com.google.android.apps.tv.launcher" } 8
Start-Sleep 2
Paso "Netflix: título exacto (nflx://)" { Servicio media_player play_media @{ entity_id = $Tele; media_content_type = "url"; media_content_id = "nflx://www.netflix.com/title/70305903" } } { App "com.netflix" }
Start-Sleep 5
Paso "Inicio (tecla HOME)" { Servicio remote send_command @{ entity_id = $Remoto; command = "HOME" } } { App "com.google.android.apps.tv.launcher" } 8
Paso "Apagar tele" { Servicio media_player turn_off @{ entity_id = $Tele } } { (Estado $Tele).state -eq "off" } 20

"== Estado final"
"Tele: $((Estado $Tele).state) · Luz: $((Estado $Luz).state)"
$resultados | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $PSScriptRoot "resultado-tele.json")
