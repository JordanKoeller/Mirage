from abc import ABC, abstractmethod

class CalculationDependency(ABC):
	"""Abstract base class that specifies any subclasses have attributes that when changed may cause any ray-tracing that has occurred prior to the change to need to be redone.

	There is one abstract method that must be overridden. The :method:`is_similar`, which returns a `bool` specifying if the system must be recalculated.
	""" 

	def __init__(self):
		pass

	@abstractmethod
	def is_similar(self,other:'CalculationDependency') -> bool:
		pass