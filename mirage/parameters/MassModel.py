from astropy import units as u
from astropy import constants as const

from mirage.util import Jsonable, Vec2D, PolarVec

from .Cosmic import Cosmic
from .CalculationDependency import CalculationDependency

class Lens(Jsonable, Cosmic, CalculationDependency):
	"""A class for containing information about a lensing galaxy. In the future this could be overridden to specify various mass profiles, but by default we consider a singular isothermal ellipse in the presence of external shear.
	""" 

	def __init__(self,redshift:float, velocity_dispersion:u.Quantity,
		shear: PolarVec, ellipticity:PolarVec) -> None:
		Cosmic.__init__(self,redshift)
		CalculationDependency.__init__(self)
		Jsonable.__init__(self)
		try:
			assert isinstance(shear,PolarVec)
			assert isinstance(ellipticity, PolarVec)
			assert isinstance(redshift,float)
			self._velocity_dispersion = velocity_dispersion.to('km/s')
			self._ellipticity = ellipticity
			self._shear = shear
		except:
			from mirage.parameters import ParametersError
			raise ParametersError("Could not construct a Lens instance from the supplied constructor arguments.")

	#I define methods to expose internal attributes

	@property
	def shear(self):
		return self._shear

	@property
	def velocity_dispersion(self):
		return self._velocity_dispersion
	
	@property
	def ellipticity(self):
		return self._ellipticity
	
	@property
	def json(self):
		ret = {}
		ret['ellipticity'] = self.ellipticity.json
		ret['shear'] = self.shear.json
		ret['velocity_dispersion'] = Jsonable.encode_quantity(self.velocity_dispersion)
		ret['redshift'] = self.redshift
		return ret


	@classmethod
	def from_json(cls, js):
		el = PolarVec.from_json(js['ellipticity'])
		shear = PolarVec.from_json(js['shear'])
		vd = Jsonable.decode_quantity(js['velocity_dispersion'])
		z = js['redshift']
		return cls(z,vd,shear,el)

	def is_similar(self,other:'Lens') -> bool:
		return self.json == other.json	
	
