from typing import Self, Optional, List, Dict
from dataclasses import dataclass, field

from mirage.calc import Reducer, KdTree
from mirage.calc.reducer_funcs import populate_magmap, populate_lightcurve
from mirage.util import Vec2D, PixelRegion, DelegateRegistry, Region
from mirage.model import SourcePlane
from mirage_ext import reduce_lensed_image, reduce_magmap

import numpy as np
from astropy import units as u


@dataclass
class ReducerTree:
  """
  Tree representation of reducers.

  Before reducing a simulation, a ReducerTree is constructed and the ReducerTree
  is ultimately what is applied to the reducer.

  During reduction, each node is visited and applied to the simulation.
  """

  node_key: str
  children: Dict[str, Reducer] = field(default_factory=dict)
  value: Optional[Reducer] = None

  def add_child(self, reducer: Reducer):
    self.children[reducer.key] = reducer
    reducer._set_parent_key(self.node_key)
