# Luchi: interfaz de la app

> Estado: **propuesta para aprobar** · 2026-10-01
> Prototipo navegable: `mockups/ui/index.html` (abrir en el navegador). Enlaces directos: `#isla`, `#bienvenida`, `#general`, `#voz`, `#tuluchi`, `#tuluchi:accesorios`, `#casa`, `#apps`, `#escenas`, `#recordatorios`, `#grabaciones`, `#historial`, `#cuenta`, `#privacidad`, `#estado`, `#acerca`, `#laboratorio`.
> El personaje y sus emociones están en [PERSONAJE.md](PERSONAJE.md).

## 1. Principios

- **La voz manda.** Toda la app se puede usar sin abrir ninguna ventana; las pantallas son para configurar y revisar.
- **Una sola ventana** con barra lateral, más la isla y el menú de la bandeja. Nada de ventanas sueltas.
- **Tema oscuro por defecto**, claro opcional, o el del sistema.
- **Lenguaje simple**, en español rioplatense, sin términos técnicos ("Home Assistant" aparece una sola vez, explicado).
- **Todo local:** cada pantalla que maneja datos personales lo recuerda (grabaciones, privacidad).

### Tokens visuales

| Token | Oscuro | Claro | Uso |
|---|---|---|---|
| Fondo | `#13141b` | `#f3f0ec` | Ventana |
| Superficie | `#1b1d26` | `#fbfaf8` | Tarjetas |
| Superficie 2 / 3 | `#232633` / `#2c3040` | `#f1eee9` / `#e7e2db` | Controles, hover |
| Texto / secundario | `#ece8f0` / `#9a93a8` | `#2f2a31` / `#7d7480` | |
| Acento | `#f0a5b4` (mejillas de Luchi) | igual | Botón principal, selección, interruptores |
| Lavanda | `#b7a6e0` | igual | "Otros" en transcripciones, adornos |
| Peligro / OK | `#e5566b` / `#7fd1a8` | igual | Borrar, estados |

Radios: 16 px tarjetas, 10 px controles, 999 px chips. Tipografía: Segoe UI Variable. Iconos de línea de 1,7 px.

## 2. La isla

| Estado | Qué se ve |
|---|---|
| Oculta | Nada. El borde negro tampoco |
| Llamada ("Luchi") | El borde negro baja desde el borde superior (≈ 300 ms) y Luchi cae desde él como superhéroe (*aparecer*) |
| Escuchando | Luchi *escuchando* + globo con el texto que va entendiendo, en vivo |
| Pensando | Luchi *pensando* + globo "…" (solo si tarda más de 400 ms) |
| Respondiendo | Luchi *hablando* + globo con la respuesta |
| Pregunta | Luchi *pregunta* + globo con las opciones como chips |
| Error | Luchi *apenado* + globo con la explicación |
| Fin | *feliz* o *guiño*, luego *esconderse* (mira a los costados y salta hacia el borde); el borde se va con él |
| Grabando | Solo el borde, más ancho: punto rojo titilando + "Grabando · mm:ss · tocar para detener" |
| Silenciado | Luchi *dormido* unos segundos + globo "Micrófono silenciado"; después se esconde. El icono de la bandeja cambia |
| Modo compañía | Luchi *idle* visible bajo el borde |
| Recordatorio | Luchi aparece, *hablando* + globo "⏰ Recordatorio" con el texto y las opciones "Posponé 5 minutos" / "Listo" |
| Corrección | Tras "eso no es lo que quería": *apenado* + "Perdón. Volví a… ¿Qué querías?" → escucha → hace lo correcto → *feliz* |
| Dictado | Globo "Escribiendo en <app>" con el texto |

Medidas de referencia (pantalla 1440 px de alto): borde 200 × 30 px (250 × 34 px grabando), Luchi ≈ 120 px de ancho, globo hasta 460 px. Tamaño de Luchi ajustable en Ajustes. La ventana de la isla es transparente y deja pasar los clics salvo sobre el borde, Luchi y el globo.

## 3. Bandeja del sistema

Icono: la cara de Luchi (con los ojos cerrados si el micrófono está silenciado). Menú: estado ("Luchi está escuchando · di 'Luchi'"), Ajustes, Tu Luchi, Grabaciones, Dispositivos, Recordatorios, Historial, Estado del sistema, Silenciar / activar micrófono, Dejar a Luchi visible, Salir.

## 3b. Barra lateral

Agrupada en: **Luchi** (General, Voz y micrófono, Tu Luchi) · **Casa y PC** (Casa y dispositivos, Apps y sistema, Escenas y atajos) · **Tus cosas** (Recordatorios, Grabaciones, Historial) · **Cuenta** (Cuenta y sincronización, Privacidad, Estado del sistema, Acerca de) · **Desarrollo** (Laboratorio del personaje; no aparece en la versión para usuarios). Arriba, la miniatura de tu Luchi y su estado.

## 4. Pantallas

### Bienvenida (primer uso)
1. **Hola**: portada y una frase de qué hace.
2. **Micrófono**: elegir dispositivo, medidor de nivel grande, "Ahora decí 'Luchi'" → ✓ Te escuché.
3. **Tu casa**: si no hay Home Assistant, "Instalar y buscar dispositivos" (un clic). Se puede saltear.
4. **¿Cómo querés que sea?**: 6 presets animados; el elegido se guarda.
5. **¡Listo!**: 4 ejemplos de órdenes. Al terminar, Luchi aparece y se presenta.

### Ajustes · General
Iniciar con Windows · Tema (oscuro / claro / sistema) · Idioma de la interfaz · **La isla:** posición (izquierda / centro / derecha), monitor (principal o seguir al mouse), tamaño de Luchi, esconderse después de responder, sonidos cortos, movimiento reducido, ocultar en juegos a pantalla completa · **Accesibilidad:** subtítulos grandes, cuánto quedan visibles, alto contraste en la isla.

### Ajustes · Voz y micrófono
- **Palabra de activación:** tarjetas "Luchi" (recomendada) y "Oye Luchi" (menos activaciones falsas). Sensibilidad con explicación de los dos extremos. "Probar ahora" muestra la detección y la confianza. Atajo de teclado (por defecto Ctrl + Alt + L).
- **Micrófono:** dispositivo, nivel en vivo, silenciar.
- **Voz de Luchi:** voz, velocidad, volumen, "Escuchar un ejemplo".
- **Conversación:** cuánto sigue escuchando después de responder, idioma de las órdenes, responder en voz.
- **Dictado:** escribir en la app activa, confirmar antes de enviar en chats ("y mandalo"), puntuación automática, probar.
- **Preguntas generales:** activar, largo de las respuestas (muy cortas / cortas / detalladas), probar.

### Tu Luchi
- **Vista previa** grande: poses neutral / feliz / hablando, fondo oscuro / claro. En la app es animada en vivo.
- Acciones: **Sorprendeme** (combinación al azar), **Restablecer**, **Guardar**.
- Pestañas, cada opción con su propia miniatura de Luchi con esa opción puesta:
  - **Color** (10) · **Mejillas** (5, incluye sin mejillas) · **Ojos** (6) · **Boca** (6; la nota sugiere las poses feliz/hablando para ver dientes, labios, etc.)
  - **Tatuajes:** patrón de cuerpo completo (7 + ninguno) y diseños chicos: primero se elige la posición (panza derecha, panza izquierda, frente, costado) y después el diseño (19, con etiqueta código / clásico / japonés, o "quitar"). Máximo 3: si se intenta un cuarto, aviso.
  - **Accesorios:** filtro Todos / Diario / Divertidos / De temporada (23 + ninguno; los de temporada muestran su fecha). Opciones: accesorios de temporada automáticos (no reemplazan uno elegido), hemisferio, fecha de cumpleaños.
  - **Presets** (9).

### Casa y dispositivos
- Tarjeta de estado: Home Assistant conectado, dónde corre, cantidad de dispositivos y habitaciones, botón **Agregar dispositivo**.
- **Encontrados en tu red**, con "Agregar".
- **Tus dispositivos** por habitación: icono, nombre, estado, marca, apodos como chips (+ alias), interruptor.
- Video por defecto (esta PC o una tele) · Abrir Home Assistant (avanzado).
- **Asistente de agregar:** marca (buscador + grilla; cada marca dice si es local o por nube) → conectar (instrucción según la marca: botón del puente, aceptar en la tele, código, o usuario y contraseña; aviso si usa la nube) → nombre, habitación y apodos → "¡Listo! Probalo: 'Luchi, prendé la luz del escritorio'".

### Apps y sistema
Fuentes detectadas con cantidad (Menú Inicio, Steam, Epic Games, Riot, Battle.net, EA, Ubisoft Connect, Google Play Games) · buscador · Volver a escanear · lista con fuente, apodos y permiso para abrir. Nota: cerrar siempre es normal, nunca forzado. **Acciones del sistema:** salida de audio (con los dispositivos disponibles), capturas de pantalla, carpetas favoritas con apodos, bloquear la PC, suspender o apagar (siempre con confirmación en voz).

### Escenas y atajos de voz
- Lista: nombre, frase ("Luchi, modo stream"), cantidad de acciones, Probar, Editar; Nueva escena.
- Editor: frase disparadora grande (se pueden sumar otras frases), acciones numeradas con subir/bajar/borrar, botones para agregar: dispositivo de la casa, abrir o cerrar app, volumen o salida de audio, reproducir algo, esperar, que Luchi diga algo. Probar y Guardar.
- Horarios por escena (opcional).

### Recordatorios
- Aviso destacado si **venció algo con la PC apagada** (Ya está / Posponer).
- Próximos: temporizadores y recordatorios con su hora y repetición; Editar, Borrar; Nuevo recordatorio; "Ver cómo avisa".
- Ajustes: despertar la PC de la suspensión, contarme lo vencido al prender, sonido del aviso, posponer por defecto.
- Nota clara de que con la PC apagada no puede avisar en el momento.

### Historial
- Buscador y filtro (Todo / Con errores / Corregidos).
- Cada orden: hora, lo que dijiste, lo que entendió e hizo, y **"Esto estuvo mal"** (o la etiqueta Error / Corregido).
- Nota de la corrección por voz ("Luchi, eso no es lo que quería" / "eso está mal") con demo.
- Guardar historial (7 días / 30 días / no guardar), borrar.

### Cuenta y sincronización
- Sin sesión: "Guardá tus preferencias en tu cuenta de Google" + botón **Iniciar sesión con Google**. Con sesión: cuenta, última sincronización, Sincronizar ahora, Cerrar sesión.
- Qué se sincroniza: diseño de Tu Luchi, ajustes, apodos, escenas y recordatorios (activados); grabaciones y transcripciones (desactivado).
- Explicación de la carpeta oculta de la app en Drive y de lo que nunca se sube.
- Copia local: exportar / importar `.luchi`, copia automática semanal.

### Estado del sistema
Tarjetas por servicio (micrófono, detector, voz a texto, LLM, voz de Luchi, Home Assistant, dispositivos con problemas, GPU con uso de VRAM por componente) · Diagnóstico guiado (pasos concretos para lo que falla) · Reiniciar servicios · Abrir registros · Modo juego automático · Latencia de la última orden.

### Laboratorio del personaje (solo desarrollo)
Vista grande con selector Prototipo / Renderer de la app / Diferencia · botones por emoción (las 16) · deslizadores de parámetros de expresión y del cuerpo · copiar como JSON, restablecer, pausa, cuadro a cuadro · abrir el editor de estilo · simular datos en vivo · resultado de los tests visuales.

### Grabaciones
- Lista: título, fecha, duración, idioma detectado.
- Detalle: reproductor con forma de onda, transcripción con marca de tiempo y "Yo / Otros" en colores distintos, **Ver en** (original o traducida: al elegir un idioma se traduce con el modelo local y se guarda como `transcripcion.<idioma>.txt`), Resumen, Abrir carpeta, Borrar.
- Ajustes: carpeta, qué se graba (micrófono + sistema / solo micrófono / una sola app, experimental), recordatorio de consentimiento, transcribir al terminar, idioma de traducción por defecto.

### Privacidad
Silenciar micrófono · historial de órdenes (7 días / 30 días / no guardar; nunca audio) · borrar historial · registros técnicos. Nota de que el detector no graba nada antes de escuchar "Luchi".

### Acerca de
Portada, versión, "100 % local y 100 % gratis", tecnologías usadas.

## 5. Pendiente de aprobación

- [ ] Isla (borde + Luchi + globo) y sus estados
- [ ] Menú de la bandeja
- [ ] Bienvenida
- [ ] Ajustes, Tu Luchi, Casa y dispositivos, Apps y sistema, Grabaciones, Privacidad
- [ ] Escenas, Recordatorios, Historial, Cuenta y sincronización, Estado del sistema, Laboratorio
