from abc import ABC, abstractmethod
from typing import Self, Optional, List
from dataclasses import dataclass, field, fields
from copy import deepcopy
import re
import logging

import numpy as np
from astropy import units as u

from mirage.util import Dictify
from mirage.calc import KdTree
from mirage.model import SourcePlane

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Reducer(ABC):
  """
  Variation Function:
  ===================

  The variation function should change one variable in the parameter space a finite
  number of times. Each sub-reducer will be run with each iteration of the parameter
  space set up in the variation.

  The variation function may be used to change any property on the reducer. It cannot
  be used to change properties of the lens.
  """

  _parent_key: Optional[List[str]] = None
  name: Optional[str] = None
  variation: Optional[str] = None

  @abstractmethod
  def reduce(self, traced_rays: KdTree, source_plane: Optional[SourcePlane]):
    """
    Apply the reducer to the specified set of rays.

    This method should accumulate the outcome of the reduction
    as internal state inside the reducer.
    """

  @abstractmethod
  def merge(self, other: Self) -> Self:
    """
    Accumulate the result of another reducer with the result
    inside this reducer.
    """

  @property
  @abstractmethod
  def output(self) -> Optional[object]:
    """
    Return the outcome of this reduction.
    """

  @classmethod
  def type_key(cls) -> str:
    """
    A key uniquely identifying this reducer.

    By default the reducer's class name is used. For most uses this is probably fine,
    but if a new key is needed, this method can be overwritten. in a subclass
    """
    return cls.__name__

  def materialize_all(self) -> List[Self]:
    if self.variation is None:
      return [self]
    return self._apply_variation()

  def _set_parent_key(self, parent_key: List[str]):
    self._parent_key = parent_key

  def _apply_variation(self):
    template = Dictify.to_dict(self)
    for regex, func in EXPR_REGEXES:
      matches = regex.match(self.variation)
      if matches:
        ret_arr = []
        all_groups = matches.groups()
        func_args = all_groups[1:]
        property_name = all_groups[0]
        for property_value in func(func_args):
          merged_dict = {**template, **{property_name: Dictify.to_dict(property_value)}}
          ret_arr.append(Dictify.from_dict(type(self), merged_dict))
        return ret_arr
    raise ValueError("Could not find regex match!")

  @property
  def key(self):
    key = self.type_key()
    if self.name:
      key = self.name
    if self._parent_key:
      return os.path.join(*self._parent_key, key)
    return key


EXPR_REGEXES = [
    (
        re.compile(
            r"(\w+) ?= ?linspace\(([0-9.e\-]+), ?([0-9.e\-]+), ?([0-9]+)\) ([\w]+)"
        ),
        lambda matches: u.Quantity(
            np.linspace(
                float(matches[0]), float(matches[1]), int(matches[2]), endpoint=True
            ),
            matches[3],
        ),
    ),
    (
        re.compile(r"(\w+) ?= ?\[([0-9.e\-]+):([0-9.e\-]+):([0-9]+)\] ([\w]+)"),
        lambda matches: u.Quantity(
            np.linspace(
                float(matches[0]), float(matches[1]), int(matches[2]), endpoint=True
            ),
            matches[3],
        ),
    ),
    (
        re.compile(
            r"(\w+) ?= ?logspace\(([0-9.e\-]+), ?([0-9.e\-]+), ?([0-9]+)\) ([\w]+)"
        ),
        lambda matches: u.Quantity(
            np.logspace(
                float(matches[0]), float(matches[1]), int(matches[2]), endpoint=True
            ),
            matches[3],
        ),
    ),
]
