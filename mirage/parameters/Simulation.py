import copy
import math

import numpy as np
from astropy import units as u

from .Parameters import Parameters, MicrolensingParameters, ParametersError, ResultParameters
from mirage.utility import Vec2D, Jsonable, Region


class Simulation(Jsonable):

	def __init__(self,
		parameters:MicrolensingParameters,
		name:str,
		description:str,
		num_trials:int,
		trial_variance:str=''):
		self._name = name
		self._description = description
		self._num_trials = num_trials
		self._trial_variance = trial_variance
		self._parameters = parameters
		self.parameters(self.num_trials-1)
		self._results = {}

	def add_result(self,result:ResultParameters): 
		self._results[result.keyword] = result


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

	def parameters(self,trial_number:int=0) -> MicrolensingParameters:
		if self.trial_variance:
			nspace = {}
			try:
				exec(self.trial_variance,{'old_parameters':self.parameters,'trial_number':trial_number,'u':u,'np':np,'copy':copy,'math':math},nspace)
			except ParametersError as e:
				raise ParametersError("Parameters Error encountered in generating new Parameters instance.")
			except:
				print("What happened")
				raise SyntaxError
			return nspace['new_parameters']
		else:
			return self.parameters

	@property
	def json(self):
		ret = {}
		ret['name'] = self.name
		ret['description'] = self.description
		ret['trial_count'] = self.num_trials
		ret['variation'] = self.trial_variance
		ret['parameters'] = self.parameters.json
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
		

	def __getitem__(self,ind):
		return self._results[ind]

