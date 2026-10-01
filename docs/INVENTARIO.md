# Inventario de la casa

> Relevado con el usuario el 2026-10-01 (F0-07). Define qué puede controlar Luchi y cómo (PLAN.md §3.4, §6.1).
> Las capacidades reales de cada uno se confirman al integrarlos en Home Assistant (F0-08).

## Dispositivos

| Habitación | Dispositivo | Marca / modelo | Conexión hoy | En Home Assistant | Control previsto |
|---|---|---|---|---|---|
| Comedor | **Tele Comedor** | TCL 55" con Google TV ("Smart TV") · `192.168.100.139` | Google Home | Detectada: Google Cast ✅, Android TV Remote (falta vincular) | Local |
| Comedor | **Luz Balcón** | Interruptor Wi-Fi genérico de 3 teclas, tecla 1 | Smart Life (Tuya) | — | Tuya (ver abajo) |
| Comedor | **Luz Comedor** | Mismo interruptor de 3 teclas, tecla 2 | Smart Life (Tuya) | — | Tuya (ver abajo) |
| Habitación de Luz | **Tele de Luz** | TCL 43" con Android TV | Google Home | No detectada todavía (apagada) | Local |
| Habitación de Luz | **Habitación Luz** | Interruptor Wi-Fi genérico de 2 teclas, tecla 1 | Smart Life (Tuya) | — | Tuya (ver abajo) |
| Habitación de Luz | **Placard Luz** | Mismo interruptor de 2 teclas, tecla 2 | Smart Life (Tuya) | — | Tuya (ver abajo) |
| Habitación principal | **Tele Habitación** | TCL 50" con Google TV ("Smart TV Pro") · `192.168.100.8` | Google Home | Detectada: Google Cast ✅, Android TV Remote y DLNA (falta vincular) | Local |
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

### Interruptores Smart Life (Tuya): a decidir en F0-08

Son interruptores Wi-Fi genéricos de Tuya. Opciones:

| Opción | Cómo | Local | Costo / riesgo |
|---|---|---|---|
| **Tuya oficial** (HA) | Se vincula escaneando un QR con la app Smart Life | ❌ Las órdenes pasan por la nube de Tuya (más lento, depende de internet) | Gratis. PLAN.md §3.4 lo permite con aviso |
| **Tuya Local** (custom, HACS) | Control directo por la red con la `local_key` de cada dispositivo | ✅ | Gratis. Para sacar la `local_key` hay que usar una vez una cuenta de desarrollador de Tuya (o una herramienta que la lea de la app); si se re-vincula el dispositivo, la clave cambia |

### Cámara

No forma parte del roadmap. Si tiene RTSP/ONVIF se puede agregar localmente más adelante.

## Pendiente

- [x] Nombres confirmados por el usuario.
- [ ] Prender la **Tele de Luz** para que Home Assistant la detecte (F0-08).
- [ ] Elegir cómo integrar los interruptores Tuya (F0-08).
- [ ] Reservar en el router las IPs de las teles y de la VM de Home Assistant.
