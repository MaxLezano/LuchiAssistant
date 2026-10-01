# Assets de Luchi

Capas listas para que la app dibuje y personalice a Luchi **en vivo**. Todo lo describe [`catalogo.json`](catalogo.json).
Se generan con `mockups/animaciones/generar.py assets`; no se editan a mano.

Diseño, emociones y reglas de interacción: [docs/PERSONAJE.md](../../docs/PERSONAJE.md). Referencia de cómo se ve todo: `mockups/animaciones/visor.html`.

## Contenido

| Carpeta | Qué hay | Tamaño / espacio |
|---|---|---|
| `cuerpo/<color>.png` | Cuerpo sin cara en cada uno de los 10 colores, con transparencia | 1024×1024, espacio común |
| `cuerpo/mascara.png` | Silueta del cuerpo (superelipse) | 1024×1024 |
| `ojos/<estilo>_<izq\|der>.png` | Sprite de cada estilo de ojo, centrado | 140×140, centro en (70, 70) |
| `accesorios/<id>.png` | 23 accesorios ya ubicados (pueden salir del cuerpo). En el catálogo: `categoria` (diario, divertido, temporada), `temporada` y `tapa_ojos` | 1024×1024, espacio común |
| `tatuajes/patrones/<id>.png` | Tinta de cada patrón de cuerpo completo (sin aplicar) | 1024×1024, espacio común |
| `tatuajes/flash/<id>.png` | Tinta de cada diseño chico, a escala 1 | 200×200, centro en (100, 100) |
| `tatuajes/ruido.png` | Textura para la irregularidad de la tinta | 1024×1024 |
| `tatuajes/mascara_cara.png` | Dónde pueden ir los patrones (0 = zona de la cara) | 1024×1024 |

**Espacio común:** todas las capas de 1024×1024 comparten coordenadas. Las posiciones clave (centro de cada ojo, boca, mejillas, caja del cuerpo, posiciones de los tatuajes) están en `catalogo.json → espacio` y `tatuajes.posiciones`.

## Orden de composición (de abajo hacia arriba)

1. **Sombra** bajo el cuerpo (elipse suave que se achica cuando sube) + sombra de contorno (silueta desplazada 5 px y desenfocada, 20 % de opacidad).
2. **Cuerpo** del color elegido (`cuerpo/<color>.png`).
3. **Tatuajes**, en modo `multiply` sobre el cuerpo (ver *Realismo*).
4. **Mejillas**: dos elipses de 76×34 en `espacio.mejillas`, desenfoque 7 px, color de `mejillas`, opacidad `150/255 × expresion.blush`.
5. **Ojos abiertos**: sprite del estilo, escalado en alto por `open_l` / `open_r` y desplazado por `look_x` / `look_y`. Cuando la apertura baja de 0,2 se cambia **en seco** por el ojo cerrado (nunca se mezclan).
6. **Párpados** (`lid_*`, `lid_tilt`): se tapa la parte de arriba del ojo con píxeles del propio cuerpo y se dibuja la línea del párpado.
7. **Tinta vectorial**: ojos cerrados, corazones, espirales, cejas, lagrimita.
8. **Boca**: un único contorno de 48 puntos por borde que se interpola entre formas (morph). El estilo cambia grosor/color o agrega dientes, colmillo, labios o lengua siguiendo ese contorno.
9. **Accesorio** (`accesorios/<id>.png`).
10. Todo lo anterior forma el *sprite* de Luchi, que se transforma como un bloque: escala x/y (squash & stretch) anclada en la base, altura, rotación y desplazamiento.
11. **Adornos** de la emoción, fuera del cuerpo: ondas, `?`, `z`, corazones, 💢, estrellitas, polvo.

## Realismo de los tatuajes

Para que parezcan tinta en la piel y no una calcomanía (valores en `tatuajes.realismo`):

1. Mezclar los colores de la tinta un 12 % hacia el azul tinta, **salvo el blanco** (el blanco es "sin tinta").
2. Alfa = alfa desenfocado 0,9 px × `ruido.png` × 0,9.
3. Sumar un "corrido": alfa desenfocado 3 px al 18 %.
4. Fusionar con `multiply` sobre el cuerpo: así se conservan la textura y el sombreado.
5. Los **patrones** se multiplican además por `mascara_cara.png`, para no tapar la expresión.
6. Los **flash** se dibujan en su posición (`posiciones.<slot>`) con su escala. Máximo 3.

## Accesorios de temporada

`catalogo.json → temporadas` tiene las fechas sugeridas (MM-DD). Cumpleaños y graduación las define el usuario; el verano depende del hemisferio (se elige en ajustes). Si están activados los automáticos, en esas fechas se muestra el accesorio de temporada en lugar del elegido.

## Diseño del usuario

El diseño de cada usuario es un JSON chico (ejemplo en `catalogo.json → diseno_usuario_ejemplo`):

```json
{ "version": 1, "color": "azul", "blush": "rosa", "eyes": "punto", "mouth": "colmillo",
  "pattern": "circuito", "flash": [["codigo", "panza_der"]], "accessory": "lentes" }
```

## Lo que se dibuja por código (no son imágenes)

Ojos cerrados, corazones, espirales, cejas, párpados, bocas, mejillas, sombras y adornos. Sus formas exactas están en `mockups/animaciones/luchi.py` (funciones `draw_face`, `mouth_shape`, `_lid`) y las líneas de tiempo de cada emoción en `animaciones.py`.
