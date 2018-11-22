from abc import abstractmethod

from astropy import units as u
import numpy as np

from mirage.util import Jsonable, Region, zero_vector
from .InitialMassFunction import IMF_broken_powerlaw, Evolved_IMF



class MassFunction(Jsonable):

    def __init__(self,IMF:IMF_broken_powerlaw, seed:int=None) -> None:
        self._IMF = IMF
        seed = seed or np.random.randint(2**32-1)
        self._seed = seed
        self._IMF.set_seed(seed)
        self._stars = np.array([])

    def is_similar(self,other) -> bool:
        return self.json == other.json

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
        if isinstance(self._IMF, Evolved_IMF):
            ret['conversions'] = self._IMF.conversions.tolist()
        return ret

    @classmethod
    def from_json(cls,js):
        seed = js['seed']
        ml = js['mass_limits']
        pows = js['powers']
        if 'conversions' in js:
            convs = js['conversions']
            imf = Evolved_IMF(conversions = convs,
                powers = pows,
                massLimits = ml)
            return cls(imf,seed)
        else:
            imf = IMF_broken_powerlaw(ml,pows)
            return cls(imf,seed)

    @abstractmethod
    def generate_stars(self,region:Region, mass_density:u.Quantity) -> np.ndarray:
        pass

class StationaryMassFunction(MassFunction):

    def __init__(self,IMF:IMF_broken_powerlaw,seed:int=None) -> None:
        MassFunction.__init__(self,IMF,seed)


    def generate_stars(self,region:Region,mass_density:u.Quantity,center_on_zero=False) -> np.ndarray:
        if len(self._stars) == 0:
            total_mass = mass_density * region.area
            self._IMF.set_seed(self.seed)
            masses = self._IMF.generate_cluster(total_mass.to('solMass').value)
            ret_arr = np.ndarray((len(masses),3))
            rng = self._IMF.random_number_generator
            # return rng.get_state()
            locs = region.random_sample(len(masses),rng)
            ret_arr[:,0] = locs[:,0].value
            ret_arr[:,1] = locs[:,1].value
            ret_arr[:,2] = np.array(masses)
            self._stars = ret_arr
            return ret_arr
        else:
            return self._stars


def getMassFunction() -> MassFunction:
    from .InitialMassFunction import Kroupa_2001, Kroupa_2001_Modified
    # from .InitialMassFunction import Kroupa_2001
    # seed = 123
    # print("NEED to fix GETMASSFUNCTION")
    # return StationaryMassFunction(Kroupa_2001(),seed)
    import numpy as np
    from mirage import GlobalPreferences
    seed = GlobalPreferences['star_generator_seed']
    fn = GlobalPreferences['mass_function']
    if fn == "Kroupa_2001":
        return StationaryMassFunction(Kroupa_2001(),seed)
    elif fn == "Pooley_2011":
        return StationaryMassFunction(Kroupa_2001_Modified(),seed)
    elif fn == "Aged_galaxy":
        return StationaryMassFunction(Evolved_IMF(),seed)

    # #Means this is a custom IMF. It may or may not have aging thresholds.
    elif "mass_limits" in fn and "powers" in fn:
        imf = IMF_broken_powerlaw(np.array(fn['mass_limits']),np.array(fn['powers']))
        if 'conversions' not in fn:
            return StationaryMassFunction(imf,seed)
        else:
            emf = Evolved_IMF(imf,conversions = fn['conversions'])
            return StationaryMassFunction(emf,seed)
    #     # ret = StationaryMassFunction(IMF_broken_powerlaw(np.array(fn['mass_limits']),np.array(fn['powers'])),seed)
    #     # if "conversions" in fn: ret = StationaryMassFunction(Evolved_IMF(ret,fn['conversions']),seed)
    # else:
    #     raise ValueError("Not a valid mass function. Please update your preferences.")