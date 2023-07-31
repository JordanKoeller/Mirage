from typing import Optional, Tuple

from scipy.spatial import cKDTree
import numpy as np
from astropy import units as u

from mirage.util import Vec2D

from mirage_ext import KiddoTree


class PyKdTree:

  def __init__(self, data: u.Quantity):
    major_sz = data.shape[0] * data.shape[1]
    self.data_shape = data.shape
    self.unit = data.unit
    self.data = np.reshape(data.value, (major_sz, self.data_shape[2]))  # original data
    self.tree = cKDTree(
        self.data[:, :2], compact_nodes=True, balanced_tree=True, leafsize=128
    )

  def query_rays(self, query_pos: Vec2D, radius: u.Quantity) -> u.Quantity:
    x, y, radius = self._query_primatives(query_pos, radius)
    flat_indices = np.array(self.tree.query_ball_point([x, y], radius), dtype=np.uint64)
    return u.Quantity(self.data[flat_indices], self.unit)

  def query_count(self, x, y, radius: float) -> int:
    # x, y, radius = self._query_primatives(query_pos, radius)
    return self.tree.query_ball_point([x, y], radius, return_length=True)

  def query_indices(self, query_pos: Vec2D, radius: u.Quantity) -> np.ndarray:
    x, y, radius = self._query_primatives(query_pos, radius)
    flat_indices = np.array(self.tree.query_ball_point([x, y], radius), dtype=np.uint64)
    indices: np.ndarray = np.ndarray((len(flat_indices), 2), dtype=np.uint64)
    indices[:, 0] = flat_indices // self.data_shape[1]
    indices[:, 1] = flat_indices % self.data_shape[1]
    return indices

  def _query_primatives(
      self, query_pos: Vec2D, radius: u.Quantity
  ) -> Tuple[float, float, float]:
    query_pos = query_pos.to(self.unit)
    radius = radius.to(self.unit)
    return query_pos.x.value, query_pos.y.value, radius.value


class RustKdTree:

  def __init__(self, data: u.Quantity):
    self.unit = data.unit
    self.tree = KiddoTree(data.value)

  def query_rays(self, query_pos: Vec2D, radius: u.Quantity) -> u.Quantity:
    query_pos = query_pos.to(self.unit)
    radius = radius.to(self.unit)
    rays = self.tree.query_rays(query_pos.x.value, query_pos.y.value, radius.value)
    return u.Quantity(rays, self.unit)

  def query_count(self, x, y, radius) -> int:
    return self.tree.query_count(x, y, radius)

  def query_indicies(self, query_pos: Vec2D, radius: u.Quantity) -> np.ndarray:
    query_pos = query_pos.to(self.unit)
    radius = radius.to(self.unit)
    return self.tree.query_indices(query_pos.x.value, query_pos.y.value, radius.value)
