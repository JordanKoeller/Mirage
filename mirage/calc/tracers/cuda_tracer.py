# /// script
# dependencies = ["cuda_bindings", "cuda_core", "nvidia-cuda-nvrtc", "cupy-cuda13x"]
# ///

from pathlib import Path

import cupy as cp
import numpy as np

from cuda.core import Device, LaunchConfig, Program, ProgramOptions, launch

class CudaTracer:
