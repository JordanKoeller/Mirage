import numpy as np
from astropy import units as u

from mirage.util import Vec2D, PixelRegion
from mirage.calc.fast_tree import FastTree


class FastKdTree:
  def __init__(self, data: u.Quantity, region: PixelRegion, leaf_size: int = 64):
    self.unit = data.unit
    self.tree = FastTree(data.value, leaf_size)
    self.region = region

  def query_rays(self, query_pos: Vec2D, radius: u.Quantity) -> u.Quantity:
    raise NotImplementedError("Yat")

  def query_count(self, x, y, radius, parity=0) -> int:
    return self.tree.points_in_circle(x, y, radius, parity)

  def batch_query_count(
    self, query_points: u.Quantity, radius: u.Quantity, parity: int = 0
  ) -> np.ndarray:
    return self.tree.batch_points_in_circle(
      query_points.to(self.unit).value, radius.to(self.unit).value, parity
    )

  def query_indices(
    self, query_pos: Vec2D, radius: u.Quantity, parity: int
  ) -> np.ndarray:
    """
    Returns the indices of active rays in (x, y) coordinate pairs.
    """
    query_pos = query_pos.to(self.unit)
    radius = radius.to(self.unit)
    tree_local_inds = self.tree.query_rays(
      query_pos.x.value, query_pos.y.value, radius.value, parity
    )
    return self.region.unravel(tree_local_inds)
