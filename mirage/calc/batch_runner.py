from multiprocessing import Process
import logging


from mirage.calc.dask_engine import DaskEngine
from mirage.sim import Experiment
from mirage.util import (
    BidiStream,
    ClusterProvider,
    Stopwatch,
)
from mirage.io import ResultFileManager

logger = logging.getLogger(__name__)


class BatchRunner:
    def __init__(
        self,
        experiment: Experiment,
        output_filename: str,
        cluster_provider: ClusterProvider,
    ):
        self.experiment: Experiment = experiment
        self.output_filename: str = output_filename
        self.cluster_provider = cluster_provider

    @staticmethod
    def _engine_main(
        experiment: Experiment,
        bidi_stream: BidiStream,
        cluster_provider: ClusterProvider,
    ):
        try:
            engine = DaskEngine(
                bidi_stream=bidi_stream, cluster_provider=cluster_provider
            )
            engine.blocking_run_simulation(experiment)
            logger.info("Terminating Engine")
        except Exception as e:
            bidi_stream.close()
            logger.error("Engine Encountered an error: ")
            raise e

    def start(self):
        timer = Stopwatch()
        timer.start()
        send, recv = BidiStream.create(10)

        engine_process = Process(
            name="EngineProcess",
            target=BatchRunner._engine_main,
            args=(self.experiment, send, self.cluster_provider),
        )

        engine_process.start()  # This starts the engine in a separate process
        serializer = ResultFileManager(self.output_filename, "x")
        serializer.dump_experiment(self.experiment)
        flag = True
        try:
            while flag:
                try:
                    result_event = recv.recv(blocking=True)
                except EOFError:
                    logger.info("EngineProcess Closed. Saving and quiting")
                    flag = False
                    break
                serializer.dump_result(
                    result_event.result, result_event.simulation_key
                )
        except Exception as e:
            logger.error("Encountered Error!")
            logger.error(str(e))
        finally:
            serializer.close()
            logger.info("Result saved to %s", self.output_filename)
            engine_process.join()  # After UI is closed, terminate engine
            timer.stop()
            logger.info("Total Runtime: %ss", timer.total_elapsed_seconds())
