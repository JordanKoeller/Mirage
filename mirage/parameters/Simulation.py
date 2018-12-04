import copy
import math

import numpy as np
from astropy import units as u

from .Parameters import Parameters, MicrolensingParameters, ParametersError
from .ResultParameters import ResultParameters
from mirage.util import Vec2D, Jsonable, Region


class Simulation(Jsonable):

    def __init__(self,
        parameters:MicrolensingParameters,
        name:str,
        description:str,
        num_trials:int,
        trial_variance:str='',
        trial:int=0):
        self._name = name
        self._description = description
        self._num_trials = num_trials
        self._trial_variance = trial_variance
        self._parameters = parameters
        # self.parameters(self.num_trials-1)
        self._results = {}
        self.set_trial(trial)

    def add_result(self,result:ResultParameters): 
        self._results[result.keyword] = result

    def set_trial(self,trial):
        if trial < self.num_trials:
            self._trial = trial
        else:
            raise ParametersError("Requested trial exceeds the max.")


    @property
    def trial_variance(self):
        return self._trial_variance
    
    @property
    def num_trials(self):
        return self._num_trials

    @property
    def description(self):
        return self._description

    @property
    def name(self):
        return self._name

    @property
    def original_parameters(self):
        return self._parameters

    @property
    def trial_number(self):
        return self._trial

    @property 
    def parameters(self) -> MicrolensingParameters:
        if self.trial_variance:
            nspace = {}
            try:
                exec(self.trial_variance,{'old_parameters':self.original_parameters,'trial_number':self.trial_number,'u':u,'np':np,'copy':copy,'math':math},nspace)
            except ParametersError as e:
                raise ParametersError("Parameters Error encountered in generating new Parameters instance.")
            except:
                raise SyntaxError
            return nspace['new_parameters']
        else:
            return self.original_parameters

    @property
    def json(self):
        ret = {}
        ret['name'] = self.name
        ret['description'] = self.description
        ret['trial_count'] = self.num_trials
        ret['variation'] = self.trial_variance
        ret['parameters'] = self.original_parameters.json
        tmp = {}
        for k,v in self._results.items():
            tmp[k] = v.json
        ret['results'] = tmp
        return ret

    @classmethod
    def from_json(cls,js):
        name = js['name']
        desc = js['description']
        tc = js['trial_count']
        variation = js['variation']
        params = MicrolensingParameters.from_json(js['parameters'])
        ret = cls(params, name, desc, tc, variation)
        results = js['results']
        for k,v in results.items():
            value = ResultParameters.from_json((k,v))
            ret.add_result(value)
        return ret
        

    def __getitem__(self,ind):
        return self._results[ind]


    def __contains__(self,k):
        return k in self._results

    def __len__(self):
        return len(self._results)


class AnimationSimulation(Jsonable):

    def __init__(self,parameters:Parameters,start_pos:Vec2D,velocity:Vec2D):
        self._parameters = parameters
        self._start_pos = start_pos
        self._velocity = velocity

    @property
    def parameters(self):
        return self._parameters
    
    @property
    def start_position(self):
        return self._start_pos

    @property
    def velocity(self):
        return self._velocity

    def query_info(self,time:u.Quantity):
        """
            Returns all the info needed to query a system.

            Returns:
                position: Vec2D
                radius: u.Quantity
        """
        pos = self.start_position + self.velocity*time
        radius = self.parameters.quasar.radius
        return (pos,radius)


    def update(self,start_position=None,velocity=None):
        if start_position:
            self._start_pos = start_position
        if velocity:
            self._velocity = velocity

    @classmethod
    def from_json(cls,js):
        params = Parameters.from_json(js['parameters'])
        start = Vec2D.from_json(js['start_position'])
        vel = Vec2D.from_json(js['quasar_velocity'])
        return cls(params,start,vel)

    @property
    def json(self):
        js = {}
        js['parameters'] = self.parameters.json
        js['start_position'] = self.start_position.json
        js['quasar_velocity'] = self.velocity.json
        return js
    