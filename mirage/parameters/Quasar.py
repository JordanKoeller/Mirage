from astropy import units as u
from astropy import constants as const

from mirage.util import Jsonable
from .Cosmic import Cosmic
from .CalculationDependency import CalculationDependency

class Quasar(Jsonable, Cosmic, CalculationDependency):
	"""A class for containing information about a quasar. By default this class does not contain information to animate the quasar. However, it can be decorated with a :class:`MovableQuasar` for animating it.
	""" 

	def __init__(self,redshift:float, radius: u.Quantity, mass: u.Quantity) -> None:
		Cosmic.__init__(self,redshift)
		CalculationDependency.__init__(self)
		Jsonable.__init__(self)
		try:
			self._mass = mass.to('solMass')
			try:
				self._radius = radius.to('uas')
			except:
				tmp = radius.to('m')/self.ang_diam_dist.to('m')
				self._radius = u.Quantity(tmp.value,'rad').to('uas')
		except:
			from mirage.parameters import ParametersError
			raise ParametersError("Quasar could not construct itself based on the provided constructor arguments.")

	@staticmethod
	def static_r_g(mass,z):
		add = Cosmic.cosmology.angular_diameter_distance(z).to('m')
		linRg = mass.to('kg')*const.G/const.c/const.c
		angRg = linRg.to('m')/add
		return u.def_unit('r_g',angRg.value*u.rad)
		

	@property
	def radius(self):
		return self._radius

	@property
	def mass(self):
		return self._mass


	@property
	def r_g(self):
		return Quasar.static_r_g(self.mass,self.redshift)

	@property 
	def json(self):
		ret = {}
		ret['redshift'] = self.redshift
		ret['mass'] = Jsonable.encode_quantity(self.mass)
		ret['radius'] = Jsonable.encode_quantity(self.radius)
		return ret

	@classmethod
	def from_json(cls,js):
		z = js['redshift']
		mass = Jsonable.decode_quantity(js['mass'])
		rad = Jsonable.decode_quantity(js['radius'])
		return cls(z,rad,mass)

	def is_similar(self,other:'Quasar') -> bool:
		return self.redshift == other.redshift

	def update(self,radius=None,mass=None,redshift=None):
		if radius != None:
			self._radius = radius
		if mass != None:
			self._mass = mass
		# if redshift != None:
		# 	self._redshift = redshift
