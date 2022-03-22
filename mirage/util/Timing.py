from time import time

class StopWatch:

    def __init__(self):
        self._start_time = None
        self._end_time = None

    def start(self):
        self._start_time = time()

    def stop(self):
        self._end_time = time()

    def refresh(self):
        self._start_time = None
        self._end_time = None

    @property
    def secs(self):
        return (self._end_time - self._start_time)