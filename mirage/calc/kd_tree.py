from typing import Optional, Tuple

from scipy.spatial import cKDTree
import numpy as np
from astropy import units as u

from mirage.util import Vec2D

from mirage_ext import KdTree as RustKdTree


class PyKdTree:

  def __init__(self, data: u.Quantity):
    self.data_shape = (data.shape[0], data.shape[1])
    self.unit = data.unit
    sz = self.data_shape[0] * self.data_shape[1]
    self.data = np.reshape(data.value, (sz, 2))
    self.tree = cKDTree(self.data, leafsize=128)

  def query(self, query_pos: Vec2D, radius: u.Quantity) -> np.ndarray:
    query_pos = query_pos.to(self.unit)
    radius = radius.to(self.unit)
    query_pt = [query_pos.x.value, query_pos.y.value]
    flat_indices = np.array(self.tree.query_ball_point(query_pt, radius), dtype=int)
    buffer: np.ndarray = np.ndarray((len(flat_indices), 2), dtype=int)
    buffer[:, 0] = flat_indices // self.data_shape[1]
    buffer[:, 1] = flat_indices % self.data_shape[1]
    return buffer

  def query_count(self, query_x: float, query_y: float, radius: float) -> int:
    query_pt = [query_x, query_y]
    return self.tree.query_ball_point(query_pt, radius, return_length=True)


class KdTree:

  def __init__(self, data: u.Quantity):
    self.data_shape = (data.shape[0], data.shape[1])
    self.unit = data.unit
    sz = self.data_shape[0] * self.data_shape[1]
    self.data = np.reshape(data.value, (sz, 2))
    self.tree = RustKdTree(self.data, 128)

  def query(self, query_pos: Vec2D, radius: u.Quantity) -> np.ndarray:
    query_pos = query_pos.to(self.unit)
    radius = radius.to(self.unit).value
    query_pt = [query_pos.x.value, query_pos.y.value]
    flat_indices = np.array(
        self.tree.query_near(query_pt[0], query_pt[1], radius), dtype=int
    )
    buffer: np.ndarray = np.ndarray((len(flat_indices), 2), dtype=int)
    buffer[:, 0] = flat_indices // self.data_shape[1]
    buffer[:, 1] = flat_indices % self.data_shape[1]
    return buffer

  def query_count(self, query_x: float, query_y: float, radius: float) -> int:
    query_pt = [query_x, query_y]
    return self.tree.query_near_count(query_x, query_y, radius)
