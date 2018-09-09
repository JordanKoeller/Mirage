from astropy.cosmology import WMAP5

class Cosmic(object):
	"""An abstract class for handling cosmological calculations. This class allows for self-consistent cosmology calculations. 

	With this class, one can ensure that the same cosmology is always used, with the same hubble constant. 

	It accepts one input argument, the redshift of an object."""
	cosmology = WMAP5

	def __init__(self, redshift:float):
		self._z = redshift

	# @staticmethod
	# def cosmology():
	# 	return WMAP5

	@property
	def ang_diam_dist(self):
		return self.cosmology.angular_diameter_distance(self._z)

	@property
	def redshift(self):
		return self._z
	
	
		