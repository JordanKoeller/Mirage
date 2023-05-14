from multiprocessing import Queue
from multiprocessing.connection import Connection
import queue
from typing import Optional
import logging

import numpy as np

from matplotlib import pyplot as plt
from matplotlib import animation

from mirage.util import DuplexChannel

logger = logging.getLogger(__name__)


class LensedImageView:

    def __init__(self, event_channel: DuplexChannel):
        self.fig, self.ax = plt.subplots()
        self.event_channel = event_channel
        self.animation = animation.FuncAnimation(
            self.fig,
            lambda i: self.draw_frame(i),
            interval=1000 / 60,
            blit=True,
            cache_frame_data=False,
        )

    def blocking_start(self):
        self.fig.canvas.mpl_connect("close_event", lambda _: self._terminate())
        plt.show()

    def draw_frame(self, frame_id: int):
        if self.event_channel.closed:
            return []
        frame = self.event_channel.recv()
        if frame is not None:
            logger.info(f"####### Frame {type(frame)}")
            self.ax.clear()
            return [self.ax.imshow(frame, origin="lower")]
        return []

    def _terminate(self):
        logger.info("Closing Visualizer")
        self.event_channel.close()
        plt.close()
