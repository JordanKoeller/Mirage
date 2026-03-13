from dataclasses import dataclass
from typing import Iterator
import logging


from mirage.sim import Simulation
from mirage.calc import Reducer, KdTree
from mirage.util import BidiStream, RepeatLogger, Stopwatch, VariantKey

logger = logging.getLogger(__name__)


@dataclass
class ResultEvent:
    result: object
    simulation_key: VariantKey


@dataclass
class Engine:
    bidi_stream: BidiStream

    def blocking_run_simulation(
        self, simulation: Simulation, simulation_key: VariantKey
    ):
        with simulation.special_units():
            logger.info("Starting Simulation. Now ray tracing")
            ray_tracer = simulation.get_ray_tracer()
            rays = simulation.get_ray_bundle().to(
                simulation.lensing_system.theta_0
            )

            traced_rays = ray_tracer.trace(rays)
            logger.info("Traced rays. Now Constructing KdTree")

            rays_tree = KdTree(traced_rays)

            logger.info("Finished building KdTree. Now applying reducers")
            stopwatch = Stopwatch()
            r_logger = RepeatLogger(10, logger)
            for reducer in self.get_reducers(simulation):
                try:
                    self.bidi_stream.recv()
                except EOFError:
                    return  # Short circuit if event channel is closed
                reducer.reduce(rays_tree, simulation)
                self.export_outcome(reducer, simulation_key)
                stopwatch.start()
                if r_logger.log(
                    f"Frame time = {stopwatch.avg_elapsed_seconds()} ms"
                ):
                    stopwatch.reset()
            self.bidi_stream.close()

    def get_reducers(self, simulation: Simulation) -> Iterator[Reducer]:
        """
        Generator that returns all reducers involved in this simulation
        """
        return iter(simulation.get_reducers())

    def export_outcome(self, outcome: object, simulation_key: VariantKey):
        """
        Save off a result of this simulation.
        #"""
        self.bidi_stream.send(ResultEvent(outcome, simulation_key), blocking=True)
