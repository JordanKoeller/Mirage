from mirage.parameters import MicrolensingParameters
from mirage.util import Vec2D

from astropy import units as u
# from .CalculationDelegate import CalculationDelegate

from mirage.engine.dask_tracer import trace_bundle

from functools import partial
import numpy as np
from scipy.spatial import cKDTree
from dask.delayed import delayed
from dask import array
# import dask.array as Array
# import dask.bag as Bag
import math



class DaskCalculationDelegate:

  def __init__(self, client):
    self.client = client
    print("Using a dask calculation delegate. See localhost:8787 to see the simulation's progress")
    self.chunk_size = 250000
    self.leaf_size = 128
    self.blocks = None


  def reconfigure(self, parameters: MicrolensingParameters):
    self.parameters = parameters
    self._inputUnit = self.parameters.theta_E
    self.ray_trace()
    # xs = Array.arange(x1, x2, dx)
    # ys = Array.arange(y1, y2, dy)

  def ray_trace(self):
    kap, starry, gam = self.parameters.mass_descriptors
    stars = self.parameters.stars
    pixels = self.parameters.ray_region.to(self._inputUnit)
    resolution = pixels.resolution
    chunk_x, chunk_y = int(math.sqrt(self.chunk_size * resolution.y / resolution.x)), int(math.sqrt(self.chunk_size * resolution.x / resolution.y))
    dTheta = pixels.dTheta
    inds = array.arange(resolution.area.value, chunks=self.chunk_size)
    rays_blocks = np.array(inds.to_delayed()).flatten()
    self.blocks = []
    for block in rays_blocks:
        block = delayed(DaskCalculationDelegate._trace_block)(kap, gam, stars, pixels.top_left_corner, dTheta, resolution, block)
        self.blocks.append(block)
    print("Made", len(self.blocks), "blocks")
    self.build_kd_tree()

  def build_kd_tree(self):
    self.trees = [
      delayed(DaskCalculationDelegate._to_kd_tree)(block, self.leaf_size)
      for block in self.blocks
    ]

  def query_region(self, region, radius):
    return self.query_points(region.pixels.to(self._inputUnit).value, radius)

  def query_points(self, points: np.ndarray, radius: u.Quantity) -> np.ndarray:
    orig_shape = points.shape
    if len(points.shape) == 3:
      points = points.reshape((orig_shape[0]*orig_shape[1], 2))
    queried = [
      delayed(DaskCalculationDelegate._query_points)(block, points, radius.to(self._inputUnit).value, self.leaf_size)
      for block in self.trees
    ]
    total_block = queried[0]
    for b in queried[1:]:
      total_block = delayed(lambda a, b: a + b)(total_block, b)
    # total_block = DaskCalculationDelegate._sum_tree(queried)
    total_matrix = total_block.compute()
    if points.shape != orig_shape:
      total_matrix = total_matrix.reshape((orig_shape[0], orig_shape[1]))
    return total_matrix.astype(np.float64)

  @staticmethod
  def _sum_tree(blocks, max_depth=6):
    queue = [blocks]
    max_depth = 6
    curr_depth = 0
    while max_depth < curr_depth:
      next_queue = []
      curr_depth += 1
      for block_group in queue:
        if len(block_group) > 4:
          next_queue.append(block_group[:len(block_group) // 2])
          next_queue.append(block_group[len(block_group) // 2:])
        else:
          next_queue.append(block_group)
      queue = next_queue
    has_queue = True
    subblock1 = None
    while has_queue:
      next_queue = []
      has_queue = False
      for superblock in queue:
        b1 = superblock[0]
        bs = superblock[:1]
        for b in bs:
          b1 = delayed(lambda a, b: a + b)(b1, b)
        if subblock1 is not None:
          next_queue.append([subblock1, b1])
          has_queue = True
          subblock1 = None
        else:
          subblock1 = b1
      queue = next_queue
    return subblock1

  @staticmethod
  def _query_points(block, query_points, radius, leaf_size):
    query_tree = cKDTree(query_points, leafsize=leaf_size)
    rays_per_query = query_tree.query_ball_tree(block, radius)
    return np.array([len(q) for q in rays_per_query], dtype=np.float64)

  @staticmethod
  def _to_kd_tree(block, leaf_size):
    return cKDTree(block, leafsize=leaf_size)

  @staticmethod
  def _sum_blocks(blocks, depth, max_depth=6):
    if depth == max_depth:
      seed = blocks[0]
      if len(blocks) > 1:
        for block in seed[1:]:
          seed = delayed(lambda a, b: a + b)(a,b)
      return seed
    num_blocks = len(blocks)
    lhs = delayed(DaskCalculationDelegate._sum_blocks)(blocks[:num_blocks // 2], depth+1, max_depth)
    rhs = delayed(DaskCalculationDelegate._sum_blocks)(blocks[num_blocks // 2:], depth+1, max_depth)
    return lhs + rhs

  @staticmethod
  def _trace_block(kappa: float, gamma: float, stars: np.ndarray, origin, dTheta, resolution, block):
    return trace_bundle(
      kappa,
      1.0 + gamma,
      1.0 - gamma,
      stars,
      stars.shape[0],
      origin.x.value,
      origin.y.value,
      dTheta.x.value,
      dTheta.y.value,
      block,
      block.size,
      resolution.x.value,
      resolution.y.value)
    
    