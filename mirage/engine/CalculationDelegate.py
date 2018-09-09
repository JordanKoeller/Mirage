from abc import ABC, abstractmethod, abstractproperty

from scipy.spatial import cKDTree
from astropy import units as u
import numpy as np

from mirage.parameters import Parameters 
from mirage.util import Vec2D

class CalculationDelegate(ABC):

	def __init__(self):
		pass

	@property
	def core_count(self):
		from mirage import GlobalPreferences
		return GlobalPreferences['core_count']

	@abstractmethod
	def reconfigure(self,parameters:Parameters):
		pass

	@abstractmethod
	def get_connecting_rays(self,location:Vec2D, radius:u.Quantity) -> np.ndarray:
		pass


	# @abstractmethod
	# def get_ray_count(self,location:Vec2D, radius:u.Quantity) -> int:
	# 	pass

	# @abstractmethod
	# def query_points(self,points:np.ndarray, radius:u.Quantity) -> np.ndarray:
	# 	pass

class MacroCPUDelegate(CalculationDelegate):

	def __init__(self):
		# from mirage import GlobalPreferences
		# self.core_count = GlobalPreferences['core_count']
		self._tree = None

	def reconfigure(self,parameters:Parameters):
		from mirage.engine.ray_tracer import ray_trace
		rays = parameters.ray_region.pixels.to('rad').value
		print(rays)
		print("Starting rays")
		src_plane = ray_trace(rays,
			parameters.dL.to('m').value,
			parameters.dS.to('m').value,
			parameters.dLS.to('m').value,
			parameters.lens.shear.magnitude.value,
			parameters.lens.shear.direction.to('rad').value,
			parameters.lens.ellipticity.magnitude.value,
			parameters.lens.ellipticity.direction.to('rad').value,
			parameters.einstein_radius.to('rad').value,
			self.core_count)
		print("Done with tracing")
		self._canvas_dimensions = parameters.ray_region.resolution
		flat_array = np.reshape(src_plane,(src_plane.shape[0]*src_plane.shape[1],2))
		self._tree = cKDTree(flat_array,256,False,False,False)
		print("Done with tree")

	def get_connecting_rays(self,location:Vec2D,radius:u.Quantity) -> np.ndarray:
		x = location.x.to('rad').value
		y = location.y.to('rad').value
		rad = radius.to('rad').value
		inds = self._tree.query_ball_point((x,y),rad)
		# print(inds.shape)
		pts = list(map(lambda ind: [ind // self._canvas_dimensions.x.value, ind % self._canvas_dimensions.y.value],inds))
		return np.array(pts)

	def get_ray_count(self,location:Vec2D,radius:u.Quantity) -> int:
		x = location.x.to('rad').value
		y = location.y.to('rad').value
		rad = radius.to('rad').value
		inds = self._tree.query_ball_point((x,y),rad)
		return len(inds)

	

