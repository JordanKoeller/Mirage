from dataclasses import dataclass
from enum import Enum


class CacheLocation(Enum):
  """
  Specifies where Dask is allowed to cache intermediate values when computing
  an experiment.

  CACHE_LOCATION_NONE - Intermediate value caching is disabled. This is suitable if few
    Reducers are being computed, but may cause intermediate values to be computed
    multiple times if many Reducers are being calculated.

  CACHE_LOCATION_MEMORY - Intermediate values are saved in memory for reuse. This is
    suitable if the simulated number of rays is small enough to comfortably sit in
    cluster memory, and many Reducers are being calculated. Note that calculations may
    fail do to Out-Of-Memory errors if the simulation consumes more memory than available.

  CACHE_LOCATION_DISK - Intermediate are saved to disk in temporary files. This is
    suitable for calculations where the size of the simulation exceeds the amount of
    available cluster memory, or in case of cluster instability. Note that for small
    computations, this introduces additional overhead of reading and writing to disk,
    resulting in a performance hit.
  """

  CACHE_LOCATION_NONE = "CACHE_LOCATION_NONE"
  CACHE_LOCATION_MEMORY = "CACHE_LOCATION_MEMORY"
  CACHE_LOCATION_DISK = "CACHE_LOCATION_DISK"


class Platform(Enum):
  """
  What platform to use when ray-tracing. If a suitable platform cannot be found, an
  EnvironmentError is raised.

  PLATFORM_CPU: Ray-tracing will be performed on the worker's CPU. One core per Dask worker.
  PLATFORM_CPU_SIMD: Ray-tracing will be performed on the worker's CPU, using SIMD instructions.
  PLATFORM_CUDA: Ray-tracing will be performed on an available Nvidia GPU, using the CUDA API.
  PLATFORM_AUTO: Uses the fastest available platform available.
  """

  PLATFORM_AUTO = "PLATFORM_AUTO"
  PLATFORM_CPU = "PLATFORM_CPU"
  PLATFORM_CPU_SIMD = "PLATFORM_CPU_SIMD"
  PLATFORM_CUDA = "PLATFORM_CUDA"


@dataclass
class DaskSettings:
  cache_location: CacheLocation = CacheLocation.CACHE_LOCATION_MEMORY
  compression_level: int = 6
  platform: Platform = Platform.PLATFORM_AUTO
  reducer_chunk_size: int = 1

  def __post_init__(self) -> None:
    if self.compression_level < 0 or self.compression_level > 9:
      raise ValueError(
        f"Invalid cache compression level {self.compression_level}"
        " does not fall between 0 and 9."
      )
