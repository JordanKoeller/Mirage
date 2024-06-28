from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from math import pi

from astropy import units as u
from astropy import constants as const
from astropy.cosmology import Cosmology, WMAP7
import numpy as np

from mirage.util import Vec2D
from mirage.calc import RayTracer

from .quasar import Quasar
from .tracing_parameters import TracingParameters

"""
TODO: Clean up this abstraction.

It's really messy having non-hermetic parameters specified in LensingSystem
and then having others specified in subclass.

Right now we have no way to specify the StarfieldGenerator. Should that go in
here or in the Simulation? Higher cohesive approach feels like in here, but as
an optional parameter to support macrolensing situations?

Refactorings:
  Maybe move the abstract code to a delegated Lens class again? Then pass down
  the quasar / cosmology as needed?
"""


@dataclass(kw_only=True, frozen=True)
class LensingSystem(ABC):
    """
    Represents the full gravitatially lensed system (observer, lensing galaxy, plus quasar).

    The LensingSystem serves multiple roles in Mirage. These include:

    + Describing the lensing system and its core parameters
      (mass model, distance to lense, distance to quasar, einstein radius, etc.)
    + Producing a :class:`mirage.calc.TracingParameters` instance, used to simulate
      microlensing configurations.
    + Providing the lensing equation for the macrolensing scenario.

    """

    quasar: Quasar
    redshift: float
    cosmology: Cosmology = field(default_factory=lambda: WMAP7)

    def microtracing_parameters(self, position: Vec2D) -> TracingParameters:
        """
        Get tracing parameters around the specified location on the source plane.

        Args:

          + position (:class:`mirage.util.Vec2D`): The position through the lensing galaxy
              around which to simulate microlensing. Given in units of angle, typically `arcseconds`.

        Returns:

          + :class:`mirage.model.TracingParameters`
        """
        raise NotImplementedError(
            f"LensingSystem delegate {type(self).__name__} does not suport "
            f"microlensing ray-tracing"
        )

    def get_ray_tracer(self) -> RayTracer:
        """
        Returns a :class:`RayTracer` instance that can be used to trace a
        bundle of rays around this lens.

        Note that this is only really used for _macrolensing_ simulation
        (tracing caused by the mass of the entire galaxy). If the model does
        not support macrolensing, this method should return None instead.
        """
        raise NotImplementedError(
            f"LensingSystem delegate {type(self).__name__} does not suport "
            f"macrolensing ray-tracing"
        )

    @property
    @abstractmethod
    def einstein_radius(self) -> u.Quantity:
        """
        Computes the einstein radius for the lensing system.
        """

    @abstractmethod
    def magnification_coefficient(self, p: Vec2D) -> float:
        """
        Computes the magnification coefficient of the LensingSystem
        at a particular location
        """

    @property
    def xi_0(self) -> u.Unit:
        """
        Impact parameter (distance) of a 1 M_sun point lens
        """
        return u.def_unit(
            "xi_0",
            np.sqrt(
                4
                * const.G
                * u.Quantity(1, "solMass")
                * self.effective_distance
                / const.c
                / const.c
            ).to("m"),
        )

    @property
    def theta_0(self) -> u.Unit:
        """
        Angle of an einstein radius for a 1 M_sun point mass lens
        """
        xi_0 = 1.0 * self.xi_0
        factor = xi_0.to("m") / self.lens_distance.to("m")
        return u.def_unit("theta_0", u.Quantity(factor.value, "rad"))

    @property
    def r_g(self) -> u.Unit:
        """
        Gravitational radius of the Quasar, expressed as an angle on the sky
        """
        return u.def_unit(
            "r_g",
            u.Quantity(
                (
                    2
                    * const.G
                    * self.quasar.mass
                    / const.c
                    / const.c
                    / self.source_distance
                )
                .to("")
                .value,
                "rad",
            ),
        )

    @property
    def lens_distance(self) -> u.Quantity:
        return self.cosmology.angular_diameter_distance(self.redshift)

    @property
    def source_distance(self) -> u.Quantity:
        return self.cosmology.angular_diameter_distance(self.quasar.redshift)

    @property
    def effective_distance(self) -> u.Quantity:
        """
        Returns the effective distance of the lens.

        Effective Distance is defined by the equation (d_L * d_LS / d_S)
        """
        d_l = self.cosmology.angular_diameter_distance(self.redshift)
        d_s = self.cosmology.angular_diameter_distance(self.quasar.redshift)
        d_ls = self.cosmology.angular_diameter_distance_z1z2(
            self.redshift, self.quasar.redshift
        )
        return d_ls * d_l / d_s

    @property
    def critical_density(self) -> u.Quantity:
        """
        Computes the critical density for the lensing system.

        Returns:

          + u.Quantity: The critical density, in units of solMass / lyr^2.
        """
        density = (
            const.c * const.c / (4 * pi * const.G * self.effective_distance)
        )
        return density.to("solMass / lyr2")

    def special_units(self):
        """
        Returns a context-object with special lens-specific units.
        """
        return u.add_enabled_units(
            [
                self.theta_0,
                self.xi_0,
                self.einstein_radius,
                self.r_g,
            ]
        )
