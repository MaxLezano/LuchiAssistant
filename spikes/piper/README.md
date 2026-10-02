# Spike: voz de Luchi con Piper

```bash
cd spikes/piper
uv run python comparar.py   # 6 voces × 6 frases → output/index.html
uv run python ingles.py     # nombres en inglés de tres formas → output/ingles.html
```

Las voces se descargan a `E:\Luchi\models\piper` (fuera de git).

## Resultado (2026-10-01)

| Voz | Acento | RTF (CPU) | "Listo." | Licencia del dataset |
|---|---|---|---|---|
| **es_AR-daniela-high** ✅ elegida | Argentina, mujer | 0,22 | 90 ms | CC BY-SA 4.0 (atribución) |
| es_MX-claude-high | México | 0,035 | 30 ms | Apache 2.0 |
| es_ES-sharvard-medium (2 hablantes) | España | 0,035 | 23–26 ms | CC BY 3.0 |
| es_ES-davefx-medium | España, hombre | 0,034 | 27 ms | CC0 |
| es_MX-ald-medium | México, hombre | 0,034 | 41 ms | Unlicense |

**daniela** es provisoria: en F9 la reemplaza la voz clonada de la hija del autor (derechos propios).

## Nombres en inglés

Piper lee todo con las reglas de espeak del idioma de la voz, así que "Hollow Knight" sale en castellano. Se probaron tres variantes:

1. Tal cual: suena mal.
2. Reescrito a mano ("Jólou Náit"): suena bien, pero hay que escribir cada nombre.
3. **Fonemas en inglés** ✅ elegida: el nombre se convierte con espeak `en-us` y se inserta entre `[[ ]]` (sintaxis de fonemas crudos de Piper). Suena igual de bien que la 2 y es automática.

Reglas para implementarlo (F2, `TextToSpeechPort`):

- Solo se convierten los **nombres marcados como extranjeros** (catálogo de apps y juegos, títulos, artistas, dispositivos); las palabras en castellano de la frase no se tocan.
- La voz tiene todos los fonemas IPA del inglés en su mapa (`phoneme_id_map`), así que no se pierde ningún sonido.

## Licencia del motor

`piper-tts` 1.8 (OHF-Voice/piper1-gpl) es **GPL-3.0**. Para un producto comercial puede obligar a liberar `luchi-voice`. **sherpa-onnx** (Apache 2.0) corre los mismos modelos de Piper. El motor se elige en F2 y se revisa en F13-04; la voz y la técnica de `[[ ]]` hay que verificarlas con el motor elegido.
