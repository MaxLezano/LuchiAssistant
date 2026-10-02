#!/usr/bin/env bash
# F0-10: descarga los datos negativos (todos CC BY 4.0, ver docs/LICENCIAS.md). Reanudable.
# Uso (en WSL): bash descargar.sh ~/luchi-wakeword/data [partes_mls=10]
set -euo pipefail
DATOS="${1:?carpeta de datos}"; PARTES="${2:-10}"
RAW="$DATOS/raw"; mkdir -p "$RAW/mls_es"
bajar() { echo "-> $(basename "$2")"; curl -sSL -C - --retry 5 -o "$2" "$1"; }

for s in dev test; do
  bajar "https://huggingface.co/datasets/facebook/multilingual_librispeech/resolve/main/spanish/$s-00000-of-00001.parquet" "$RAW/mls_es/$s.parquet"
done
for i in $(seq 0 $((PARTES - 1))); do
  n=$(printf "%05d" "$i")
  bajar "https://huggingface.co/datasets/facebook/multilingual_librispeech/resolve/main/spanish/train-$n-of-00030.parquet" "$RAW/mls_es/train-$n.parquet"
done
bajar "https://www.openslr.org/resources/12/train-clean-100.tar.gz" "$RAW/librispeech-train-clean-100.tar.gz"
bajar "https://www.openslr.org/resources/17/musan.tar.gz" "$RAW/musan.tar.gz"

cd "$RAW"
[ -d LibriSpeech ] || { echo "descomprimiendo LibriSpeech"; tar xzf librispeech-train-clean-100.tar.gz; }
[ -d musan ] || { echo "descomprimiendo MUSAN"; tar xzf musan.tar.gz; }
du -sh "$RAW"/* | sort -h
echo "LISTO"
