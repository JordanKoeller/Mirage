from abc import ABC, abstractmethod
from typing import Optional, List
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

  name: str

  @abstractmethod
  def reduce(self, traced_rays: KdTree, source_plane: Optional[SourcePlane]):
    """
    Apply the reducer to the specified set of rays.

    This method should accumulate the outcome of the reduction
    as internal state inside the reducer.
    """

  @abstractmethod
  def merge(self, other: 'Reducer') -> 'Reducer':
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

  @abstractmethod
  def set_output(self, output: object):
    """
    Explicitly sets the output of this reducer. Used to reconstruct the
    populated reducer while deserializing.
    """
