from dataclasses import dataclass, field

from astropy import units as u

@dataclass(frozen=True, kw_only=True)
class TracingParameters:
  """
  Parameters used to describe a gravitational lens for gravitational microlensing.

  When microlensing it is assumed that the scale of the lens being simulated is small
  enough that the parameters encapsulated by this class are locally constant over the
  simulated region.

  Args:
  
    + convergence (float): Unitless quantity describing the surface mass density of the lens.
    + shear (float): Unitless quantity describing the ellipticity of the lens.
    + starry_fraction (float): How much of the mass in the lens to simulate as discrete stars. The
        remainder of the mass is simulated as smooth matter. This should be a number between zero
        and one.
  """
  convergence: float
  shear: float
  starry_fraction: float