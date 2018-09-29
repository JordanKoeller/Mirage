from .CalculationDelegate import MacroCPUDelegate
from .SparkCalculationDelegate import MicroSparkDelegate
from .AbstractEngine import EngineHandler
from .ray_tracer import raw_brightness

_sparkdel = MicroSparkDelegate

def getCalculationEngine():
	return EngineHandler(_sparkdel())