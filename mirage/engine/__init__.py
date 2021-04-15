import os

from .CalculationDelegate import MacroCPUDelegate, MicroCPUDelegate
from .SparkCalculationDelegate import MicroSparkDelegate
from .DaskCalculationDelegate import DaskCalculationDelegate
from .AbstractEngine import EngineHandler
from .ray_tracer import raw_brightness


def getCalculationEngine():
  if 'EXECUTION_ENVIRONMENT' not in os.environ:
    print('Execution environment not set. Assuming local execution.')
    return EngineHandler(MicroCPUDelegate())
  if os.environ['EXECUTION_ENVIRONMENT'] == 'SPARK':
    from pyspark import SparkContext
    if SparkContext._active_spark_context is not None:
      return EngineHandler(MicroSparkDelegate())
    raise EnvironmentError("No active Spark environment.")
  elif os.environ['EXECUTION_ENVIRONMENT'] == 'CPU':
    return EngineHandler(MicroCPUDelegate())
  elif os.environ['EXECUTION_ENVIRONMENT'] == 'DASK':
    from dask.distributed import Client
    client = Client(threads_per_worker=2, n_workers=8) 
    return EngineHandler(DaskCalculationDelegate(client))

def getVisualEngine(sim):
  from mirage.parameters import Parameters, MicrolensingParameters
  if isinstance(sim, MicrolensingParameters):
    # print("Chose Micro")
    return EngineHandler(MicroCPUDelegate())
  elif isinstance(sim, Parameters):
    # print("Chose Macro")
    return EngineHandler(MacroCPUDelegate())
  else:
    raise ValueError("sim must be a Parameters instance")
