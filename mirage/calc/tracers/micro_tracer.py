from dataclasses import dataclass, field
from importlib.util import find_spec
from abc import abstractmethod, ABC
import logging
from pathlib import Path

from astropy import units as u
import numpy as np

from mirage.settings import load_settings
from mirage.calc import RayTracer
from mirage.model import Starfield
from mirage.util import PixelRegion, DaskSettings, Platform

logger = logging.getLogger(__name__)


class _TracerFn(ABC):
  @abstractmethod
  def trace(
    self,
    rays: np.ndarray,
    kap: float,
    gam: float,
    star_mass: np.ndarray,
    star_pos: np.ndarray,
  ) -> np.ndarray:
    """
    Function to raytrace with specified parameters.
    """

  @staticmethod
  def create():
    platform = load_settings(DaskSettings).platform
    if platform in (Platform.PLATFORM_CPU_SIMD, Platform.PLATFORM_CPU):
      return _CpuTracerFn
    if platform == Platform.PLATFORM_CUDA:
      if not _CudaTracerFn.is_supported():
        raise EnvironmentError("Cuda tracing requested, but CUDA API is not available.")
      return _CudaTracerFn()
    if platform == Platform.PLATFORM_AUTO:
      if _CudaTracerFn.is_supported():
        return _CudaTracerFn()
      return _CpuTracerFn()


class _CpuTracerFn(_TracerFn):
  def trace(
    self,
    rays: np.ndarray,
    kap: float,
    gam: float,
    star_mass: np.ndarray,
    star_pos: np.ndarray,
  ) -> np.ndarray:
    from mirage.calc.tracers.micro_tracer_helper import trace

    return trace(rays, kap, gam, star_mass, star_pos, True)


class _CudaTracerFn(_TracerFn):
  # dependencies = ["cuda_bindings", "cuda_core", "nvidia-cuda-nvrtc", "cupy-cuda13x"]
  def __init__(self) -> None:
    self.device = None
    self.stream = None
    self.program = None
    self.cuda_module = None
    self.kernel = None

    with open(Path(__file__).parent / "cuda_tracer.cc") as f:
      self._program_source_code = f.read()

  @staticmethod
  def is_supported() -> bool:
    try:
      return find_spec("cuda.core") is not None
    except ModuleNotFoundError:
      return False

  def initialized(self) -> bool:
    return self.kernel is not None

  def initialize(self) -> None:
    from cuda.core import Device, Program, ProgramOptions

    if self.device:
      return
    self.device = Device()
    self.device.set_current()
    self.stream = self.device.create_stream()

    program_options = ProgramOptions(std="c++17", arch=f"sm_{self.device.arch}")
    self.program = Program(
      self._program_source_code, code_type="c++", options=program_options
    )
    self.cuda_module = self.program.compile(
      "cubin", name_expressions=("ray_trace_cuda<double>",)
    )
    self.kernel = self.cuda_module.get_kernel("ray_trace_cuda<double>")

  def trace(
    self,
    rays: np.ndarray,
    kap: float,
    gam: float,
    # TODO: Cache star data in GPU vram since it's doesn't change across chunks of rays.
    star_mass: np.ndarray,
    star_pos: np.ndarray,
  ) -> np.ndarray:
    from cuda.core import LaunchConfig, launch
    import cupy as cp

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


@dataclass
class MicrolensingRayTracer(RayTracer):
  starfield: Starfield
  star_mass: u.Quantity
  starfield_angular_radius: u.Quantity
  convergence: float
  shear: float
  tracer_fn: _TracerFn = field(default_factory=_TracerFn.create)

  def trace(self, rays: PixelRegion) -> u.Quantity:
    rays = rays.to("theta_0")

    stars_mass, stars_positions = self.starfield.get_starfield(
      self.star_mass, self.starfield_angular_radius
    )

    stars_positions = stars_positions.to("theta_0")

    pixels = rays.pixels.value

    logger.info(
      f"Running with {pixels.shape} (Total={pixels.shape[0] * pixels.shape[1]}) pixels"
    )

    traced_values = self.tracer_fn.trace(
      pixels,
      self.convergence,
      self.shear,
      stars_mass.to("solMass").value,
      stars_positions.to("theta_0").value,
    )

    return u.Quantity(traced_values, rays.unit)

  def __eq__(self, other: object) -> bool:
    if type(self) is not type(other):
      return False
    my_other: MicrolensingRayTracer = other  # type: ignore

    return (
      self.convergence == my_other.convergence
      and self.shear == my_other.shear
      and self.starfield == my_other.starfield
      and self.star_mass == my_other.star_mass
      and self.starfield_angular_radius == my_other.starfield_angular_radius
    )
