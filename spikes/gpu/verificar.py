"""Spike F0-03: confirma Python 3.12 y la GPU desde PyTorch y CTranslate2.

Uso: cd spikes/gpu && uv run python verificar.py
"""
import os
import pathlib
import sys
import sysconfig

# CTranslate2 en Windows busca cuBLAS/cuDNN en el PATH: se agregan las DLL de los paquetes nvidia-*.
nvidia = pathlib.Path(sysconfig.get_paths()["purelib"]) / "nvidia"
for bin_dir in nvidia.glob("*/bin"):
    os.add_dll_directory(str(bin_dir))
    os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"

import ctranslate2  # noqa: E402
import torch  # noqa: E402

ok = True
print(f"Python {sys.version.split()[0]}")
ok &= sys.version_info[:2] == (3, 12)

print(f"PyTorch {torch.__version__} · CUDA {torch.version.cuda} · disponible: {torch.cuda.is_available()}")
ok &= torch.cuda.is_available()
if torch.cuda.is_available():
    print(f"  GPU: {torch.cuda.get_device_name(0)} · cuDNN {torch.backends.cudnn.version()}")
    a = torch.randn(2048, 2048, device="cuda")
    print(f"  matmul en GPU: {float((a @ a).sum()):.1f}")

n = ctranslate2.get_cuda_device_count()
print(f"CTranslate2 {ctranslate2.__version__} · GPUs CUDA: {n} · tipos: {sorted(ctranslate2.get_supported_compute_types('cuda')) if n else '-'}")
ok &= n > 0

print("OK" if ok else "FALLA")
sys.exit(0 if ok else 1)
