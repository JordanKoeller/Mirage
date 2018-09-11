# from abc import ABC, abstractmethod, abstractmethod
from mirage.parameters import Parameters

class EngineHandler(object):

	def __init__(self,engine):
		self._calculation_delegate = engine
		self._parameters = None


	def update_parameters(self,params:Parameters,force_recalculate=False) -> bool:
		if not self._parameters or force_recalculate or self._parameters.is_similar(params):
			self._parameters = params
			self.calculation_delegate.reconfigure(self._parameters)
			return True
		else:
			self._parameters = params
			return False

	def query_points(self,*args,**kwargs):
		return self.calculation_delegate.query_points(*args,**kwargs)

	@property
	def calculation_delegate(self):
		return self._calculation_delegate
	
# class 