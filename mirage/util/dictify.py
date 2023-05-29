"""
Example Dictify-serialized object.
I need to be able to specify what field, as well as the delegate's type.

Key names are always in PascalCase.

So the plan is for types that are abstract, I will encode their key name as <FieldName>_<DelegateType>
  That way I always know what type to instantiate.

At least for this first implementation, I'm only going to focus on primatives, @dataclass types, and then
  Also support for a few other types (Cosmology, scalar Quantity, etc) that I can't avoid.

```
Model_SingularIsothermalSphere:
  Redshift: 1.2
  VelocityDispersion: [1.234, "km/s"]
  StarFraction: 0.3
  Shear:
    R: [0.23, "km"]
    Theta: [1.2, "arcsec"]
  Ellipticity:
    R: [0.34, "km"]
    Theta: [2.3, "arcsec"]
  Cosmology: "WMAP7"
  Quasar:
    Redshift: 0.7
    Cosmology: "WMAP7"
```"""
from dataclasses import fields, Field, is_dataclass, dataclass
from datetime import date, datetime, time
from typing import Any, Dict, List, Type, TypeVar, Self, Callable, Generic, Union, Optional, get_args, get_origin
from abc import ABC, abstractmethod, abstractclassmethod
from inspect import isabstract, isclass
import logging
import json

from astropy import units as u

from .delegate_registry import DelegateRegistry

logger = logging.getLogger(__name__)

T = TypeVar(
    "T",
)


@dataclass(frozen=True, kw_only=True)
class CustomSerializer(Generic[T]):
  """
  Encapsulate custom dictify behavior for an external type.

  This lets you add custom behavior to the dictify system that you don't own. For example,
  a type from a standard library.

  To use, construct a :class:`CustomSerializer` instance, then register it with the
  :class:`Dictify` system using :func:`Dictify.register_serializer`.

  Args:

    + value_type (Type[T]): The type this seriailzer applies to.
    + to_dict (Callable[[T], Any]): Method to call to convert an instance of T to a dict.
    + from_dict (Callable[[Any], T]): Method to call to convert a dict to an instance of T.
  """

  value_type: Type[T]
  to_dict: Callable[[T], Any]
  from_dict: Callable[[Any], T]


class Dictify:
  __custom_serializers: List[CustomSerializer] = []

  @staticmethod
  def register_serializer(serializer: CustomSerializer[T]):
    """
    Register custom serializer behavior in the Dictify system.

    For more details, see the docs for :class:`CustomSerializer`.
    """
    Dictify.__custom_serializers.append(serializer)

  @staticmethod
  def to_dict(value: Any, type_as_key: bool = False) -> Any:
    """
    Converts an object into a representation that is JSON-compatible.

    Supports any object that is a python primitive, @dataclass objects,
      objects that inherit :class:`DictifyMixin`, and any object that has been
      registered with a :class:`CustomSerializer`.

    Args:

    + value (Any): The object to convert to a primitive representation.
    + type_as_key (bool): If true, sets the dict-representation of objects inside a wrapper dict,
                          with its key equal to its type's name.
    """
    if value is None:
      return None
    custom_serializer = Dictify._get_custom_serializer(value)
    if custom_serializer:
      ret = custom_serializer.to_dict(value)
      return Dictify._sanitize(ret)
    if isinstance(value, DictifyMixin):
      return Dictify._sanitize(value.to_dict())
    if isinstance(value, (int, float, str, bool)):
      return value
    if isinstance(value, (list, tuple)):
      type_names = [elem.__class__.__name__ for elem in value]
      values_list = [Dictify.to_dict(elem) for elem in value]
      if len(set(type_names)) > 1 or type_as_key:
        values_list = [{k: v} for k, v in zip(type_names, values_list)]
      return values_list
    if isinstance(value, dict):
      return Dictify._sanitize({k: Dictify.to_dict(v) for k, v in value.items()})
    if is_dataclass(value):
      return Dictify._sanitize(Dictify._dictify_dataclass(value))
    if isinstance(value, (datetime, time, date)):
      return str(value)
    raise ValueError(
        f"Encountered undictifiable value {value} of type {str(type(value))}"
    )

  @staticmethod
  def from_dict(klass: Type[T], dict_obj: Dict[str, Any]) -> Optional[T]:
    """
    Converts a dict into an instance of a @dataclass type.

    Args:

      + klass (Type): The Class definition to parse the dict into. Must be a @dataclass type.
      + dict_obj (Dict[str, Any]): The dict-representation of the object.

    Returns:

      + Any: An instance of the type specified by "klass"

    Raises:

      + ValueError: The passed in type was not a @dataclass type.
    """
    custom_serializer = Dictify._get_custom_serializer(klass)  # type: ignore
    if custom_serializer:
      return custom_serializer.from_dict(dict_obj)
    if isinstance(klass, DictifyMixin):
      return klass.from_dict(dict_obj)
    return Dictify._value_from_dict(klass, dict_obj)

  @staticmethod
  def _sanitize(value: Union[dict, list]) -> dict:
    """
    Sanitizes complex types, converting them to primitives.

    This is done by using the `json` library (converts to a json string, then back to a dict).
    This can probably be optimized.
    """
    return json.loads(json.dumps(value))

  @staticmethod
  def _value_from_dict(klass: Type[T], dictable_value: Any) -> Optional[T]:
    if isabstract(klass):
      raise ValueError(f"Cannot convert a dict to an abstract type {klass.__name__}")
    custom_serializer = Dictify._get_custom_serializer(klass)  # type: ignore
    if dictable_value is None:
      return None
    if get_origin(klass) is Union and type(None) in get_args(klass):
      klass = get_args(klass)[0]
    logger.debug(f"_value_from_dict: {klass} {dictable_value}")
    if custom_serializer:
      return custom_serializer.from_dict(dictable_value)
    if klass in (int, float, str, bool):
      return klass(dictable_value)  # type: ignore
    if Dictify._is_python_collection(klass):
      return Dictify._value_from_py_collection(klass, dictable_value)
      return dictable_value  # TODO: Properly handle lists and dicts
    if issubclass(klass, DictifyMixin):
      return klass.from_dict(dictable_value)  # type: ignore
    if is_dataclass(klass):
      return Dictify._dataclass_from_dict(klass, dictable_value)  # type: ignore
    raise ValueError(
        f"Could not construct a {klass.__name__} from value:\n{dictable_value}"
    )

  @staticmethod
  def _dataclass_from_dict(klass: Type[T], dict_obj: Dict[str, Any]) -> T:
    logger.debug(f"_dataclass_from_dict {str(klass)} | {str(dict_obj)}")
    field_map = {k.split("_")[0]: v for k, v in dict_obj.items()}
    subtype_map = {
        k.split("_")[0]: k.split("_")[1] for k in dict_obj if len(k.split("_")) == 2
    }
    constructor_args: Dict[str, Any] = {}
    expected_fields = {
        Dictify._to_pascal_case(f.name): f for f in fields(klass)  # type: ignore
    }
    for dict_name, field in expected_fields.items():
      custom_serializer = Dictify._get_custom_serializer(field.type)
      dict_value = field_map.get(dict_name, None)
      if custom_serializer:
        constructor_args[field.name] = custom_serializer.from_dict(dict_value)
      elif isabstract(field.type):  # Find its subtype by name and construct
        delegate_name = subtype_map[dict_name]
        subtype = DelegateRegistry.get_typedef(field.type, delegate_name)
        if subtype:
          constructor_args[field.name] = Dictify._value_from_dict(subtype, dict_value)
        else:
          raise ValueError(
              "Could not find registered delegate for supertype "
              f"{field.type.__name__} with name {delegate_name}"
          )
      else:
        constructor_args[field.name] = Dictify._value_from_dict(field.type, dict_value)
    return klass(**constructor_args)  # type: ignore

  @staticmethod
  def _get_custom_serializer(
      instance_or_type: Union[T, Type[T]]
  ) -> Optional[CustomSerializer[T]]:
    for ser in Dictify.__custom_serializers:
      if isclass(instance_or_type) and issubclass(instance_or_type, ser.value_type):
        return ser
      if isinstance(instance_or_type, ser.value_type):
        return ser
    return None

  @staticmethod
  def _is_python_collection(type_def: Type) -> bool:
    return (
        type_def in (list, dict)
        or str(type_def).startswith("typing.Dict")
        or str(type_def).startswith("typing.List")
    )

  @staticmethod
  def _value_from_py_collection(klass: Type[T], dictable_value: Any) -> Any:
    logger.debug(f"py_collection {str(klass)} | {str(dictable_value)}")
    if get_origin(klass) == list:
      inner_type = get_args(klass)[0]
      if isabstract(inner_type):
        # Case where we have a polymorphic list of Dataclass type.
        # Then we have elems of {"ConcreteTypeName": {args}}
        values: List[Any] = []
        for elem in dictable_value:
          concrete_type_name = list(elem.keys())[0]
          concrete_type = DelegateRegistry.get_typedef(inner_type, concrete_type_name)
          if concrete_type is not None:
            values.append(
                Dictify._value_from_dict(concrete_type, elem[concrete_type_name])
            )
          else:
            raise ValueError("Encountered polymorphic list with non-matching element")
        return values
      return [Dictify._value_from_dict(inner_type, elem) for elem in dictable_value]
    if isinstance(klass, Dict):
      k_type, v_type = get_args(klass)
      return {
          Dictify._value_from_dict(k_type, k): Dictify._value_from_dict(v_type, v)
          for k, v in dictable_value.items()
      }
    logger.warn(f"could not parse out python collection type {klass}")
    return dictable_value

  @staticmethod
  def _dictify_dataclass(obj: Any):
    """
    Convert any value to a jsonible value.

    If the conversion could not be done, raises a ValueError.
    """
    obj_fields = fields(obj)
    ret = {}
    for field in obj_fields:
      field_name = field.name
      field_value = getattr(obj, field_name, None)
      dict_key = Dictify._to_pascal_case(field_name)
      dict_value = None
      if isabstract(field.type) and DelegateRegistry.has_supertype(field.type):
        # Fields with a abstract-defined type have format "<FieldName>_<Type>"
        dict_key = f"{dict_key}_{field_value.__class__.__name__}"
      if get_origin(field.type) == list:
        inner_type = get_args(field.type)[0]
        if isabstract(inner_type) and DelegateRegistry.has_supertype(inner_type):
          dict_value = Dictify.to_dict(field_value, type_as_key=True)
      if dict_value is None:
        dict_value = Dictify.to_dict(field_value)
      if dict_value is not None:
        ret[dict_key] = dict_value
    return ret

  @staticmethod
  def _to_pascal_case(lower_underscore_string: str) -> str:
    ret = []
    for i in range(len(lower_underscore_string)):
      char = lower_underscore_string[i]
      if char == "_":
        pass  # Skip underscores. Don't add to resultant string.
      elif i > 0 and lower_underscore_string[i - 1] == "_":
        ret.append(char.upper())
      elif len(ret) == 0:
        ret.append(char.upper())
      else:
        ret.append(char)
    return "".join(ret)


class DictifyMixin(ABC):

  @abstractmethod
  def to_dict(self: Any) -> Union[Dict[str, Any], List[Any]]:
    """
    Convert self to a Dictionary representation
    """

  @classmethod
  @abstractmethod
  def from_dict(cls, dict_obj: Dict[str, Any]) -> Self:
    """
    Convert a dictionary representation to an instance of `cls`
    """
