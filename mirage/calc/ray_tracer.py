from abc import ABC, abstractmethod

from astropy import units as u

from mirage.util import PixelRegion


class RayTracer(ABC):
    """
    Encapsulates deflecting a bundle of rays around a lensing galaxy.
    """

    @abstractmethod
    def trace(self, rays: PixelRegion) -> u.Quantity:
        """
        Trace the bundle of rays through the lensing galaxy and return their
        positions on the source plane.

        Rays are passed in in units of arcsec, and the deflected rays should be returned
        in units of arcsec as well.
        """
