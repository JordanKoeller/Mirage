from abc import ABC, abstractmethod

from scipy.spatial import cKDTree
from astropy import units as u
import numpy as np

from mirage.parameters import Parameters, MicrolensingParameters
from mirage.util import Vec2D

from .reducers import QueryReducer, MagmapReducer

class CalculationDelegate(ABC):

    def __init__(self):
        pass

    @property
    def core_count(self):
        from mirage import GlobalPreferences
        return GlobalPreferences['core_count']

    @abstractmethod
    def reconfigure(self,parameters:Parameters):
        """
        Inject a new system's parameters into the calculation engine.

        This method should lazily reconfigure the delegate, but not do any number-crunching yet.
        """
        pass

    @abstractmethod
    def query(self, reducer: QueryReducer) -> np.ndarray:
        """
        Submit a QueryReducer for the system to aggregate all the results of this simulation.

        Returns a SimulationResult object.
        """
        pass

    @abstractmethod
    def get_connecting_rays(self,location:Vec2D, radius:u.Quantity) -> np.ndarray:
        pass



class MacroCPUDelegate(CalculationDelegate):

    def __init__(self):
        self._tree = None

    def reconfigure(self,parameters:Parameters):
        from mirage.engine.ray_tracer import ray_trace
        rays = parameters.ray_region.pixels.to('rad').value
        src_plane = ray_trace(rays,
            parameters.dL.to('m').value,
            parameters.dS.to('m').value,
            parameters.dLS.to('m').value,
            parameters.lens.shear.magnitude.value,
            parameters.lens.shear.direction.to('rad').value,
            1 - parameters.lens.ellipticity.magnitude.value,
            parameters.lens.ellipticity.direction.to('rad').value,
            parameters.einstein_radius.to('rad').value,
            4)#self.core_count)
        self._canvas_dimensions = parameters.ray_region.resolution
        flat_array = np.reshape(src_plane,(src_plane.shape[0]*src_plane.shape[1],2))
        self._tree = cKDTree(flat_array,256,False,False,False)

    def get_connecting_rays(self,location:Vec2D,radius:u.Quantity) -> np.ndarray:
        x = location.x.to('rad').value
        y = location.y.to('rad').value
        rad = radius.to('rad').value
        inds = self._tree.query_ball_point((x,y),rad)
        # print(inds.shape)
        # pts = list(map(lambda ind: [ind // self._canvas_dimensions.x.value, ind % self._canvas_dimensions.y.value],inds))
        return np.array(inds,dtype=np.int32)

    def get_ray_count(self,location:Vec2D,radius:u.Quantity) -> int:
        x = location.x.to('rad').value
        y = location.y.to('rad').value
        rad = radius.to('rad').value
        inds = self._tree.query_ball_point((x,y),rad)
        return len(inds)

    

class MicroCPUDelegate(CalculationDelegate):

    def __init__(self):
        self._tree = None
        self._inputUnit = None

    def reconfigure(self,parameters:MicrolensingParameters):
        src_plane = self._ray_trace(parameters)
        # print("Ray-tracing done")
        self._canvas_dimensions = parameters.ray_region.resolution
        flat_array = np.reshape(src_plane,(src_plane.shape[0]*src_plane.shape[1],2))
        self._tree = cKDTree(flat_array,128,False,False,False)

    def get_connecting_rays(self,location:Vec2D,radius:u.Quantity) -> np.ndarray:
        x = location.x.to(self._inputUnit).value
        y = location.y.to(self._inputUnit).value
        rad = radius.to(self._inputUnit).value
        inds = self._tree.query_ball_point((x,y),rad)
        return np.array(inds,dtype=np.int32)

    def get_ray_count(self,location:Vec2D,radius:u.Quantity) -> int:
        x = location.x.to(self._inputUnit).value
        y = location.y.to(self._inputUnit).value
        rad = radius.to(self._inputUnit).value
        inds = self._tree.query_ball_point((x,y),rad)
        return len(inds)

    def query(self, reducer: QueryReducer) -> QueryReducer:
        for query in reducer.query_points():
            ray_indicies = self._tree.query_ball_point((query.x, query.y), query.radius)
            for index in ray_indicies:
                query.reduce_ray(self._tree.data[index])
            reducer.save_value(query.identifier, query.get_result())
        return reducer

    def query_region(self,region,radius:u.Quantity) -> QueryReducer:
        return self.query(MagmapReducer(region, radius))

    def _ray_trace(self, parameters: MicrolensingParameters):
        from mirage.engine.micro_ray_tracer import ray_trace
        self._inputUnit = parameters.theta_E
        rays = parameters.ray_region.pixels

        # print(rays)
        # rays -= u.Quantity(1.4,'arcsec')
        rays[:,:,0] -= parameters.ray_region.center.x.to(self._inputUnit)
        rays[:,:,1] -= parameters.ray_region.center.y.to(self._inputUnit)
        rays = rays.to(parameters.theta_E).value
        stars = parameters.stars
        kap,starry,gam = parameters.mass_descriptors
        return ray_trace(
            rays,
            np.empty_like(rays),
            kap,
            gam,
            self.core_count,
            stars)