from abc import ABC, abstractmethod
from typing import Self, Optional, List
from dataclasses import dataclass, field

import numpy as np

from mirage.calc import KdTree
from mirage.model import SourcePlane


@dataclass(kw_only=True)
class Reducer(ABC):
  _parent_key: Optional[List[str]] = None
  _name: Optional[str] = None

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

  def _set_parent_key(self, parent_key: List[str]):
    self._parent_key = parent_key

  @property
  def key(self):
    if self._name:
      return self._name
    type_key = self.type_key()
    if self._parent_key:
      return os.path.join(*self._parent_key, type_key)
    return type_key
