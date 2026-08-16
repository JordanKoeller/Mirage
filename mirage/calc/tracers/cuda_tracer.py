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
    self.device = Device()
    self.device.set_current()
    self.stream = device.create_stream()

    program_options = ProgramOptions(std="c++17", arch=f"sm_{self.device.arch}")
    self.program = Program(self._program_source_code, code_type="c++", options=program_options)
    self.cuda_module = self.program.compile("cubin", name_expressions=("ray_trace_cuda<double>",))
    self.kernel = mod.get_kernel("ray_trace_cuda<double>")

  def cuda_trace(
    self,
    rays: np.ndarray,
    kap: float,
    gam: float,
    # TODO: Cache star data in GPU vram since it's doesn't change across chunks of rays.
    star_pos: np.ndarray,
    star_mass: np.ndarray,
  ) -> np.ndarray:
    rays_x = cp.asarray(rays[:, :, 0])
    rays_y = cp.asarray(rays[:, :, 1])
    stars_x = cp.asarray(star_pos[:, 0])
    stars_y = cp.asarray(star_pos[:, 1])
    stars_m = cp.asarray(star_mass[:, 0])

    out_x = cp.empty_like(rays_x)
    out_y = cp.empty_like(rays_y)

    self.device.sync()

    # prepare launch
    block = 256
    grid = (size + block - 1) // block
    config = LaunchConfig(grid=grid, block=block)

    launch(
        self.stream,
        config,
        self.kernel,
        rays_x.data.ptr,
        rays_y.data.ptr,
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


# def main():
#     dev = Device()
#     dev.set_current()
#     stream = dev.create_stream()

#     try:
#         # prepare program
#         program_options = ProgramOptions(std="c++17", arch=f"sm_{dev.arch}")
#         prog = Program(code, code_type="c++", options=program_options)
#         mod = prog.compile("cubin", name_expressions=("ray_trace_cuda<double>",))

#         # run in single precision
#         kernel = mod.get_kernel("ray_trace_cuda<double>")
#         dtype = cp.float64

#         # prepare input/output
#         size = 50000
#         rng = cp.random.default_rng()
#         a = rng.random(size, dtype=dtype)
#         b = rng.random(size, dtype=dtype)
#         c = cp.empty_like(a)

#         # cupy runs on a different stream from stream, so sync before accessing
#         dev.sync()

#         # prepare launch
#         block = 256
#         grid = (size + block - 1) // block
#         config = LaunchConfig(grid=grid, block=block)

#         # launch kernel on stream
#         launch(stream, config, kernel, a.data.ptr, b.data.ptr, c.data.ptr, cp.uint64(size))
#         stream.sync()

#         # check result
#         assert cp.allclose(c, a + b)
#     finally:
#         stream.close()


# if __name__ == "__main__":
#     main()