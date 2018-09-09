# # from abc import ABC, abstractmethod, abstractmethod

# class EngineHandler(object):

# 	def __init__(self,engine):
# 		self._engine = engine
# 		self._parameters = None


# 	def update_parameters(self,params:Parameters,force_recalculate=False) -> bool:
# 		if not self._parameters or force_recalculate or self.parameters.is_similar(params):
# 			self._parameters = params
# 			self.calculation_delegate.reconfigure(self.parameters)
# 			return True
# 		else:
# 			self._parameters = params
# 			return False

# 	@property
# 	def calculation_delegate(self):
# 		return self._calculation_delegate
	
# # class 