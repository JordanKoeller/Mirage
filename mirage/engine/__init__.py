from .CalculationDelegate import MacroCPUDelegate, MicroCPUDelegate
from .SparkCalculationDelegate import MicroSparkDelegate
from .DaskCalculationDelegate import DaskCalculationDelegate
from .AbstractEngine import EngineHandler
from .ray_tracer import raw_brightness

_sparkdel = MicroSparkDelegate

def getCalculationEngine():
    return EngineHandler(DaskCalculationDelegate())
    try:
        ret = EngineHandler(MicroCPUDelegate())
        return ret
    except ImportError:
        return EngineHandler(MacroCPUDelegate())

def getVisualEngine(sim):
	from mirage.parameters import Parameters, MicrolensingParameters
	if isinstance(sim,MicrolensingParameters):
		# print("Chose Micro")
		return EngineHandler(MicroCPUDelegate())
	elif isinstance(sim,Parameters):
		# print("Chose Macro")
		return EngineHandler(MacroCPUDelegate())
	else:
		raise ValueError("sim must be a Parameters instance")
