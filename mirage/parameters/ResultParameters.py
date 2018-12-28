from abc import abstractproperty
import math

from astropy import units as u
import numpy as np

from mirage.util import Jsonable, Vec2D, Region


class ResultParameters(Jsonable):

    def __init__(self):
        pass

    @classmethod
    def from_json(cls,js):
        k,v = js 
        if k == 'magmap':
            return MagnificationMapParameters.from_json(v)
        elif k == 'lightcurves':
            return LightCurvesParameters.from_json(v)
        elif k == 'causticmap':
            return CausticMapParameters.from_json(v)

    @abstractproperty
    def keyword(self):
        pass


class MagnificationMapParameters(ResultParameters):

    def __init__(self,resolution:Vec2D):
        self._resolution = resolution

    @property
    def resolution(self):
        return self._resolution

    @property
    def json(self):
        return {'magmap_resolution' : self.resolution.json}

    @classmethod
    def from_json(cls,js):
        return cls(Vec2D.from_json(js['magmap_resolution']))

    @property
    def keyword(self):
        return "magmap"

class CausticMapParameters(MagnificationMapParameters):

    def __init__(self,resolution:Vec2D):
        MagnificationMapParameters.__init__(self,resolution)

    @property
    def resolution(self):
        return self._resolution

    @property
    def json(self):
        return {'caustic_resolution' : self.resolution.json}

    @classmethod
    def from_json(cls,js):
        return cls(Vec2D.from_json(js['caustic_resolution']))

    @property
    def keyword(self):
        return "causticmap"
    

class LightCurvesParameters(ResultParameters):

    def __init__(self,num_curves:int,
        sample_density:u.Quantity,
        seed:int=None):
        self._num_curves = num_curves
        self._sample_density = sample_density.to('1/uas')
        self._seed = seed

    @property
    def seed(self):
        return self._seed
    
    @property
    def num_curves(self):
        return self._num_curves
    
    @property
    def sample_density(self):
        return self._sample_density

    @property
    def json(self):
        ret = {}
        ret['seed'] = self.seed
        ret['num_curves'] = self.num_curves
        ret['sample_density'] = Jsonable.encode_quantity(self.sample_density)
        return ret

    @classmethod
    def from_json(cls,js):
        seed = js['seed']
        num_curves = js['num_curves']
        sample_density = Jsonable.decode_quantity(js['sample_density'])
        return cls(num_curves,sample_density,seed)
    

    @property
    def keyword(self):
        return "lightcurves"
    
    
    def lines(self,region:Region) -> np.ndarray:
        rng = np.random.RandomState(self.seed)
        scaled = rng.rand(self.num_curves,4) - 0.5
        #np.random.rand returns an array of (number,4) dimension of doubles over interval [0,1).
        #I subtract 0.5 to center on 0.0
        center = region.center
        dims = region.dimensions
        width = dims.x.value
        height = dims.y.value
        scaled[:,0] *= width
        scaled[:,1] *= height
        scaled[:,2] *= width
        scaled[:,3] *= height
        # from mirage.calculator import interpolate
        # slices = map(lambd/a line: u.Quantity(np.array(self._slice_line(line,region)).T,'rad'),scaled)
        ends = self.end_points(region,scaled*region.unit)
        ret = self.interpolate(ends,1/self.sample_density)
        return ret

    # def line_ends(self,region:Region) -> np.ndarray
    #     rng = np.random.RandomState(self.seed)
    #     scaled = rng.rand(self.num_curves,4) - 0.5
    #     #np.random.rand returns an array of (number,4) dimension of doubles over interval [0,1).
    #     #I subtract 0.5 to center on 0.0
    #     center = region.center.to('rad')
    #     dims = region.dimensions.to('rad')
    #     width = dims.x.value
    #     height = dims.y.value
    #     scaled[:,0] *= width
    #     scaled[:,1] *= height
    #     scaled[:,2] *= width
    #     scaled[:,3] *= height
    #     from mirage.calculator import interpolate_ends
    #     return = interpolate_ends(region,scaled,self.sample_density)


    def end_points(self,region,two_points):
        two_points = two_points.to(region.unit)
        lX, lY, rX, rY = region.extent 
        deltas = two_points[:,2:] #two_points[:,2:] - two_points[:,0:2]
        a_point = two_points[:,0:2]
        t_values = np.ndarray((two_points.shape[0],4))  
        t_values[:,0] = (lX - a_point[:,0])/deltas[:,0] 
        t_values[:,1] = (lY - a_point[:,1])/deltas[:,1] 
        t_values[:,2] = (rX - a_point[:,0])/deltas[:,0] 
        t_values[:,3] = (rY - a_point[:,1])/deltas[:,1] 
        sorts = np.sort(t_values,axis=1) 
        good_t_values = sorts[:,1:3] 
        intersection_points = np.ndarray(t_values.shape) 
        intersection_points[:,0] = a_point[:,0] + good_t_values[:,0]*deltas[:,0] 
        intersection_points[:,1] = a_point[:,1] + good_t_values[:,0]*deltas[:,1] 
        intersection_points[:,2] = a_point[:,0] + good_t_values[:,1]*deltas[:,0] 
        intersection_points[:,3] = a_point[:,1] + good_t_values[:,1]*deltas[:,1] 
        return intersection_points*region.unit

    def interpolate(self,end_points,density): 
        du = end_points.unit
        density = density.to(du).value
        end_points = end_points.value
        def interp(row): 
            distance = np.sqrt((row[2] - row[1])**2.0 + (row[3] - row[1])**2.0) 
            num_points = int(distance/density) 
            xx = np.linspace(row[0],row[2],num_points) 
            yy = np.linspace(row[1],row[3],num_points) 
            return np.dstack((xx,yy)) 
        interped = map(interp,end_points) 
        ret = [i.reshape((i.shape[1],2))*du for i in interped] 
        return ret 


