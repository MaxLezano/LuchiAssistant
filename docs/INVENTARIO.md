# Inventario de la casa

> Relevado con el usuario el 2026-10-01 (F0-07). Define qué puede controlar Luchi y cómo (PLAN.md §3.4, §6.1).
> Las capacidades reales de cada uno se confirman al integrarlos en Home Assistant (F0-08).

## Dispositivos

| Habitación | Dispositivo | Marca / modelo | Conexión hoy | En Home Assistant | Control previsto |
|---|---|---|---|---|---|
| Comedor | **Tele Comedor** | TCL 55" con Google TV ("Smart TV") · `192.168.100.139` | Google Home | `media_player.tele_comedor` (Android TV Remote) + `media_player.tele_comedor_cast` | Local |
| Comedor | **Luz Balcón** | Interruptor Wi-Fi genérico de 3 teclas ("WiFi+Bel 3gang"), tecla 1 | Smart Life (Tuya) | `light.luz_balcon` | Nube de Tuya |
| Comedor | **Luz Comedor** | Mismo interruptor de 3 teclas, tecla 2 | Smart Life (Tuya) | `light.luz_comedor` | Nube de Tuya |
| Habitación de Luz | **Tele de Luz** | TCL 43" con Android TV | Google Home | `media_player.tele_de_luz` (Android TV Remote; no expone Cast) · `192.168.100.134` | Local |
| Habitación de Luz | **Habitación Luz** | Interruptor Wi-Fi genérico de 2 teclas ("WiFi+Bel 2gang"), tecla 1 | Smart Life (Tuya) | `light.habitacion_luz` | Nube de Tuya |
| Habitación de Luz | **Placard Luz** | Mismo interruptor de 2 teclas, tecla 2 | Smart Life (Tuya) | `light.placard_luz` | Nube de Tuya |
| Habitación principal | **Tele Habitación** | TCL 50" con Google TV ("Smart TV Pro") · `192.168.100.8` | Google Home | `media_player.tele_habitacion` (Android TV Remote) + `media_player.tele_habitacion_cast` | Local |
| — | **Cámara** | Cámara IP genérica china | App del fabricante | — | Fuera del alcance actual (posible RTSP/ONVIF local) |

> La tecla 3 del interruptor del comedor no se usa.

## Cómo se controla cada tipo

### Teles TCL (Google TV / Android TV): local

| Integración de HA | Para qué | Local |
|---|---|---|
| **Android TV Remote** | Encender y apagar, teclas del control remoto, volumen y **abrir apps o deep links** (`https://www.netflix.com/watch/<id>`, YouTube) | Sí. Hay que aceptar el código de vinculación que aparece en cada tele |
| **Google Cast** | Mandar videos de YouTube por ID, ver qué se está reproduciendo | Sí |
| DLNA | Reproducir archivos locales | Sí (no hace falta por ahora) |

Con esto se cubre lo de PLAN.md §6.1 para Android/Google TV: encender, abrir Netflix en un título por deep link, YouTube por ID, volumen y pausa.

### Tele Comedor: capacidades medidas (F0-17)

Probado de noche desde Home Assistant con [spikes/casa/probar-tele.ps1](../spikes/casa/probar-tele.ps1) (la tele se silencia al prenderla y queda apagada al final). Los tiempos van desde que se pide la acción hasta que se refleja en HA.

| Acción | Cómo | Resultado |
|---|---|---|
| Encender desde standby | `media_player.turn_on` | ✅ 0,8–1,1 s |
| Apagar | `media_player.turn_off` | ✅ 1,6–2,6 s |
| Silenciar | `media_player.volume_mute` | ✅ 0,3 s |
| Volumen | Solo por pasos (`volume_up/down`); no hay nivel exacto. **No probado** de noche: en Android TV subir o bajar desactiva el silencio | — |
| Pausa / reproducir / anterior / siguiente | `media_player.media_*` | ✅ |
| Teclas del control (Inicio, atrás, flechas…) | `remote.send_command` (`HOME`, `BACK`, `DPAD_*`) | ✅ Inicio en 0,4–0,7 s |
| **YouTube** (abrir o un video exacto) | `play_media` tipo `url` con `https://www.youtube.com/watch?v=<id>` | ✅ 0,5–1,3 s |
| **Netflix** con un título exacto | `play_media` tipo `url` con **`nflx://www.netflix.com/title/<id>`** | ✅ 2,9–3,9 s |
| Netflix con `https://www.netflix.com/...` (`/title/` o `/watch/`) | `play_media` tipo `url` | ❌ abre el diálogo "abrir con…" del sistema |
| Abrir apps por nombre de paquete | `play_media` tipo `app` o `remote.turn_on` con `activity` | ❌ no hace nada en esta tele |
| YouTube por Google Cast | `play_media` tipo `cast` | ❌ error: depende de una API de YouTube en la nube (`get_lounge_token_batch`) que lo rechazó. No conviene igual (sale a internet) |

**Conclusión para F5:** las apps de la tele se abren con **deep links** por Android TV Remote, que es local: `https://www.youtube.com/...` para YouTube y `nflx://www.netflix.com/title/<id>` para Netflix. Cast no se usa para mandar contenido.

### Interruptores Smart Life (Tuya): integración oficial

Se usa la **integración oficial de Tuya** de Home Assistant (D24): se vincula con el código de usuario y el QR de la app Smart Life, y trae todos los dispositivos de la cuenta. Las órdenes pasan por la nube de Tuya (`cloud_push`).

- Cada tecla se convirtió en **luz** con el ayudante oficial *Cambiar tipo de interruptor* (`switch_as_x`), para que Assist entienda "las luces del comedor". Los `switch.*` originales quedan ocultos.
- La tecla 3 del comedor y los selectores de "comportamiento de encendido" no se exponen a Assist.
- "Prendé la luz del comedor" → `action_done` en 656 ms; "apagá la luz del comedor" → 509 ms (con la nube de Tuya).
- Hasta que el estado cambia en HA: prender 1,8–1,9 s, apagar 1,0 s (F0-17).

> Se probó primero Tuya Local (local, comunitaria) y se descartó para el producto (D24). Su carpeta quedó **inactiva** en `config/custom_components/tuya_local` (sin entradas configuradas) y se borra cuando haya acceso a archivos de HA.

### Cámara

No forma parte del roadmap. Si tiene RTSP/ONVIF se puede agregar localmente más adelante.

## Pendiente

- [x] Nombres confirmados por el usuario.
- [x] Tele de Luz detectada y vinculada.
- [x] Interruptores Tuya integrados con la integración oficial.
- [ ] Borrar la carpeta inactiva de Tuya Local en HA.
- [ ] Reservar en el router las IPs de las teles y de la VM de Home Assistant.

## Hallazgos de Assist en español (para el router de F2)

- Entiende "prendé" / "apagá" para encender y apagar.
- **No** entiende "prendida" ni preguntas de estado sobre las teles ("¿está encendida la tele del comedor?"): Luchi lee el estado directo de la API.
- Responde "no conozco ningún dispositivo llamado …" cuando no encuentra el nombre: el router puede usar ese texto para pedir aclaración.
