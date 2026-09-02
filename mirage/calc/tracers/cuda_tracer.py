# /// script
# dependencies = ["cuda_bindings", "cuda_core", "nvidia-cuda-nvrtc", "cupy-cuda13x"]
# ///

from pathlib import Path

import cupy as cp

from cuda.core import Device, LaunchConfig, Program, ProgramOptions, launch

# compute c = a + b
code = """
template<typename T>
__global__ void vector_add(const T* A,
                           const T* B,
                           T* C,
                           size_t N) {
    const unsigned int tid = threadIdx.x + blockIdx.x * blockDim.x;
    for (size_t i=tid; i<N; i+=gridDim.x*blockDim.x) {
        C[i] = A[i] + B[i];
    }
}
"""

class CudaTracer:
  def __init__(self) -> None:
    self.device = None
    self.stream = None
    self.program = None
    self.cuda_module = None
    self.kernel = None

    with open(Path(__file__).parent / "cuda_tracer.cc" ) as f:
        self._program_source_code = f.read()

  def initialized(self) -> bool:
    return self.kernel is not None

  def initialize(self) -> None:
    if self.device:
        return
    self.device = Device()
    self.device.set_current()
    self.stream = self.device.create_stream()

    program_options = ProgramOptions(std="c++17", arch=f"sm_{self.device.arch}")
    self.program = Program(self._program_source_code, code_type="c++", options=program_options)
    self.cuda_module = self.program.compile("cubin", name_expressions=("ray_trace_cuda<double>",))
    self.kernel = self.cuda_module.get_kernel("ray_trace_cuda<double>")

  def cuda_trace(
    self,
    rays: np.ndarray,
    kap: float,
    gam: float,
    # TODO: Cache star data in GPU vram since it's doesn't change across chunks of rays.
    star_mass: np.ndarray,
    star_pos: np.ndarray,
  ) -> np.ndarray:
    self.initialize()
    rays_x = cp.asarray(rays[:, :, 0])
    rays_y = cp.asarray(rays[:, :, 1])
    stars_x = cp.asarray(star_pos[:, 0])
    stars_y = cp.asarray(star_pos[:, 1])
    stars_m = cp.asarray(star_mass)

    out_x = cp.empty_like(rays_x)
    out_y = cp.empty_like(rays_y)

    self.device.sync()

    # prepare launch
    num_rays = rays_x.shape[0] * rays_y.shape[1]
    block = 256
    grid = (num_rays + block - 1) // block
    config = LaunchConfig(grid=grid, block=block)

    launch(
        self.stream,
        config,
        self.kernel,
        rays_x.data.ptr,
        rays_y.data.ptr,
        cp.uint64(num_rays),
        cp.float64(kap),
        cp.float64(gam),
        stars_x.data.ptr,
        stars_y.data.ptr,
        stars_m.data.ptr,
        cp.uint64(stars_m.shape[0]),
        out_x.data.ptr,
        out_y.data.ptr,
    )
    self.stream.sync()

    rays[:, :, 0] = out_x.get()
    rays[:, :, 1] = out_y.get()

    self.stream.close()

    return rays