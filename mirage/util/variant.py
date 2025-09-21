"""
Variance provides a structure that allows for wildcard substitution in

Dictify representations of objects.

If a "Variants" key is present in a yaml or json doc processed by the dictify
module it is interpreted before the rest of the object, and any generated
substitutions are specified.

Variants can be used to expand a templated object out to multiple versions of the 
object with a specific parameter (or parameters) tweaked on each version.

Variants should be specified in a special reserved "Variants" key in the
dict, with a value type of list[Variant]
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any
from uuid import uuid4
from functools import cached_property


import numpy as np

from .delegate_registry import DelegateRegistry

class EndBehavior(Enum):
    FIXED = "FIXED"
    REPEAT = "REPEAT"
    MIRROR = "MIRROR"

@dataclass(frozen=True, kw_only=True)
class Variant(ABC):
    """
    Base class of all variants. 

    Implementors should implement the get_values() abstract method.

    All variants must support the following fields:

    name: str - A unique name for the variant. This is used to match substitutions.
    tag: str - A human-readable tag that can be used to group variants. Variants
               with the same tag will change together. Variants with different
               tags will change separately, with the cartesian product of all
               possible values generated. A unique tag is used for each variant
               if not specified.
    end_behavior: EndBehavior - What to do if two variants share the same tag
               but produce a different number of values.
    """
    name: str
    tag: str = field(default_factory=lambda: str(uuid4()))
    end_behavior: EndBehavior = EndBehavior.FIXED

    @abstractmethod
    def get_values(self) -> list:
        """
        Applies the variant and returns a list of all the generated values.
        """

    @cached_property
    def _values(self):
        return self.get_values()

    def __len__(self) -> int:
        return len(self._values)

    def get_value(self, index: int) -> Any:
        if index < len(self._values):
            return self._values[index]
        match self.end_behavior:
            case EndBehavior.FIXED:
                return self._values[-1]
            case EndBehavior.REPEAT:
                return self._values[index % len(self._values)]
            case EndBehavior.MIRROR:
                tooth = self._values[:-1] + self._values[1:][::-1]
                return tooth[index % len(tooth)]




@DelegateRegistry.register
@dataclass(frozen=True, kw_only=True)
class LinspaceVariant(Variant):
    """
    Variant that generates linearly spaced values, using the np.linspace function.
    """
    start: float
    stop: float
    num_points: int

    def get_values(self) -> list:
        return np.linspace(self.start, self.stop, self.num_points, endpoint=True).tolist()

@DelegateRegistry.register
@dataclass(frozen=True, kw_only=True)
class LogspaceVariant(Variant):
    """
    Variant that generates logarithmically spaced values, using the np.logspace function.
    """
    start: float
    stop: float
    num_points: int

    def get_values(self) -> list:
        return np.logspace(self.start, self.stop, self.num_points, endpoint=True).tolist()

