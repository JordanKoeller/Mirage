from abc import ABC, abstractmethod
from typing import Optional
import logging
import multiprocessing
from dataclasses import dataclass, field

from dask.distributed import Client, LocalCluster
from dask_cloudprovider.aws import FargateCluster

from mirage.util import DelegateRegistry

logger = logging.getLogger(__name__)


@dataclass
class ClusterProvider(ABC):

  @property
  @abstractmethod
  def num_partitions(self) -> int:
    """
    The number of partitions to use when running a simulation.
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


@dataclass(kw_only=True)
@DelegateRegistry.register
class LocalClusterProvider(ClusterProvider):
  num_workers: int = field(default_factory=multiprocessing.cpu_count)
  worker_mem: str = field(default_factory=lambda: "1GiB")

  def __pre_init__(self):
    self._cluster: Optional[LocalCluster] = None
    self._client: Optional[Client] = None

  def initialize(self):
    self._cluster = LocalCluster(
        n_workers=self.num_workers, memory_limit=self.worker_mem, threads_per_worker=2
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
    raise ValueError("Cluster was not intiailized. Please call `.intiailize()` first")

  @property
  def num_partitions(self) -> int:
    return self.num_workers

  @property
  def dashboard(self) -> str:
    if self._cluster is None:
      raise ValueError("Cluster has not been initialized!")
    return self._cluster.dashboard_link


@dataclass(kw_only=True)
@DelegateRegistry.register
class RemoteClusterProvider(ClusterProvider):
  scheduler_uri: str

  def __pre_init__(self):
    self._client: Optional[Client] = None

  def initialize(self):
    self._client = Client(self.scheduler_uri)
    logger.info(f"Connected to Dask Cluster {self.scheduler_uri}")

  def close(self):
    pass

  @property
  def client(self) -> Client:
    if self._client:
      return self._client
    raise ValueError("Client was not intiailized. Please call `.intiailize()` first")

  @property
  def num_partitions(self) -> int:
    return 12

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

  def __pre_init__(self):
    self._client: Optional[Client] = None
    self._cluster: Optional[FargateCluster] = None

  def initialize(self):
    self._cluster = FargateCluster(
        image="jkoeller12/mirage:latest",
        worker_cpu=1024 * self.cpus_per_worker,
        worker_mem=1024 * self.cpus_per_worker * 2,
        worker_nthreads=self.cpus_per_worker * 2,
        scheduler_cpu=1024 * 2,
        scheduler_mem=1024 * 4,
        n_workers=self.num_workers,
    )
    self._client = self._cluster.get_client()
    logger.info(f"Connected to Dask Cluster {self._client.dashboard_link}")

  def close(self):
    self._client.close()
    self._cluster.close()

  @property
  def client(self) -> Client:
    if self._client:
      return self._client
    raise ValueError("Client was not intiailized. Please call `.intiailize()` first")

  @property
  def num_partitions(self) -> int:
    return 32

  @property
  def dashboard(self) -> str:
    if self._client is None:
      raise ValueError("Client has not been initialized!")
    return self._client.dashboard_link
