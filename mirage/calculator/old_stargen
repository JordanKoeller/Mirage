from mirage.utility import Vector2D, Region, JSONable
from .InitialMassFunction import IMF_broken_powerlaw, Evolved_IMF
from astropy import units as u
import numpy as np
from abc import ABC, abstractmethod

class MassFunction(JSONable,ABC):

    def __init__(self,IMF:IMF_broken_powerlaw, seed:int=None, percent_stars=0) -> None:
        self._IMF = IMF
        seed = seed or np.random.randint(2**32-1)
        self._seed = seed
        self._IMF.set_seed(seed)
        self._percent_stars = percent_stars
        self._stars = np.array([])

    def is_similar(sel,other) -> bool:
        return self.json == other.json

    def set_percentage(self,num:float) -> None:
        self._percent_stars = num/100
        self._stars = np.array([])

    @property
    def percent_stars(self):
        return self._percent_stars

    @abstractmethod
    def generate_stars(self,region:Region,mass_density:u.Quantity) -> np.ndarray:
        pass

    @property
    def seed(self):
        return self._seed

    @property
    def stars(self):
        if len(self._stars) > 0:
            return self._stars
        else:
            raise EnvironmentError("Never generated stars to begin with.")
    

    @property
    def json(self):
        ret = {}
        ret['seed'] = self._seed
        ret['mass_limits'] = self._IMF._mass_limits.tolist()
        ret['powers'] = self._IMF._powers.tolist()
        ret['percent_stars'] = self.percent_stars*100
        if isinstance(self._IMF, Evolved_IMF):
            ret['conversions'] = self._IMF.conversions.tolist()
        return ret

    @classmethod
    def from_json(cls,js):
        seed = js['seed']
        ml = js['mass_limits']
        pows = js['powers']
        pcnt = js['percent_stars']
        if 'conversions' in js:
            convs = js['conversions']
            imf = Evolved_IMF(conversions = convs,
                powers = pows,
                massLimits = ml)
            return cls(imf,seed,pcnt)
        else:
            imf = IMF_broken_powerlaw(ml,pows)
            return cls(imf,seed,pcnt)

class StationaryStarGenerator(MassFunction):

    def __init__(self,IMF:IMF_broken_powerlaw,seed:int=None,percent_stars:int=0) -> None:
        MassFunction.__init__(self,IMF,seed,percent_stars)


    def generate_stars(self,region:Region,mass_density:u.Quantity) -> np.ndarray:
        if len(self._stars) == 0:
            total_mass = mass_density * region.area * self._percent_stars
            self._IMF.set_seed(self.seed)
            masses = self._IMF.generate_cluster(total_mass.to('solMass').value)
            ret_arr = np.ndarray((len(masses),3))
            rng = self._IMF.random_number_generator
            d2 = region.dimensions/2.0
            offsets = rng.rand(len(masses),2) - 0.5
            print(masses.shape)
            ret_arr[:,0] = offsets[:,0]*d2.x + region.center.x
            ret_arr[:,1] = offsets[:,1]*d2.y + region.center.y
            ret_arr[:,2] = np.array(masses)
            self._stars = ret_arr
        return self._stars


def getMassFunction() -> MassFunction:
    from .InitialMassFunction import Kroupa_2001, Kroupa_2001_Modified, Weidner_Kroupa_2004
    import numpy as np
    from mirage.preferences import GlobalPreferences
    seed = GlobalPreferences['star_generator_seed']
    fn = GlobalPreferences['mass_function']
    if fn == "Kroupa_2001": return StationaryStarGenerator(Kroupa_2001(),seed)
    elif fn == "Pooley_2011": return StationaryStarGenerator(Kroupa_2001_Modified(),seed)
    elif fn == "Aged_galaxy": return StationaryStarGenerator(Evolved_IMF(),seed)
    #Means this is a custom IMF. It may or may not have aging thresholds.
    elif "mass_limits" in fn and "powers" in fn:
        imf = IMF_broken_powerlaw(np.array(fn['mass_limits']),np.array(fn['powers']))
        if 'conversions' in fn:
            return StationaryStarGenerator(imf,seed)
        else:
            emf = Evolved_IMF(imf,conversions = fn['conversions'])
            return StationaryStarGenerator(emf,seed)
        # ret = StationaryStarGenerator(IMF_broken_powerlaw(np.array(fn['mass_limits']),np.array(fn['powers'])),seed)
        # if "conversions" in fn: ret = StationaryStarGenerator(Evolved_IMF(ret,fn['conversions']),seed)
    else:
        raise ValueError("Not a valid mass function. Please update your preferences.")
        