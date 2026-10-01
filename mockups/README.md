# Mockups de Luchi

Referencias visuales del personaje. **No son el código de la app**: la app dibujará a Luchi en vivo con los mismos parámetros (ver [docs/PERSONAJE.md](../docs/PERSONAJE.md)).

**Para revisar todo:** abrir `animaciones/visor.html` (personaje) y `ui/index.html` (interfaz de la app).

## Animaciones (`animaciones/`)

| Archivo | Qué es |
|---|---|
| `visor.html` | Emociones, catálogo y presets, sobre fondo claro, oscuro o de pantalla, en tamaño grande o isla |
| `<emoción>.webp` | Las 16 animaciones (30 fps, fondo transparente) |
| `emociones.png` | Pose clave de cada emoción |
| `luchi.py` | Renderer: cuerpo, cara paramétrica y catálogo de estilos |
| `tatuajes.py` | Patrones, diseños flash y el efecto de tinta real |
| `accesorios.py` | Los 23 accesorios, sus categorías y fechas de temporada |
| `animaciones.py` | Línea de tiempo de cada emoción |
| `generar.py` | Exporta todo: `python generar.py [anim] [catalogo] [presets] [assets] [<emoción>] [--frames]` (requiere Pillow) |
| `fuentes/` | Imagen original elegida y cuerpo sin cara (ComfyUI) |

## Personalización (`personalizacion/`)

| Archivo | Qué es |
|---|---|
| `colores.png` | 10 colores del cuerpo con su hex |
| `ojos.png` | 6 estilos de ojos en 5 emociones |
| `bocas.png` | 6 estilos de boca en 5 emociones |
| `tatuajes_patrones.png` | 7 patrones de cuerpo completo |
| `tatuajes_flash.png` | 19 diseños chicos (código, clásicos, japoneses) |
| `tatuajes_combinados.png` | Patrón + varios flash juntos |
| `accesorios_diario.png`, `accesorios_divertido.png`, `accesorios_temporada.png` | 23 accesorios por categoría |
| `presets.png`, `presets/*.webp` | 9 Luchis de ejemplo, animados hablando |

Las capas listas para la app y `catalogo.json` están en `assets/luchi/` (se generan con `generar.py assets`). La portada está en `assets/branding/luchi_portada.png`.

## Interfaz de la app (`ui/`)

| Archivo | Qué es |
|---|---|
| `index.html` | Prototipo navegable: escritorio con la isla, bandeja y ventana de la app. Enlaces directos: `#isla`, `#bienvenida`, `#tuluchi`, `#casa`, `#grabaciones`… |
| `ui.css`, `ui.js` | Estilos y lógica del prototipo. El editor "Tu Luchi" compone las capas reales de `assets/luchi/` |
| `generar_piezas.py` | Exporta bocas y ojos cerrados por pose (`piezas/`) y `datos.js` desde `catalogo.json` |

Especificación de cada pantalla: [docs/INTERFAZ.md](../docs/INTERFAZ.md).
