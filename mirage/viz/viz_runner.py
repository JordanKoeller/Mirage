from multiprocessing import Process, Queue, Pipe
from multiprocessing.connection import Connection
from typing import Tuple
import logging

from astropy import units as u

from mirage.viz import LensedImageView
from mirage.calc.engine import Engine
from mirage.sim import Simulation
from mirage.util import PixelRegion, Vec2D, DuplexChannel
from mirage.calc.reducers import LensedImageReducer

logger = logging.getLogger(__name__)

MAX_RAYS = (5000, 5000)


class VizRunner:

  def __init__(self, simulation: Simulation):
    self.simulation: Simulation = simulation.copy()
    self.normalize_simulation()

  def normalize_simulation(self):
    """
    Prepares the simulation for visualization.

    This means:

    + Ssetting a ray_bundle to a default size for visualization if it does not exist
    or exceed an upper limit.

    + Setting the `reducers` to be only one LensedImageReducer. If a `LensedImageReducer`
    is already present then the existing one is used and any other reducers are removed.

    """

  @staticmethod
  def _engine_main(simulation: Simulation, channel: DuplexChannel):
    engine = Engine(event_channel=channel)
    engine.blocking_run_simulation(simulation)
    logger.info("Terminating Engine")

  def start(self):
    send, recv = DuplexChannel.create(100)

    engine_process = Process(
        name="EngineProcess",
        target=VizRunner._engine_main,
        args=(self.simulation, send),
    )
    vizualizer = LensedImageView(recv)

    engine_process.start()  # This starts the engine in a separate process
    vizualizer.blocking_start()  # Starts the UI (blocking call) in the main thread
    engine_process.join()  # After UI is closed, gracefully terminate engine process
