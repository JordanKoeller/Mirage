from dataclasses import dataclass, field
from math import pi

from numpy import sin, cos, arctan2, sqrt

from astropy import units as u
from astropy.cosmology import Cosmology, WMAP7
from astropy import constants as const

from mirage.model import LensingSystem, TracingParameters
from mirage.util import PolarVec, Vec2D, DelegateRegistry


@dataclass(kw_only=True, frozen=True)
@DelegateRegistry.register
class SingularIsothermalSphereLens(LensingSystem):
    redshift: float
    velocity_dispersion: u.Quantity
    star_fraction: float
    shear: PolarVec = field(default_factory=lambda: PolarVec.zero_vector("rad"))
    ellipticity: PolarVec = field(default_factory=lambda: PolarVec.zero_vector("rad"))

    @property
    def einstein_radius(self) -> u.Quantity:
        d_ls = self.cosmology.angular_diameter_distance_z1z2(
            self.redshift, self.quasar.redshift
        )
        d_s = self.cosmology.angular_diameter_distance(self.quasar.redshift)
        ret = (4 * pi * self.velocity_dispersion.to("m/s") ** 2 * d_ls) / (
            d_s * const.c**2
        )
        ret = ret.to("")
        return u.Quantity(ret.value, "rad").to("arcsec")

    def microtracing_parameters(self, position: Vec2D) -> TracingParameters:
        return TracingParameters(
            convergence=self._convergence(position),
            shear=self._shear(position),
            starry_fraction=self.star_fraction,
        )

    def _convergence(self, position: Vec2D) -> float:
        # TODO: Validate that this is the correct convergence equation
        b = self.einstein_radius.to("rad").value
        x = position.x.to("rad").value
        y = position.y.to("rad").value
        E = self.ellipticity.theta.to("rad").value
        t1 = x * sin(E) + y * cos(E)
        t2 = y * sin(E) - x * cos(E)
        p = self.shear.theta.to("rad").value
        g = self.shear.r.value
        q = 1 - self.ellipticity.r.value
        return (
            b / (2 * sqrt(q**2 * t1**2 + t2**2))
            + 3 * g * cos(E - p + arctan2(t2, t1)) / 4
        )

    def _shear(self, position: Vec2D) -> float:
        # TODO: Validate that this is the correct shear equation
        b = self.einstein_radius.to("rad").value
        x = position.x.to("rad").value
        y = position.y.to("rad").value
        E = self.ellipticity.theta.to("rad").value
        t1 = x * sin(E) + y * cos(E)
        t2 = y * sin(E) - x * cos(E)
        p = self.shear.theta.to("rad").value
        g = self.shear.r.value
        q = 1 - self.ellipticity.r.value
        return sqrt(
            t1**2
            * (
                2 * b * t2 * (t1**2 + t2**2) * sqrt(q**2 * t1**2 + t2**2)
                + g
                * sqrt((t1**2 + t2**2) / t1**2)
                * (
                    t1**2
                    * (
                        q**2 * t1**3 * sin(E - p)
                        - q**2 * t2**3 * cos(E - p)
                        + t1 * t2**2 * sin(E - p)
                    )
                    - t2**5 * cos(E - p)
                )
            )
            ** 2
            / (
                4
                * (t1**2 + t2**2) ** 2
                * (
                    q**2 * t1**4
                    + q**2 * t1**2 * t2**2
                    + t1**2 * t2**2
                    + t2**4
                )
                ** 2
            )
            + (
                -b * t1**2 * sqrt(q**2 * t1**2 + t2**2) / 2
                + b * t2**2 * sqrt(q**2 * t1**2 + t2**2) / 2
                + g * q**2 * t1**4 * cos(E - p + arctan2(t2, t1)) / 4
                + g * q**2 * t1**3 * t2 * sin(E - p + arctan2(t2, t1))
                - g * q**2 * t1**2 * t2**2 * cos(E - p + arctan2(t2, t1)) / 4
                + g * t1**2 * t2**2 * cos(E - p + arctan2(t2, t1)) / 4
                + g * t1 * t2**3 * sin(E - p + arctan2(t2, t1))
                - g * t2**4 * cos(E - p + arctan2(t2, t1)) / 4
            )
            ** 2
            / (
                q**2 * t1**4
                + q**2 * t1**2 * t2**2
                + t1**2 * t2**2
                + t2**4
            )
            ** 2
        )
