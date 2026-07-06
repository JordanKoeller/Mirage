from datetime import datetime


class Stopwatch:
    def __init__(self):
        self._start_times = []
        self._end_times = []

    def start(self):
        now = datetime.now()
        if len(self._end_times) < len(self._start_times):
            self._end_times.append(now)
        self._start_times.append(now)

    def stop(self):
        now = datetime.now()
        self._end_times.append(now)

    def reset(self):
        self._start_times = []
        self._end_times = []

    def total_elapsed_seconds(self) -> float:
        start = self._start_times[0]
        end = self._end_times[-1]
        return self._delta_millis(start, end) / 1000

    def avg_elapsed_seconds(self) -> float:
        if len(self._start_times) == 0:
            return 0
        total_millis = 0
        for s, e in zip(self._start_times, self._end_times):
            total_millis += self._delta_millis(s, e)
        return total_millis / len(self._start_times) / 1000

    @property
    def loops(self) -> int:
        return len(self._start_times)

    def _delta_millis(self, start, end) -> int:
        delta = end - start
        delta_t = delta.total_seconds() * 1e6 + delta.microseconds
        return delta_t / 1000

class LabeledStopwatch:

    def __init__(self):
        self.watches: dict[str, Stopwatch] = {}

    def get_or_create_stopwatch(self, label: str) -> Stopwatch:
        if label not in self.watches:
            self.watches[label] = Stopwatch()
        return self.watches[label]

    def print(self, logger: Logger | None = None) -> None:
        logger = logger.info if logger else print
        for label in self.watches:
            watch = self.watches[label]
            logger(
                f"{label}: Elapsed [{watch.loops}] "
                f"{watch.total_elapsed_seconds() * 1000} ms (avg "
                f"{watch.avg_elapsed_seconds() * 1000} ms)"
            )
