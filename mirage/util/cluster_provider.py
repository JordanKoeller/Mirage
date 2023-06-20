from abc import ABC, abstractmethod
from typing import Optional
import logging

from dask.distributed import Client, LocalCluster

logger = logging.getLogger(__name__)


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


class LocalClusterProvider(ClusterProvider):

  def __init__(self, num_workers: int, worker_mem: str):
    self.num_workers = num_workers
    self.worker_mem = worker_mem
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


class RemoteClusterProvider(ClusterProvider):

  def __init__(self, uri: str):
    self._scheduler_uri = uri
    self._client: Optional[Client] = None

  def initialize(self):
    self._client = Client(self._scheduler_uri)
    logger.info(f"Connected to Dask Cluster {self._scheduler_uri}")

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
