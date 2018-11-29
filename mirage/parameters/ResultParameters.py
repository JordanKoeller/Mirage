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
        center = region.center.to('rad')
        dims = region.dimensions.to('rad')
        width = dims.x.value
        height = dims.y.value
        scaled[:,0] *= width
        scaled[:,1] *= height
        scaled[:,2] *= width
        scaled[:,3] *= height
#        scaled[:,0] += center.x.value
#        scaled[:,1] += center.y.value
#        scaled[:,2] += center.x.value
#        scaled[:,3] += center.y.value
        # lines = u.Quantity(scaled,'rad')
        from mirage.calculator import interpolate
        # slices = map(lambd/a line: u.Quantity(np.array(self._slice_line(line,region)).T,'rad'),scaled)
        self._lines = interpolate(region,scaled,self.sample_density)
        return self._lines


    def _slice_line(self,pts,region):
        #pts is an array of [x1,y1,x2,y2]
        #Bounding box is a MagMapParameters instance
        #resolution is a specification of angular separation per data point
        x1,y1,x2,y2 = pts
        m = (y2 - y1)/(x2 - x1)
        angle = math.atan(m)
        resolution = ((self.sample_density)**(-1)).to('rad')
        dx = resolution.value*math.cos(angle)
        dy = resolution.value*math.sin(angle)
        dims = region.dimensions.to('rad')
        center = region.center.to('rad')
        lefX =  - dims.x.value/2
        rigX =  + dims.x.value/2
        topY =  + dims.y.value/2 
        botY =  - dims.y.value/2
        flag = True
        x = x1
        y = y1
        retx = [] 
        rety = [] 
        while flag:
            x -= dx
            y -= dy
            flag = x >= lefX and x <= rigX and y >= botY and y <= topY
        flag = True
        while flag:
            x += dx
            y += dy
            retx.append(x)
            rety.append(y)
            flag = x >= lefX and x <= rigX and y >= botY and y <= topY
        retx = retx[:-1]
        rety = rety[:-1]
        return [retx,rety]
    
    
