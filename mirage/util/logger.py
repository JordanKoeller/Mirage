from logging import Logger

from mirage.util import Stopwatch


class RepeatLogger:

  def __init__(self, frequency: int, logger: Logger):
    self.frequency: int = frequency
    self.count: int = 0
    self.logger: Logger = logger

  def log(self, message: str) -> bool:
    """
    Logs the message every `every_count` times this method is called

    Returns true if the message was actually logged
    """
    self.count += 1
    if self.count == self.frequency:
      self.logger.info(message)
      self.count = 0
      return True
    return False
