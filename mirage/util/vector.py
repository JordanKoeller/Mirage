from typing import Union, Optional, Self, Dict, Any, List
from dataclasses import dataclass

from astropy import units as u
from astropy.coordinates import BaseRepresentation, CartesianRepresentation
import numpy as np

from .dictify import DictifyMixin, Dictify


class Vec2D(BaseRepresentation, DictifyMixin):
  """
  Two-dimensional coordinate vector
  """

  attr_classes = {
      "x": u.Quantity,
      "y": u.Quantity,
  }

  def __init__(
      self,
      x: Union[float, u.Quantity],
      y: Union[float, u.Quantity],
      unit: Optional[Union[str, u.Unit]] = None,
  ):
    if type(x) != type(y):
      raise ValueError(
          f"X and Y must both be floats or both be Quantities, "
          f"but found types {type(x)} and {type(y)}."
      )
    if isinstance(x, u.Quantity) and isinstance(y, u.Quantity):
      # Case: Both are quantities. unit may or may not be present
      if not x.isscalar or not y.isscalar:
        raise ValueError(
            f"When constructing Vec2D from Quantities, both quantities must be scalar but "
            f"found Quantities with shapes ({x.shape}, {y.shape})"
        )
      try:
        y = y.to(x.unit, copy=True)
      except:
        raise ValueError(
            f"Could not convert y value in units '{y.unit}' into x units of '{x.unit}'"
        )
      if unit:
        x = x.to(unit)
        y = y.to(unit)
      super().__init__(x, y, copy=True)
    else:
      # Case: Both are floats. u.Unit passed in as third parameter
      if unit is None:
        raise ValueError(
            "u.Unit must be specified when construct a Vec2D if x and y are passed in as floats"
        )
      if isinstance(unit, str):
        unit = u.Unit(unit)
      super().__init__(x * unit, y * unit, copy=True)

  @classmethod
  def unitless(cls, x: float, y: float):
    return cls(x, y, "")

  @classmethod
  def from_dict(cls, dict_obj: Dict[str, Any]) -> Self:
    x, y, unit = dict_obj
    return cls(float(x), float(y), unit)

  def to_dict(self) -> List[Any]:
    return [self.x.value, self.y.value, self.unit.to_string()]

  @classmethod
  def zero_vector(cls, unit: Union[str, u.Unit]) -> Self:
    return cls(0, 0, unit)

  @classmethod
  def from_cartesian(cls, cartesian: CartesianRepresentation):
    return Vec2D(cartesian.x.value, cartesian.y.value, cartesian.x.unit)

  def to_cartesian(self):
    return CartesianRepresentation(self.x, self.y, 0 * self.x.unit)

  def unit_vectors(self):
    unit_zero = 0 * self.x.unit
    return {
        "x": CartesianRepresentation(self.x, unit_zero, unit_zero),
        "y": CartesianRepresentation(unit_zero, self.y, unit_zero),
    }

  @property
  def unit(self) -> u.Unit:
    return self.x.unit

  def to(self, unit: Union[str, u.Unit]) -> Self:
    return Vec2D(self.x.to(unit), self.y.to(unit))

  @property
  def magnitude(self) -> u.Quantity:
    return np.sqrt(self.x * self.x + self.y * self.y)

  @property
  def direction(self) -> Self:
    """
    Get a unit vector pointing in the same direction as self
    """
    return self / self.magnitude

  def mul(self, other: Self) -> Self:
    return Vec2D(self.x * other.x, self.y * other.y)

  def div(self, other: Self) -> Self:
    return Vec2D(self.x / other.x, self.y / other.y)

  @property
  def max_dim(self) -> u.Quantity:
    """
    Returns the larger dimension of (x, y)
    """
    if self.x > self.y:
      return self.x
    return self.y

  def __str__(self):
    return "<%.3f, %.3f %s>" % (self.x.value, self.y.value, str(self.unit))

  def __repr__(self):
    return str(self)


class PolarVec(BaseRepresentation, DictifyMixin):
  """
  Two dimensional polar coordinate (r, theta)
  """

  attr_classes = {
      "r": u.Quantity,
      "theta": u.Quantity,
  }

  def __init__(self, r: u.Quantity, theta: u.Quantity):
    try:
      theta.to("arcsec")
    except:
      raise ValueError(
          f"`theta` must be some type of angle, but found units {theta.unit}"
      )

    super().__init__(r, theta, copy=True)

  @classmethod
  def from_dict(cls, dict_obj: Dict[str, Any]) -> Self:
    return PolarVec(
        Dictify.from_dict(u.Quantity, dict_obj["R"]),
        Dictify.from_dict(u.Quantity, dict_obj["Theta"]),
    )

  def to_dict(self) -> Dict[str, Any]:
    return {"R": Dictify.to_dict(self.r), "Theta": Dictify.to_dict(self.theta)}

  @classmethod
  def zero_vector(cls, unit: Union[str, u.Unit]) -> Self:
    if isinstance(unit, str):
      unit = u.Unit(unit)
    return cls(0 * unit, 0 * u.rad)

  @classmethod
  def from_cartesian(cls, cartesian: CartesianRepresentation):
    r_value = cartesian.norm().value
    unit_vector = cartesian / r_value
    theta = np.arctan2(unit_vector.y.value, unit_vector.x.value)
    return PolarVec(r_value * cartesian.x.unit, u.Quantity(theta, "rad"))

  def to_cartesian(self):
    theta = self.theta.to("rad").value
    return CartesianRepresentation(
        self.r * np.cos(theta), self.r * np.sin(theta), 0 * self.unit
    )

  def unit_vectors(self):
    unit_zero = 0 * self.unit
    theta = self.theta.to("rad").value
    return {
        "r": CartesianRepresentation(
            np.cos(theta) * self.unit, np.sin(theta) * self.unit, unit_zero
        ),
        "theta": CartesianRepresentation(
            -np.sin(theta) * self.unit, np.cos(theta) * self.unit, unit_zero
        ),
    }

  @property
  def unit(self):
    return self.r.unit


@dataclass
class Index2D:
  x: int
  y: int

  def __pre_init__(self):
    if self.x < 0:
      raise ValueError(f"Negative x index of {self.x} is invalid")
    if self.y < 0:
      raise ValueError(f"Negative index of {self.y} is invalid")

  def array(self) -> List[int]:
    return [self.x, self.y]
