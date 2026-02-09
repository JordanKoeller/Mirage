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
import copy
import logging
from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, Type, TypeVar, Iterator, Optional
from uuid import uuid4
from functools import cached_property
from frozendict import frozendict


import numpy as np

from .delegate_registry import DelegateRegistry
from .dictify import Dictify

logger = logging.getLogger(__name__)
T = TypeVar("T")

class EndBehavior(Enum):
    FIXED = "FIXED"
    REPEAT = "REPEAT"
    MIRROR = "MIRROR"

class VariantKey:
    def __init__(self, **keys: dict[str, Any]) -> None:
        self._keys = frozendict(keys)

    def matches(self, key: dict[str, Any]) -> bool:
        for k, v in key.items():
            if k not in self._keys:
                raise ValueError(f"Unrecognized variance name: {k}")
            if callable(v):
                if not v(self._keys[k]):
                    return False
            if isinstance(v, slice):
                value = self._keys[k]
                if not (v.start < value and value <= v.stop):
                    return False
            if self._keys[k] != v:
                return False
        return True

    def __str__(self) -> str:
        return "VariantKey(" + ",".join(f"{k}={v}" for k, v in self._keys.items()) + ")"

    def __repr__(self) -> str:
        return str(self)

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        if type(self) != type(other):
            return False
        return self._keys == other._keys


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

@DelegateRegistry.register
@dataclass(frozen=True, kw_only=True)
class ListVariant(Variant):
    """
    Variant that returns a list of value literals.
    """
    values: list[Any]

    def get_values(self) -> list:
        return values


class ObjVariants(Generic[T]):
    """
    Encapsulates variants of an object produced by an object template + variance.
    """
    
    def __init__(self, variants: list[Variant], objs: dict[VariantKey, T], template: dict[str, Any] | None = None) -> None:
        self._variants = {v.name: v for v in variants}
        self._objs = {str(k): v for k, v in objs.items()}
        self._keys = {str(k): k for k in objs}
        self._template = template

    @classmethod
    def from_single_variant(cls, obj: T) -> 'ObjVariants[T]':
        return cls([], {VariantKey(): obj}, Dictify.to_dict(obj))

    @property
    def klass(self) -> Type[object]:
        for k in self._objs:
            return type(self._objs[k])
        raise ValueError("Could not infer object type")

    def to_dict(self) -> dict[str, Any]:
        return self._template

    def get(self, key: Any = None, **kwargs) -> T | list[T] | None:
        """
        Returns single object if a single key is provided, or list of objects
        if slicing.

        This method can be called either with a single key object, or with key-value pairs as kwargs

        If calling with a single key, the key may be:
          A VariantKey object
          A dictionary object

        Value Matching:
          If called with a dictionary or kwargs, the values should be:
            + a value that equals the variant
            + A slice object that equals a range of values. Note that the 'step'
              of a slice is interpreted as how many matches to include. For
              example, slice [0:10:1] will match all variants with value between
              0 and 10. Slice [0:10:2] will match every other variant with value
              between 0 and 10. Slice [0:10:3] will match every third variant, etc.
              Fractional "step"s will throw an error.
            + A Callable[Any] -> bool, where the argument is a value, and should
              return a boolean if the variant should be selected.

        NOTE: If a VariantKey is provided, or only strict equality matches are
        used, a single object is returned. Otherwise, a list is returned.

        Examples:
          v = obj_variants.get(some_variant_key)
          v = obj_variants.get({"key": v1, "key2": v2})
          v = obj_variants.get(key=v1, key2=v2)
        """
        if key and kwargs:
            raise ValueError("Cannot specify both a key and kwargs")
        if kwargs:
            return self.get(kwargs)
        if isinstance(key, VariantKey):
            return self._objs.get(str(key), None)
        ret = {}
        is_multi_response = False
        for variant_key, variant in self._objs:
            if variant_key.matches(key):
                ret[variant_key] = variant
        for k, v in key.items():
            if callable(v) or isinstance(v, slice):
                is_multi_response = True
        if is_multi_response:
            return ret
        if len(ret) == 0:
            return None
        if len(ret) != 1:
            return ValueError(f"Ambiguous matches: {list(ret.keys())}")
        for k in ret:
            return ret[k]

    def variants(self) -> list[T]:
        return [self._objs[k] for k in self._objs]

    @property
    def variant_keys(self) -> list[VariantKey]:
        return [self._keys[k] for k in self._keys]

    def __len__(self) -> int:
        return len(self._objs)

    def __iter__(self) -> Iterator[tuple[VariantKey, T]]:
        return iter(self._objs.items())

    def __getitem__(self, key: object) -> T:
        if not isinstance(key, VariantKey):
            raise ValueError(f"key must be of type VariantKey, but got {type(key)}")
        return self._objs[str(key)]

    def __eq__(self, other: object) -> bool:
        if type(self) != type(other):
            return False
        return self._template == other._template


class VariantDictify:
    """
    Drop-in replacement for Dictify that will process any variants present and
    return all the resultant dictified objects.
    """

    @staticmethod
    def from_dict(
        klass: Type[T],
        dict_obj: dict[str, Any],
        allow_custom_serializer: bool = True,
        variant_container = None,
    ) -> Optional[ObjVariants]:
        if "Variants" not in dict_obj:
            logger.debug("No Variant. Pass-through to regular Dictify.")
            obj = Dictify.from_dict(klass, dict_obj, allow_custom_serializer)
            if obj:
                return (variant_container or ObjVariants).from_single_variant(obj)
            return None
        variants = []
        logger.debug("Found variants. Parsing.")
        for obj in dict_obj["Variants"]:
            parsed = Dictify.from_dict(Variant, obj, allow_custom_serializer) 
            if parsed:
                variants.append(parsed)
        if len(variants) == 0:
            return None
        original_dict_obj = copy.deepcopy(dict_obj)
        del dict_obj["Variants"]
        objs = {}
        for substitutions, inds in VariantDictify._get_substitutions(variants):
            dict_obj_copy = copy.deepcopy(dict_obj)
            VariantDictify._apply_substitutions(dict_obj_copy, substitutions)
            key = VariantKey(**inds)
            objs[key] = Dictify.from_dict(klass, dict_obj_copy, allow_custom_serializer)
            logger.debug(f"Created Variant with {key=}")
        return (variant_container or ObjVariants)(variants, objs, original_dict_obj)

    @staticmethod
    def _get_substitutions(variants: list[Variant]) -> list[tuple[dict[str, Any], dict[str, int]]]:
        """
        Gives a list of substitution objects based on the values produced by the set of variants.

        The elements of the returned list consist of key-value pairs, where each key maps to a
        value that should be substituted in.
        """
        substitutions = []
        tags_counter = _TagsCounter(variants)
        while True:
            substitution_set = {}
            tag_set = {}
            tag_inds = tags_counter.get_tag_indices()
            for variant in variants:
                substitution_set[variant.name] = variant.get_value(tag_inds[variant.tag])
                tag_set[variant.name] = tag_inds[variant.tag]
            substitutions.append((substitution_set, tag_set))
            if not tags_counter.increment():
                return substitutions

    @staticmethod
    def _apply_substitutions(dict_obj: Any, substitutions: dict[str, Any]):
        """
        Mutates dict_obj inplace with the provided substitutions.
        """
        ret = {}
        if isinstance(dict_obj, dict):
            for k in dict_obj:
                if isinstance(dict_obj[k], (dict, list)):
                    VariantDictify._apply_substitutions(dict_obj[k], substitutions)
                if not isinstance(dict_obj[k], str):
                    continue
                for s in substitutions:
                    sub_str = "${" + s + "}"
                    if dict_obj[k] == sub_str:
                        dict_obj[k] = substitutions[s]
                    elif isinstance(dict_obj[k], str):
                        dict_obj[k] = dict_obj[k].replace(sub_str, str(substitutions[s]))
        elif isinstance(dict_obj, list):
            for i in range(len(dict_obj)):
                if isinstance(dict_obj[i], (dict, list)):
                    VariantDictify._apply_substitutions(dict_obj[i], substitutions)
                if not isinstance(dict_obj[i], str):
                    continue
                for s in substitutions:
                    sub_str = "${" + s + "}"
                    if dict_obj[i] == sub_str:
                        dict_obj[i] = substitutions[s]
                    elif isinstance(dict_obj[i], str):
                        dict_obj[i] = dict_obj[i].replace(sub_str, str(substitutions[s]))

class _TagsCounter:
    def __init__(self, variants: list[Variant]) -> None:
        self.tag_indices = {}
        self.tag_lengths = {}
        for variant in variants:
            self.tag_indices[variant.tag] = 0
            self.tag_lengths[variant.tag] = max(self.tag_lengths.get(variant.tag, 0), len(variant))
        self.tags = list(self.tag_lengths.keys())

    def increment(self) -> bool:
        for tag in self.tags:
            self.tag_indices[tag] += 1
            if self.tag_indices[tag] == self.tag_lengths[tag]:
                self.tag_indices[tag] = 0
            else:
                return True
        return False

    def get_tag_indices(self) -> dict[str, int]:
        return self.tag_indices
