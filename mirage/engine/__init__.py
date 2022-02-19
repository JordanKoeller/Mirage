from .CalculationDelegate import MacroCPUDelegate, MicroCPUDelegate
from .SparkCalculationDelegate import MicroSparkDelegate
from .AbstractEngine import EngineHandler
from .ray_tracer import raw_brightness

_sparkdel = MicroSparkDelegate

def getCalculationEngine():
    try:
#        from pyspark import SparkContext
#        if SparkContext._active_spark_context is not None:
        # return EngineHandler(_sparkdel())
#        else:
        ret = EngineHandler(MicroCPUDelegate())
        print("Returning MicroCPUDelegate")
        return ret
    except ImportError:
        pritn("Returning MacroCPUDelegate")
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
