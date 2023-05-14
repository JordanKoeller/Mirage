from abc import ABC, abstractmethod
from typing import Self, Optional

import numpy as np

from mirage.calc import KdTree
from mirage.model import SourcePlane


class Reducer(ABC):

    @abstractmethod
    def reduce(self, traced_rays: KdTree, source_plane: Optional[SourcePlane]):
        """
        Apply the reducer to the specified set of rays.

        This method should accumulate the outcome of the reduction
        as internal state inside the reducer.
        """

    @abstractmethod
    def merge(self, other: Self):
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
