# Luchi: personaje, emociones e interacción

> Estado: **propuesta para aprobar** · 2026-10-01
> Previews en `mockups/animaciones/` (abrir `visor.html`).

## 1. Qué rol cumple el personaje

Luchi se usa **por voz y muchas veces sin mirar la pantalla**. El personaje no es decoración: es el **canal de feedback** que confirma, de un vistazo y desde lejos, en qué estado está el asistente. Por eso:

- **El movimiento comunica más que el detalle.** Cada estado tiene una silueta de movimiento distinta (late, se balancea, salta, se inclina), reconocible aunque la cara se vea chica.
- **La voz manda.** Toda información importante también se dice en voz alta. La animación nunca es la única pista.
- **Aparece cuando la llamas y se va sola.** No vive fija en pantalla molestando.

## 2. Dónde vive

- **Isla flotante** arriba al centro del escritorio, **sin fondo**: el cuerpo blanco con una sombra suave que se lee sobre fondos claros y oscuros.
- Tamaño: **96 px de alto** en la isla (≈ 1/10 de la pantalla en una TV a 3 m). Las expresiones se validan a ese tamaño (ver toggle en el visor).
- **No bloquea clics** (click-through) salvo al pasar el mouse.
- **En juegos a pantalla completa no aparece**: solo responde por voz.

## 3. Mapa de estados → emociones

| Estado de la app | Emoción | Tipo | Disparador | Sale cuando |
|---|---|---|---|---|
| Oculto | — | — | Arranque, fin de una orden | Se detecta "Luchi" |
| Aparece | **aparecer** | Una vez (≈ 1,3 s) | "Luchi" con la isla oculta: cae desde el borde superior como superhéroe (estirado, con ráfagas de viento), impacta con onda expansiva, líneas de impacto y polvo, se queda agachado con cara decidida y se levanta | Encadena a *atento* |
| Palabra detectada | **atento** | Una vez (≈ 0,6 s) | Detección del wake word | Encadena a *escuchando* |
| Escuchando la orden | **escuchando** | Loop | Tras *atento* | Fin de frase (VAD) o 5 s de silencio |
| Procesando | **pensando** | Loop | Solo si tarda **> 400 ms** (evita parpadeos) | Hay resultado |
| Respondiendo en voz | **hablando** | Loop | Mientras suena el TTS | Termina el audio |
| Acción hecha | **feliz** (a veces **guiño**) | Una vez | Acción ejecutada OK | Se esconde a los 1,5 s |
| Necesita aclarar | **pregunta** | Loop | Orden ambigua o confirmación ("¿cuál de los dos?") | Respuesta del usuario |
| Error / no entendí | **apenado** | Una vez | Fallo, dispositivo no disponible, no entendió | Se esconde tras explicarlo en voz |
| Micrófono silenciado | **dormido** | Loop | "Luchi, no escuches" o botón de la bandeja | Se reactiva el micrófono |
| Agradecimiento | **amor** | Una vez | "Gracias, Luchi", "te quiero" | Se esconde |
| Tarde a la noche | **cansado** | Una vez (≈ 4 s) | Primera orden después de medianoche. Reemplaza a *feliz* **al final**; nunca retrasa la escucha | Se esconde |
| Muchas órdenes a la vez | **mareado** | Una vez (≈ 2 s) | 3 o más órdenes en pocos segundos, o una nueva mientras ejecuta otra | "¡Una a la vez!" en voz y sigue con la cola |
| Le dicen algo feo | **enojado** | Una vez (≈ 2,5 s) | Insulto o "Luchi, enojate". Easter egg | Se le pasa solo y vuelve a neutral |
| Modo compañía *(opcional)* | **idle** | Loop | El usuario activa "dejar a Luchi visible" | Se desactiva |
| Grabando una reunión | Isla compacta: punto rojo + tiempo | Fijo | "Grabá esta reunión" | "Dejá de grabar" → *feliz* al guardar |
| Fin de la interacción | **esconderse** | Una vez (≈ 2,6 s) | Termina la orden: mira a todos lados con sospecha (gota de sudor), se agacha y salta hacia arriba hasta desaparecer, dejando una bocanada de humo | Oculto |

> *Enojado* **nunca** se usa como respuesta a un error del usuario ni de Luchi: es solo un juego. Los errores siempre son *apenado*.

Secuencia típica: `oculto → aparecer → atento → escuchando → (pensando) → hablando → feliz → esconderse → oculto`.

## 4. Reglas de interacción

1. **Feedback inmediato.** Entre la detección de "Luchi" y el primer frame de *atento*: **< 150 ms**. Es la señal de que te escuchó.
2. **Escuchando reacciona a tu voz.** En la app, las ondas y el pulso del cuerpo siguen el **nivel real del micrófono**. Si no ves moverse las ondas, no te está oyendo.
3. **Hablando sigue el audio.** La boca se abre según la amplitud del TTS (no es un loop fijo).
4. **Nunca dos expresiones a la vez.** Las bocas se transforman (morph de la forma); los ojos cambian con un corte limpio cuando son una rendija. Nada de fundidos con transparencia.
5. **Siempre se vuelve a neutral** antes de cambiar a otra emoción fuerte (por ejemplo, de *feliz* a *pregunta*), en 150–250 ms.
6. **Sin parpadeos de estado.** Un estado dura al menos 300 ms en pantalla; *pensando* solo aparece si el proceso tarda más de 400 ms.
7. **Variedad sin ambigüedad.** El éxito alterna *feliz* (90 %) y *guiño* (10 %) para no aburrir, pero ambos significan lo mismo. Las demás emociones tienen un único significado.
8. **El error no dramatiza.** *Apenado* es breve y suave; la explicación va en voz ("No encontré la tele, ¿está prendida?").
9. **Dormido = no escucho.** Mismo símbolo en la bandeja del sistema. Es la promesa de privacidad, así que tiene que ser inconfundible.
10. **Sonidos cortos** (opcionales) que acompañan: un "pling" suave al despertar y un tic al terminar. Ayudan cuando no estás mirando.
11. **Movimiento reducido.** Opción en ajustes (y respeta la preferencia de Windows): sin saltos ni balanceos; solo cambian la cara y la opacidad de la isla.

## 5. Lenguaje visual

| Elemento | Regla |
|---|---|
| Cuerpo | Mochi blanco, cuadrado redondeado, base rosada. No cambia nunca de forma salvo squash & stretch (máx. ±8 %) |
| Ojos | Puntos negros con brillo (por defecto). Cerrados: línea, arco feliz `^ ^`, arco de sueño o apretados `> <`. Especiales: corazones, espirales. Párpados para *enojado* y *cansado* |
| Boca | Una sola línea o forma rellena: ω (neutral), sonrisa, punto, recta, triste, enojada, ondulada, óvalo al hablar, bostezo |
| Mejillas | Rosadas, se intensifican en *feliz* y *amor*, se apagan en *apenado* |
| Adornos | Solo uno por emoción y siempre fuera del cuerpo: ondas (*escuchando*), puntitos (*pensando*), `?`, `z`, corazones. Color lavanda medio para leerse en fondo claro y oscuro |
| Ritmo | 30 fps. Transiciones con easing, de al menos 4–5 frames. Loops sin costura |

## 6. Cómo se implementa en la app

- **No se usan secuencias de frames.** Luchi se dibuja **en vivo**: la imagen del cuerpo + la cara dibujada por código (canvas o SVG) a partir de parámetros.
- Hay **dos capas de datos**, separadas a propósito:
  - **Expresión** (cambia en cada frame, la manejan las animaciones): apertura de cada ojo, tipo de ojo cerrado, mirada x/y, escala de ojos, párpados (cobertura e inclinación), corazones, espirales, cejas (triste, enojada, levantada), boca (pesos por forma), apertura al hablar, bostezo, lagrimita, mejillas; y del cuerpo: escala x/y, altura, rotación y desplazamiento.
  - **Estilo** (lo elige el usuario): color, mejillas, ojos, boca, tatuaje, accesorio (§7).
- Cada emoción es una **línea de tiempo de parámetros de expresión**. Así se conectan a datos reales (nivel del micrófono, amplitud del TTS) y se encadenan estados sin saltos.
- El prototipo en Python es la **especificación visual**: `mockups/animaciones/luchi.py` (renderer y estilos), `tatuajes.py` y `animaciones.py` (líneas de tiempo).
- **Assets para la app:** `assets/luchi/` tiene todas las capas (cuerpos por color, ojos, accesorios, tatuajes) y `catalogo.json` con todas las opciones, coordenadas, parámetros por defecto, emociones y presets. Su README explica el orden de composición. Se regeneran con `python generar.py assets`. La implementación final va en TypeScript dentro de la isla (feature `island/`: componentes presentacionales + un contenedor con la máquina de estados).

## 7. Personalización ("Tu Luchi", F12)

Las animaciones no manejan dibujos, manejan **significados** ("ojo izquierdo abierto 60 %", "boca sonrisa"). Cada pieza de estilo sabe responder a esos significados, así que **cualquier combinación funciona con todas las emociones** sin rehacer nada. Catálogo visual en `mockups/personalizacion/` y en el visor.

### Catálogo

| Pieza | Opciones | Cómo responde a las animaciones |
|---|---|---|
| **Color** (10) | rosa `#e1a4a4` (por defecto), rojo `#dc5461`, naranja `#e19567`, amarillo `#e1cc67`, verde `#90da7c`, menta `#95e1c9`, celeste `#8fcfe1`, azul `#6988d8`, violeta `#af7cda`, nube `#d8d8d8` | Se cambia el tono del cuerpo conservando brillo y textura. Los párpados usan el mismo color para tapar el ojo |
| **Mejillas** (5) | rosa, coral, durazno, lavanda, ninguna | Capa propia; su intensidad la maneja la emoción |
| **Ojos** (6) | brillo, punto, óvalo, pestañas, estrellados, gatunos | Cada estilo es un sprite que se achata para parpadear; los ojos cerrados, corazones y espirales son comunes a todos. Los párpados se adaptan al alto de cada estilo |
| **Boca** (6) | línea, gruesa, dientes, colmillo, labios pintados, lengua | Todas usan el mismo contorno que se transforma. El estilo cambia el grosor o el color, o agrega detalles que siguen la forma: dientes y lengua dentro de la boca abierta, colmillo colgando del borde |
| **Tatuajes: patrón** (7, uno a la vez) | olas (seigaiha), rama de sakura, circuito, constelaciones, llamas, tribal, rayas de tigre | Cubren todo el cuerpo y se desvanecen alrededor de la cara para no tapar la expresión |
| **Tatuajes: flash** (19, hasta 3) | Código: `</>`, `{ }`, `;`, `404`, `$ sudo`, "Hola, Mundo!", bug, café, git, `<3`. Clásicos: ancla, Mamá, estrella náutica, rayo, luna, calaverita, gatito. Japoneses: onigiri, monte Fuji | En 4 posiciones: panza derecha, panza izquierda, frente y costado |
| **Accesorio: diario** (7) | lentes, auriculares, moño, flor de sakura, brote, orejas de gato, hachimaki | Capa sobre el cuerpo que puede salir de su contorno; sigue la escala, altura y rotación |
| **Accesorio: divertido** (9) | corona, orejas de conejo, antenas, bigote, lentes pixel, gorro con hélice, pajarito, flecha atravesada, gorro de chef | Igual. Los lentes pixel tapan los ojos a propósito: la emoción se lee por la boca, el cuerpo y los adornos |
| **Accesorio: temporada** (7) | gorro de fiesta (cumpleaños), gorro navideño, cuernitos y sombrero de bruja (Halloween), vincha de corazones (San Valentín), sombrero de paja (verano), birrete (graduación) | Se pueden poner solos en su fecha (opción en ajustes). El verano depende del hemisferio |

Los tatuajes se **multiplican** sobre la piel (conservan textura y sombreado), con trazo irregular, un leve desenfoque y corrido de tinta, para que parezcan tatuajes y no calcomanías.

Presets de ejemplo (animados en `mockups/personalizacion/presets/`): Clásica, Dev, Gamer, Sakura, Brote, Reina, Rockera, Ninja y Fiesta.

### Modelo de datos

El diseño de cada usuario es un JSON chico guardado en la PC:

```json
{
  "version": 1,
  "color": "azul",
  "blush": "rosa",
  "eyes": "punto",
  "mouth": "colmillo",
  "pattern": "circuito",
  "flash": [["codigo", "panza_der"]],
  "accessory": "lentes"
}
```

Agregar una pieza nueva = un estilo más que implementa la misma interfaz (`drawEyes(expr)`, `drawMouth(expr)`, `drawAccessory()`), validado contra la hoja de las 14 emociones.

### Reglas para que no se rompa la experiencia

- **Se elige, no se dibuja libre.** Piezas predefinidas que combinan entre sí, con vista previa animada en vivo.
- **Contraste mínimo garantizado.** Ojos y boca siempre oscuros sobre cuerpo claro. Si se agrega un color oscuro, la cara pasa a tinta clara automáticamente.
- **Las emociones no se personalizan.** Su significado (§3) es parte de la interfaz: cambia cómo se ven, no cuándo aparecen.
- **Detalles grandes, tamaño chico.** Tatuajes y accesorios finos se ven en el tamaño grande; en la isla (96 px) lo que manda es el color y la silueta.
- **Temporada sin pisar al usuario.** Si el usuario eligió un accesorio, el de temporada no lo reemplaza salvo que active "accesorios de temporada automáticos".
- **Todo local.** El diseño vive en un archivo de ajustes en la PC.

## 8. Pendiente de aprobación

- [ ] Forma, colores y estilo del personaje
- [ ] Las 16 animaciones y su ritmo
- [ ] El mapa de estados de §3
- [ ] Tamaño y posición de la isla
- [ ] Catálogo de personalización (§7)

## 9. Ideas para más interacción (propuestas, sin hacer)

Ordenadas por cuánto aportan a la experiencia frente a lo que cuestan.

| Idea | Qué hace | Por qué suma |
|---|---|---|
| **Seguir el cursor con la mirada** | Los ojos miran hacia el mouse cuando está cerca | Mucha vida por casi nada: es solo `look_x`/`look_y` |
| **Apretarlo (squish)** | Al hacer clic se aplasta como un mochi y rebota; si lo arrastrás y soltás, tiembla como gelatina | Es el gesto que más invita a tocarlo; refuerza que es un mochi |
| **Bailar con la música** | Cuando suena música (pediste "pon música"), rebota al ritmo usando el nivel de audio del sistema | Conecta el personaje con lo que el usuario acaba de pedir |
| **Pausas de reposo variadas** | En modo compañía, cada 20–60 s hace algo distinto: mira alrededor, se estira, salta, bosteza | Evita que el reposo se sienta como un loop |
| **Correr (sin piernas)** | Saltitos rápidos inclinado hacia donde va, con remolino de polvo y ráfagas onduladas (los efectos ya existen en `animaciones.py`) | Para moverse a otra posición o monitor, o "ir" hacia la app que abre |
| **Asomarse** | Aparece medio cuerpo desde el borde superior para avisar algo sin ocupar lugar | Avisos discretos (temporizador, recordatorio) |
| **Reacciones a lo que abre** | Lentes de sol al abrir un juego, palomitas al abrir Netflix | Personalidad ligada a las órdenes reales |
| **Fechas especiales** | Gorrito el día de su cumpleaños, nieve en diciembre | Sorpresa sin configurar nada |

Recomiendo empezar por **mirada al cursor, squish y bailar con la música**: son baratas, se usan todos los días y no necesitan estados nuevos en la app.
