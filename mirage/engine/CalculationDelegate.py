from abc import ABC, abstractmethod

from scipy.spatial import cKDTree
from astropy import units as u
import numpy as np

from mirage.parameters import Parameters, MicrolensingParameters
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
        from mirage.engine.micro_ray_tracer import ray_trace
        self._inputUnit = parameters.theta_E
        rays = parameters.ray_region.pixels
        # print(rays)
        print("Cnter of " + str(parameters.ray_region.center))
        # rays -= u.Quantity(1.4,'arcsec')
        rays[:,0] -= parameters.ray_region.center.x.to(self._inputUnit)
        rays[:,1] -= parameters.ray_region.center.y.to(self._inputUnit)
        rays = rays.to(parameters.theta_E).value
        stars = parameters.stars
        kap,starry,gam = parameters.mass_descriptors
        # print("Ray-tracing started")
        src_plane = ray_trace(
            rays,
            kap,
            gam,
            4, #self.core_count,
            stars)
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

    def query_region(self,region,radius:u.Quantity) -> np.ndarray:
        pts = region.pixels.to(self._inputUnit)
        # print(pts.mean())
        ret = np.ndarray((pts.shape[0],pts.shape[1]),dtype=np.int32)
        rad = radius.to(self._inputUnit).value
        for i in range(pts.shape[0]):
            for j in range(pts.shape[1]):
                x = pts[i,j,0].value
                y = pts[i,j,1].value
                inds = self._tree.query_ball_point((x,y),rad)
                ret[i,j] = len(inds)
        return ret

    # def query_points(self,points:np.ndarray, radius:u.Quantity) -> np.ndarray:
    #     ret = np.ndarray(points.shape[0])
    #     pts = points
    #     print(pts.shape)
    #     rad = radius.to(self._inputUnit).value
    #     for i in range(points.shape[0]):
    #         x = pts[i,0].value
    #         y = pts[i,1].value
    #         ret[i] = len(self._tree.query_ball_point((x,y),rad))
    #     return ret