
class ParametersError(Exception):
	def __init__(self,value):
		self.value = value

	def __repr__(self):
		return repr(self.value)

from .Cosmic import Cosmic
from .CalculationDependency import CalculationDependency
from .Quasar import Quasar
from .MassModel import Lens
from .Parameters import Parameters, MicrolensingParameters


def QSO2237():
	from astropy import units as u
	from mirage.util import Vec2D, PolarVec, PixelRegion,Region
	q = Quasar(1.69,0.8*u.arcsec,1000000000*u.solMass)
	shear = PolarVec(0.07,67.1)
	ellip = PolarVec(1.0,0.0)
	rays = PixelRegion(Vec2D(0.0,0.0,'arcsec'),Vec2D(40.0,40.0,'arcsec'),Vec2D(2000,2000))
	lens = Lens(0.04,177.95*u.km/u.s,shear,ellip)
	params = Parameters(q,lens,rays)
	return params
