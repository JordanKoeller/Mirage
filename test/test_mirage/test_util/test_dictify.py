from abc import ABC, abstractmethod
from datetime import datetime
from unittest import TestCase
from typing import List, Dict
from dataclasses import dataclass

from astropy import units as u
from astropy.cosmology import Cosmology, WMAP7

from mirage.util import Dictify, DelegateRegistry, Vec2D, PolarVec
from mirage.calc.reducers import LightCurvesReducer


class TestJsonableMixin(TestCase):

  def testToPascalCase(self):
    def assertPascal(string: str, expected: str):
      self.assertEqual(Dictify._to_pascal_case(string), expected)

    assertPascal("lowercase", "Lowercase")
    assertPascal("some_field", "SomeField")
    assertPascal("some__field", "SomeField")
    assertPascal("_some_field", "SomeField")
    assertPascal("__some_field", "SomeField")
    assertPascal("some_field_", "SomeField")
    assertPascal("some_field___", "SomeField")
    assertPascal("some_numeric_0_field", "SomeNumeric0Field")
    assertPascal("some_numeric_0_field", "SomeNumeric0Field")

  def testDictifyValue_primitives_success(self):
    self.assertEqual(Dictify.to_dict(45), 45)
    self.assertEqual(Dictify.to_dict("some string"), "some string")
    self.assertEqual(Dictify.to_dict(None), None)
    self.assertEqual(Dictify.to_dict(True), True)
    self.assertEqual(Dictify.to_dict(3.14), 3.14)
    timestamp = datetime.now()
    self.assertEqual(Dictify.to_dict(timestamp), str(timestamp))

  def testToDict_allPrimitives_success(self):
    sdc = SimpleTestDataclass(23, "abcdefg", [1, 2, 3])
    expected = {"SomeInt": 23, "SomeStr": "abcdefg", "SomeList": [1, 2, 3]}
    self.assertDictEqual(Dictify.to_dict(sdc), expected)

  def testToDict_recursiveDataclass_success(self):
    sdc = SimpleTestDataclass(23, "abcdefg", [1, 2, 3])
    cdc = ComplexTestDataclass("some-field", sdc, {"some_field": 123, "k2": 234})
    expected = {
        "SomeField": "some-field",
        "SubInstance": {"SomeInt": 23, "SomeStr": "abcdefg", "SomeList": [1, 2, 3]},
        "SubDict": {"some_field": 123, "k2": 234},
    }
    self.assertDictEqual(Dictify.to_dict(cdc), expected)

  def testToDict_abstractMember_attachesDelegateNameToKey(self):
    dc = DataclassWithAbstractMember(
        some_abstract_type=SomeSubclass("salutations"),
        some_other_value="some other value",
    )

    expected = {
        "SomeAbstractType_SomeSubclass": {
            "PreferredGreeting": "salutations",
        },
        "SomeOtherValue": "some other value",
    }
    self.assertDictEqual(Dictify.to_dict(dc), expected)

  def testFromDict_noRecursiveStructure_success(self):
    dc = SimpleTestDataclass(12, "some str", [1, 2, 3])
    serialized = Dictify.to_dict(dc)

    deserialized = Dictify.from_dict(SimpleTestDataclass, serialized)
    self.assertEqual(dc, deserialized)

  def testFromDict_withDataclassField_success(self):
    sdc = SimpleTestDataclass(23, "abcdefg", [1, 2, 3])
    cdc = ComplexTestDataclass("some-field", sdc, {"some_field": 123, "k2": 234})
    serialized = Dictify.to_dict(cdc)

    deserialized = Dictify.from_dict(ComplexTestDataclass, serialized)
    self.assertEqual(cdc, deserialized)

  def testFromDict_withAbstractField_success(self):
    dc = DataclassWithAbstractMember(
        some_abstract_type=SomeSubclass("salutations"),
        some_other_value="some other value",
    )

    serialized = Dictify.to_dict(dc)

    deserialized = Dictify.from_dict(DataclassWithAbstractMember, serialized)
    self.assertEqual(deserialized, dc)

  def testToDict_withQuantity_success(self):
    dc = DataclassWithSpecials(
        3.2 * u.m, WMAP7, Vec2D(3.2, 3.4, u.km), PolarVec(3 * u.m, 0.4 * u.arcsec)
    )

    serialized = Dictify.to_dict(dc)

    expected = {
        "Q": [3.2, "m"],
        "C": "WMAP7",
        "V": [3.2, 3.4, "km"],
        "P": {"R": [3, "m"], "Theta": [0.4, "arcsec"]},
    }

    self.assertDictEqual(serialized, expected)

  def testToDict_typeWithList_success(self):
    elem = TestType(1, [SimpleType(2, "ASDF"), SimpleType(3, "QWERTY")])

    serialized = Dictify.to_dict(elem)

    expected = {
        "SomeValue": 1,
        "SomeList": [
            {"SomeInt": 2, "SomeStr": "ASDF"},
            {"SomeInt": 3, "SomeStr": "QWERTY"},
        ],
    }

    self.assertDictEqual(serialized, expected)

  def testFromDict_typeWithList_success(self):
    serialized = {
        "SomeValue": 1,
        "SomeList": [
            {"SomeInt": 2, "SomeStr": "ASDF"},
            {"SomeInt": 3, "SomeStr": "QWERTY"},
        ],
    }

    expected = TestType(1, [SimpleType(2, "ASDF"), SimpleType(3, "QWERTY")])

    actual = Dictify.from_dict(TestType, serialized)

    self.assertEqual(actual, expected)

  def testToDict_abstractList_attachesConcreteTypeToDictKeys(self):
    elem = DataclassWithAbstractList(
        abstract_elems=[
            SomeSubclass("hello"),
            SomeSubclass2("hola", "partner"),
        ],
        some_other_value="abc123",
    )
    expected = {
        "SomeOtherValue": "abc123",
        "AbstractElems": [
            {"SomeSubclass": {"PreferredGreeting": "hello"}},
            {"SomeSubclass2": {"PreferredGreeting": "hola", "Extra": "partner"}},
        ],
    }
    actual = Dictify.to_dict(elem)
    self.assertDictEqual(expected, actual)

  def testToDict_abstractListOnlyOneElem_attachesConcreteTypeToDictKeys(self):
    elem = DataclassWithAbstractList(
        abstract_elems=[
            SomeSubclass("hello"),
        ],
        some_other_value="abc123",
    )
    expected = {
        "SomeOtherValue": "abc123",
        "AbstractElems": [
            {"SomeSubclass": {"PreferredGreeting": "hello"}},
        ],
    }
    actual = Dictify.to_dict(elem)
    self.assertDictEqual(expected, actual)

  def testFromDict_lightCurvesReducer_success(self):
    dict_repr = {
        "Radius": [1, "uas"],
        "Resolution": [10, "1/uas"],
        "NumCurves": 10,
        "Seed": 12,
    }
    expected = LightCurvesReducer(
        radius=1 * u.uas,
        resolution=10 / u.uas,
        num_curves=10,
        seed=12,
    )
    actual = Dictify.from_dict(LightCurvesReducer, dict_repr)
    self.assertEqual(expected, actual)


@dataclass
class SimpleType:
  some_int: int
  some_str: str


@dataclass
class TestType:
  some_value: int
  some_list: List[SimpleType]


@dataclass
class SimpleTestDataclass:
  some_int: int
  some_str: str
  some_list: list


@dataclass
class ComplexTestDataclass:
  some_field: str
  sub_instance: SimpleTestDataclass
  sub_dict: Dict[str, int]


@dataclass
class DataclassWithSpecials:
  q: u.Quantity
  c: Cosmology
  v: Vec2D
  p: PolarVec


class SomeSuperclass(ABC):

  @abstractmethod
  def say_hello(self):
    pass


@dataclass
@DelegateRegistry.register
class SomeSubclass(SomeSuperclass):
  preferred_greeting: str

  def say_hello(self):
    return self.preferred_greeting


@dataclass
@DelegateRegistry.register
class SomeSubclass2(SomeSuperclass):
  preferred_greeting: str
  extra: str

  def say_hello(self):
    return self.preferred_greeting


@dataclass
class DataclassWithAbstractMember:
  some_abstract_type: SomeSuperclass
  some_other_value: str


@dataclass
class DataclassWithAbstractList:
  abstract_elems: List[SomeSuperclass]
  some_other_value: str
