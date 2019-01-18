from abc import abstractmethod
import math

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
    def IMF(self):
        return self._IMF
    

    @property
    def stars(self):
        if len(self._stars) > 0:
            return self._stars
        else:
            raise EnvironmentError("Never generated stars to begin with.")
    

    @property
    def json(self):
        from .InitialMassFunction import Kroupa_2001, Kroupa_2001_Modified
        ret = {}
        ret['seed'] = self._seed
        if isinstance(self._IMF, Kroupa_2001):
            ret['type'] = "Kroupa_2001"
        elif isinstance(self._IMF,Kroupa_2001_Modified):
            ret['type'] = "Pooley_2011"
        else:
            ret['mass_limits'] = self._IMF.mass_limits.tolist()
            ret['powers'] = self._IMF.powers.tolist()
            if isinstance(self._IMF, Evolved_IMF):
                ret['conversions'] = self._IMF.conversions.tolist()
        return ret

    @classmethod
    def from_json(cls,js):
        if "mean_velocity" in js:
            return AnimatedMassFunction.from_json(js)
        else:
            return StationaryMassFunction.from_json(js)

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

    @classmethod
    def from_json(cls,js):
        from .InitialMassFunction import Kroupa_2001, Kroupa_2001_Modified
        seed = js['seed']
        if 'type' in js:
            if js['type'] == "Kroupa_2001":
                imf = Kroupa_2001()
                return cls(imf,seed)
        else:
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


class AnimatedMassFunction(MassFunction):

    def __init__(self,IMF:IMF_broken_powerlaw,velocity:u.Quantity,sigma:u.Quantity,dt:u.Quantity,seed:int=None) -> None:
        self._stationaryFunc = StationaryMassFunction(IMF,seed)
        self._velocity_characteristics = (velocity,sigma.to(velocity.unit))
        self._region_info = None
        self._time = dt*0.0
        self._dt = dt
        self._stars = []
        self._velocity = None
        # self._next_injection = 0
        self._ret_stars = None
        self._ret_vel = None

    def generate_stars(self,region:Region,mass_density:u.Quantity,center_on_zero=False) -> np.ndarray:
        if len(self._stars) == 0:
            self._region_info = (region,mass_density,center_on_zero)
            self._stars = self._stationaryFunc.generate_stars(region,mass_density,center_on_zero)
            self._velocity = self._get_velocities_for(self._stars)
            self._ret_stars = self._stars
            self._ret_vel = self._velocity
            #I've made the initial stars. Now I need to determine the injection sampler.
            # print(region.radius)
            self._injection_mean  = region.radius/self._velocity_characteristics[0]
            self._injection_sigma = region.radius*self._velocity_characteristics[1]/(self._velocity_characteristics[0]**2)
            # print("Injectors " + str(self._injection_sigma) + ", " + str(self._injection_mean))
        return self.stars
        # I just remove the z direction, leaving just the two others after it all.

    def _prune_and_replenish(self):
        #First find what stars have escaped
        curr_stars = self.stars
        within = np.sqrt(curr_stars[:,0]**2+curr_stars[:,1]**2) <= self._region_info[0].radius.value
        stars_within = np.take(curr_stars,within,axis=0)
        vel_within = np.take(self._velocity,within,axis=0)
        # if self._last_injection < self._time:
        approx_injected = int((self._time/self._injection_mean).to(self._dt.unit).value)
        if approx_injected > 0:
            add_times = rng.normal(self._injection_mean.value,self._injection_sigma.value,num_injected+10)
            cumulative_time = np.cumsum(add_times)
            num_added = np.searchsorted(cumulative_time,[self._time.value])[0]
            masses = np.array(self._stationaryFunc._IMF.generate_cluster(num_added)[0:num_added])
            pos_angle = rng.random(len(masses))*2*math.pi
            pos_x = np.cos(pos_angle)
            pos_y = np.sin(pos_angle)
            velocities = self._get_velocities_for(masses)
            s_x = pos_x - velocities[:,0]*self._dt
            s_y = pos_y - velocities[:,1]*self._dt
            ret_arr = np.ndarray((len(masses),3))
            ret_arr[:,0] = s_x
            ret_arr[:,1] = s_y
            ret_arr[:,2] = masses
            self._ret_stars = np.append(self._stars_start_pos,ret_arr,axis=0)
            self._ret_vel = np.append(self._velocity,velocities,axis=0)








    def _get_velocities_for(self,stars):
        rng = self._stationaryFunc._IMF.random_number_generator
        velocity, sigma = self._velocity_characteristics
        velocity_mags = rng.normal(velocity.value,sigma.value,len(stars))
        velocity_directions = rng.rand(len(stars),3)
        rng_mag = np.sqrt(velocity_directions[:,0]**2+velocity_directions[:,1]**2+velocity_directions[:,2]**2)
        velocity_directions[:,0] = velocity_directions[:,0]*velocity_mags/rng_mag
        velocity_directions[:,1] = velocity_directions[:,1]*velocity_mags/rng_mag
        velocity_directions[:,2] = velocity_directions[:,2]*velocity_mags/rng_mag
        return u.Quantity(velocity_directions[:,0:2],velocity.unit)

    @property
    def stars(self):
        if len(self._stars) > 0:
            # self._prune_and_replenish()
            tmp_stars = self._ret_stars.copy()
            tmp_stars[:,0] = tmp_stars[:,0] + (self._ret_vel[:,0]*self._time).value
            tmp_stars[:,1] = tmp_stars[:,1] + (self._ret_vel[:,1]*self._time).value
            return tmp_stars
        else:
            raise EnvironmentError("Never generated stars to begin with.")


    def _make_initial_stars(self,region:Region,mass_density:u.Quantity,center_on_zero=False) -> None:
        pass


    def set_time(self,time:u.Quantity) -> None:
        self._time = time


    def increment_time(self) -> None:
        self._time += self._dt


    def skip_to_frame(self,num:int) -> None:
        self._time = self._dt*num


    @property
    def json(self):
        ret = self._stationaryFunc.json
        ret['mean_velocity'] = Jsonable.encode_quantity(self._velocity_characteristics[0])
        ret['stderr_velocity'] = Jsonable.encode_quantity(self._velocity_characteristics[1])
        ret['dt'] = Jsonable.encode_quantity(self._dt)
        return ret

    @classmethod
    def from_json(cls,js):
        from .InitialMassFunction import Kroupa_2001, Kroupa_2001_Modified
        seed = js['seed']
        ml = js['mass_limits']
        pows = js['powers']
        velocity = Jsonable.decode_quantity(js['mean_velocity'])
        sigma = Jsonable.decode_quantity(js['stderr_velocity'])
        dt = Jsonable.decode_quantity(js['dt'])
        if 'type' in js:
            if js['type'] == "Kroupa_2001":
                imf = Kroupa_2001()
            else:
                imf = Kroupa_2001_Modified()
        else:
            if 'conversions' in js:
                convs = js['conversions']
                imf = Evolved_IMF(conversions = convs,
                    powers = pows,
                    massLimits = ml)
                return cls(imf,velocity,sigma,dt,seed)
            else:
                imf = IMF_broken_powerlaw(ml,pows)
                return cls(imf,velocity,sigma,dt,seed)






def getMassFunction(seed=None,fn=None) -> MassFunction:
    from .InitialMassFunction import Kroupa_2001, Kroupa_2001_Modified
    # from .InitialMassFunction import Kroupa_2001
    # seed = 123
    # print("NEED to fix GETMASSFUNCTION")
    # return StationaryMassFunction(Kroupa_2001(),seed)
    import numpy as np
    from mirage import GlobalPreferences
    seed = seed or GlobalPreferences['star_generator_seed']
    fn = fn or GlobalPreferences['mass_function']
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
    else:
        raise ValueError("Not a valid mass function. Please update your preferences.")



