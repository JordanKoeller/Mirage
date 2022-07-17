import numpy as np

from .ReducerInterfaces import RayQuery

from typing import TypeVar, Generic

Q = TypeVar('Q')

class MagnificationQuery(RayQuery[Q, np.int64]):

    def __init__(self, identifier: Q, x: float, y: float, radius: float):
        RayQuery.__init__(self, identifier, x, y, radius)
        self._count = 0

    def reduce_ray(self, ray: np.ndarray):
        self._count += 1
    
    def get_result(self) -> np.int64:
        return np.int64(self._count)
