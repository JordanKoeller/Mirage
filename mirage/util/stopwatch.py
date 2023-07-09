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

  def total_elapsed(self):
    start = self._start_times[0]
    end = self._end_times[-1]
    return self._delta_micros(start, end)

  def avg_elapsed(self) -> int:
    if len(self._start_times) == 0:
      return 0
    total_micros = 0
    for s, e in zip(self._start_times, self._end_times):
      total_micros += self._delta_micros(s, e)
    return int(total_micros / len(self._start_times))

  @property
  def loops(self) -> int:
    return len(self._start_times)

  def _delta_micros(self, start, end) -> int:
    delta = end - start
    delta_t = delta.total_seconds() * 1e6 + delta.microseconds
    return delta_t / 1000
