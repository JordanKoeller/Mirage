from functools import partial
import math
import logging
from dataclasses import dataclass
import copy
import tempfile
import uuid
import shutil
import os
import pickle
import gzip
from typing import Iterator
import itertools


import dask.bag as dask_bag
import dask.distributed
import dask
import numpy as np

from mirage.settings import load_settings
from mirage.sim import Simulation
from mirage.calc import Reducer, KdTree, RayTracer, ResultCalculator
from mirage.util import (
  PixelRegion,
  ClusterProvider,
  size_to_bytes,
  bytes_to_size,
  CacheLocation,
  timeit,
  DaskSettings,
)

logger = logging.getLogger(__name__)

PARTITION_SIZE_RANGE = ["10MB", "100MB"]
RAYS_PER_PARTITION = list(map(lambda s: size_to_bytes(s) / 16, PARTITION_SIZE_RANGE))
MAX_REDUCERS_PER_COMPUTATION = 100


@dataclass
class _RaysWithRegion:
  region: PixelRegion
  rays: np.ndarray


@timeit
def _ray_trace(simulation: Simulation, ray_tracer: RayTracer, region: PixelRegion):
  """
  Applies a RayTracer to a PixelRegion, returning the traced rays numpy array.
  """
  with simulation.special_units():
    return _RaysWithRegion(region, ray_tracer.trace(region))


@timeit
def _to_kd_tree(simulation: Simulation, rays_with_region: _RaysWithRegion):
  """
  Packs a numy array or rays into a KdTree.
  """
  with simulation.special_units():
    return KdTree(rays_with_region.rays, rays_with_region.region)


@timeit
def _apply_reducers(reducers: list[Reducer], kd_tree: KdTree) -> Reducer:
  """Reduce the specified KdTree with a reducer."""
  resolved = []
  for r in reducers:
    resolved_reducer = copy.deepcopy(r)
    resolved_reducer.reduce(kd_tree)
    resolved.append(resolved_reducer)
  return resolved


@timeit
def _persist_to_disk(compression_level: int, tree: KdTree) -> str:
  """
  Persists the kdTree to disk as a temporary file.

  Returns the path of the tempfile as a string.
  """
  dir_path = f"{tempfile.mkdtemp(prefix='mirage', suffix=str(uuid.uuid4()))}"
  with gzip.open(
    os.path.join(dir_path, "data.pickle.gz"),
    "wb+",
    compresslevel=compression_level,
  ) as f:
    pickle.dump(tree, f)
  return dir_path


@timeit
def _load_persisted_from_disk(compression_level: int, dir_path: str) -> KdTree:
  """
  Loads a KdTree that was persisted to disk by a call to
  _persist_to_disk back into memory.
  """
  with gzip.open(
    os.path.join(dir_path, "data.pickle.gz"),
    "rb",
    compresslevel=compression_level,
  ) as f:
    return pickle.load(f)


@timeit
def _cleanup_persisted_trees(dir_path: str) -> None:
  """
  Cleans up files from disk.
  """
  try:
    shutil.rmtree(dir_path)
  except FileNotFoundError:
    pass


@timeit
def _merge_reducers(aa: list[Reducer], bb: list[Reducer]) -> Reducer:
  """
  Merge two hydrated reducers, returning a new Reducer with the result.
  """
  return [a.merge(b) for a, b in zip(aa, bb)]


@dataclass
class DaskResultCalculator(ResultCalculator):
  cluster_provider: ClusterProvider
  trees: object | None = None
  settings: DaskSettings | None = None

  def initialize(self) -> None:
    self.cluster_provider.initialize()
    self.settings = load_settings(DaskSettings)
    logger.info(f"Dask Cluster hosted at {self.cluster_provider.dashboard}")

  def deinit(self) -> None:
    logger.debug("Dask Cluster shutting down.")
    if (
      self._cache_location == CacheLocation.CACHE_LOCATION_DISK
      and self.trees is not None
    ):
      dask.compute(self.trees.map(_cleanup_persisted_trees), sync=True)
      self.trees = None
    self.cluster_provider.close()

  def raytrace(self, simulation: Simulation) -> None:
    partition_size = self.cluster_provider.rays_per_partition
    with simulation.special_units():
      ray_tracer = simulation.get_ray_tracer()
      rays: PixelRegion = simulation.get_ray_bundle().to(
        simulation.lensing_system.theta_0
      )
    if partition_size < RAYS_PER_PARTITION[0] or partition_size > RAYS_PER_PARTITION[1]:
      logger.warning(
        f"ClusterProvider requested {partition_size} rays per partition, which falls outside"
        " of the recommended range. For optimal performance, each partition should"
        f" be in the range {RAYS_PER_PARTITION} rays ({PARTITION_SIZE_RANGE}) per partition."
      )
    num_rays = rays.num_pixels
    num_partitions = int(math.ceil(num_rays / partition_size))
    partition_mem_size = bytes_to_size(partition_size * 16)

    subdivisions = rays.subdivide(num_partitions)
    logger.info(
      f"Subdividing into {len(subdivisions)} ({partition_mem_size}) partitions"
    )
    logger.info(f"Total Number of Rays: {rays.resolution.x * rays.resolution.y}")
    trees_lazy = (
      dask_bag.from_sequence(subdivisions, partition_size=1)
      .map(partial(_ray_trace, simulation, ray_tracer))
      .map(partial(_to_kd_tree, simulation))
    )
    if self._cache_location == CacheLocation.CACHE_LOCATION_NONE:
      self.trees = trees_lazy
      return
    if self._cache_location == CacheLocation.CACHE_LOCATION_DISK:
      trees_lazy = trees_lazy.map(
        partial(_persist_to_disk, self.settings.compression_level)
      )
    self.trees = self.cluster_provider.client.persist(trees_lazy)

  def apply_reducer(self, reducer: Reducer) -> Reducer:
    if self.trees is None:
      raise ValueError("Called apply_reducer but trees have not been traced.")
    reduced_future = self.trees.map(partial(_apply_reducers, [reducer])).fold(
      _merge_reducers
    )
    return self.cluster_provider.client.compute(reduced_future, sync=True)

  def apply_all_reducers(self, reducers: Iterator[Reducer]) -> Iterator[Reducer]:
    trees = self.trees
    if self._cache_location == CacheLocation.CACHE_LOCATION_DISK:
      trees = trees.map(
        partial(_load_persisted_from_disk, self.settings.compression_level)
      )
    for reducers_batch in itertools.batched(
      reducers,
      self.settings.reducer_chunk_size or MAX_REDUCERS_PER_COMPUTATION,
    ):
      reducer_futures = trees.map(partial(_apply_reducers, reducers_batch)).fold(
        _merge_reducers
      )
      for resolved_future in self.cluster_provider.client.compute(
        reducer_futures, sync=True
      ):
        yield resolved_future

  @property
  def _cache_location(self) -> CacheLocation:
    return self.settings.cache_location
