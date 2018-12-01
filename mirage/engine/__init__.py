from .CalculationDelegate import MacroCPUDelegate
from .SparkCalculationDelegate import MicroSparkDelegate
from .AbstractEngine import EngineHandler
from .ray_tracer import raw_brightness

_sparkdel = MicroSparkDelegate

def getCalculationEngine():
    try:
        from pyspark import SparkContext
        if SparkContext._active_spark_context is not None:
            return EngineHandler(_sparkdel())
        else:
            return EngineHandler(MacroCPUDelegate())
    except ImportError:
        return EngineHandler(MacroCPUDelegate())