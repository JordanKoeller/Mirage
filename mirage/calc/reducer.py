from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
import logging


from mirage.calc import KdTree

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Reducer(ABC):
    name: str

    @abstractmethod
    def reduce(self, traced_rays: KdTree):
        """
        Apply the reducer to the specified set of rays.

        This method should accumulate the outcome of the reduction
        as internal state inside the reducer.
        """

    @abstractmethod
    def merge(self, other: "Reducer") -> "Reducer":
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

    @property
    def has_output(self) -> bool:
        return self.output is not None

    @abstractmethod
    def set_output(self, output: object):
        """
        Explicitly sets the output of this reducer. Used to reconstruct the
        populated reducer while deserializing.
        """

    def initialize(self, simulation: "mirage.sim.Simulation"):
        """
        Optional method used to finish initializing this Reducer, giving it
        an opportunity to gather any properties needed from the larger
        Simulation object. Note that the `Simulation` passed in is a
        throwaway copy. Any mutations to the Simulation will not be reflected
        outside of this method's context.
        """
        pass
