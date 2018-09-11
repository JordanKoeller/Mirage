from .CalculationDelegate import MacroCPUDelegate
from .SparkCalculationDelegate import MicroSparkDelegate
from .AbstractEngine import EngineHandler

_sparkdel = MicroSparkDelegate()

def getCalculationEngine():
	return EngineHandler(_sparkdel)