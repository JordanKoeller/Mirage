from abc import ABC, abstractmethod
from typing import Optional
import multiprocessing
import logging
from dataclasses import dataclass, field
from enum import Enum

from dask.distributed import Client, LocalCluster

from mirage.util import DelegateRegistry, size_to_bytes

logger = logging.getLogger(__name__)


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


@dataclass
class CacheConfig:
  """
  Provides configuration on how Dask should cache intermediate values.

  location - Where intermediate values should be cached.
  compression_level - What level of gzip compression to apply to cached values. Must be
    between 0 and 9. The larger the number, the more aggressive the compression.
  """
  location: CacheLocation = CacheLocation.CACHE_LOCATION_MEMORY
  compression_level: int = 6

  def __post_init__(self) -> None:
    if self.compression_level < 0 or self.compression_level > 9:
      raise ValueError(
        f"Invalid cache compression level {self.compression_level}"
        " does not fall between 0 and 9."
      )


@dataclass
class ClusterProvider(ABC):
  @property
  @abstractmethod
  def rays_per_partition(self) -> float:
    """
    The requested number of rays to put in each partition
    """

  @abstractmethod
  def initialize(self):
    """
    Initialize a Dask cluster.
    """

  @abstractmethod
  def close(self):
    """
    Terminate a Dask cluster.
    """

  @property
  @abstractmethod
  def client(self) -> Client:
    """
    Get the `dask.Client` to use when submitting a job.
    """

  @property
  @abstractmethod
  def dashboard(self) -> str:
    """
    Returns the url of the Dask dashboard.
    """

  def __del__(self) -> None:
    self.close()


@dataclass(kw_only=True)
@DelegateRegistry.register
class LocalClusterProvider(ClusterProvider):
  num_workers: int = field(default_factory=multiprocessing.cpu_count)
  threads_per_worker: int = 1
  worker_mem: str = field(default_factory=lambda: "1.5GiB")
  rays_per_chunk: int = field(default_factory=lambda: 1e6)
  cache_config: CacheConfig = field(default_factory=CacheConfig)
  reducers_chunk_size: int = 0

  def __post_init__(self):
    self._cluster: Optional[LocalCluster] = None
    self._client: Optional[Client] = None

  def initialize(self):
    self._cluster = LocalCluster(
      n_workers=self.num_workers,
      memory_limit=self.worker_mem,
      threads_per_worker=self.threads_per_worker,
    )
    self._client = Client(self._cluster)

  def close(self):
    if self._client:
      self._client.close()
    if self._cluster:
      self._cluster.close()

  @property
  def client(self) -> Client:
    if self._client:
      return self._client
    raise ValueError("Cluster was not initialize. Please call `.initialize()` first")

  @property
  def rays_per_partition(self) -> float:
    return self.rays_per_chunk

  @property
  def dashboard(self) -> str:
    if self._cluster is None:
      raise ValueError("Cluster has not been initialized!")
    return self._cluster.dashboard_link


@dataclass(kw_only=True)
@DelegateRegistry.register
class RemoteClusterProvider(ClusterProvider):
  scheduler_uri: str
  partition_size: str

  def __post_init__(self):
    self._client: Optional[Client] = None

  def initialize(self):
    self._client = Client(self.scheduler_uri)

  def close(self):
    pass

  @property
  def client(self) -> Client:
    if self._client:
      return self._client
    raise ValueError("Client was not initialized. Please call `.initialize()` first")

  @property
  def rays_per_partition(self) -> float:
    return size_to_bytes(self.partition_size) / 16

  @property
  def dashboard(self) -> str:
    if self._client is None:
      raise ValueError("Client has not been initialized!")
    return self._client.dashboard_link


@dataclass(kw_only=True)
@DelegateRegistry.register
class AwsEphemeralClusterProvider(ClusterProvider):
  num_workers: int
  cpus_per_worker: int
  partition_size: str
  docker_image: str = "jkoeller12/mirage:latest"

  def __post_init__(self):
    self._client: Optional[Client] = None
    self._cluster = None

  def initialize(self):
    from dask_cloudprovider.aws import FargateCluster

    self._cluster = FargateCluster(
      image=self.docker_image,
      worker_cpu=1024 * self.cpus_per_worker,
      worker_mem=1024 * self.cpus_per_worker * 2,
      worker_nthreads=1,
      scheduler_cpu=1024 * 2,
      scheduler_mem=1024 * 4,
      n_workers=self.num_workers,
      worker_extra_args=(
        f"--nworkers {self.cpus_per_worker} --memory-limit 1.8GiB".split(" ")
      ),
    )
    self._client = self._cluster.get_client()

  def close(self):
    self._client.close()
    self._cluster.close()

  @property
  def client(self) -> Client:
    if self._client:
      return self._client
    raise ValueError("Client was not initialized. Please call `.initialize()` first")

  @property
  def rays_per_partition(self) -> float:
    return size_to_bytes(self.partition_size) / 16

  @property
  def dashboard(self) -> str:
    if self._client is None:
      raise ValueError("Client has not been initialized!")
    return self._client.dashboard_link
