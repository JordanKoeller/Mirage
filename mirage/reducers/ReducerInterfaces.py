from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from typing import TypeVar, Generic, Iterator
from dataclasses import dataclass

import numpy as np


Q = TypeVar('Q') # QueryId
R = TypeVar('R') # Result type. Usually a long or a double.

@dataclass(frozen=True)
class RayQuery(Generic[Q, R]):
    """
    Abstract class for one particular call into the kD tree.
    """
    identifier: Q
    x: float
    y: float
    radius: float

    def reduce_ray(self, ray: np.ndarray) -> None:
        """
        Intake a particular ray to add to this accumulator's internal state.
        """
        raise NotImplementedError(
            "reduce_ray is an abstract method. Must be implemented by a subclass of RayQuery.")

    def get_result(self) -> R:
        """
        Returned the accumulated result of the query represented by this RayQuery instance.
        """
        raise NotImplementedError(
            "get_result is an abstract method. Must be implemented by a subclass of RayQuery.")

class QueryReducer(Generic[Q, R]):
    """
    Abstract class for performing a query and collecting the results.

    An instance of this type is what is returned when a job is completed.
    """

    def merge(self, other: QueryReducer) -> QueryReducer:
        """
        Merge this reducer's result with the result from another.
        """
        pass

    def query_points(self) -> Iterator[RayQuery[Q, R]]:
        """
        Returns an iterator, where each element is a tuple.

        The first element of each tuple is a unique ID for that query point.
        It should be passed into the `set_query_magnitude` method to save the
        result of that query.

        The second element of each tuple is the query's information as a
        (location, radius) tuple.
        """
        pass

    def save_value(self, value_id: Q, value: R) -> None:
        """
        Given a query location's id and value, save the result into the reducer's
        internal storage.
        """
        pass

    def clone_empty(self) -> QueryReducer[Q, R]:
        """
        Provides a copy of the QueryReducer for sending to different workers
        """
        pass

    def value(self) -> np.ndarray:
        pass