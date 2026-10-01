# Spike: Ollama + tool calling

Comprueba que `qwen3:8b` elige bien herramientas con `think: false` y mide latencia y VRAM. Solo usa la librería estándar.

```bash
python spikes/ollama/probar_tools.py            # qwen3:8b
python spikes/ollama/probar_tools.py otro:modelo
```

Resultados en [docs/ENTORNO.md](../../docs/ENTORNO.md#ollama). La comparación de modelos con el set de evaluación real es la tarea F3-06.
