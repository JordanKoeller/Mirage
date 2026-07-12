import logging
import logging.handlers
import multiprocessing
import threading
from logging import Logger

logger = logging.getLogger(__name__)

_LOG_FORMAT = (
    "%(asctime)s [%(processName)13s] %(levelname)5s - %(name)12s | %(message)s"
)


def init_multiprocessing_logger(filename: str, level, queue=None):
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"simple": {"format": _LOG_FORMAT}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
                "level": level,
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "simple",
                "filename": filename,
                "level": level,
            },
            "queue_handler": {
                "class": "logging.handlers.QueueHandler",
                "handlers": [
                    "console",
                    "file",
                ],
                "respect_handler_level": True,
                "level": level,
                "queue": {"()": "multiprocessing.Queue"},
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["queue_handler"],
                "level": level,
            }
        },
    }
    logging.config.dictConfig(config)
    queue_handler_logger = logging.getHandlerByName("queue_handler")
    queue_handler_logger.listener.start()
    return queue_handler_logger


def bind_logging_to_queue(logging_queue: multiprocessing.Queue):
    """
    Updates the logging to have the root logger send messages through the provided
    queue.
    """
    queue_handler = logging.handlers.QueueHandler(logging_queue)
    logging.basicConfig(
        format="%(message)s",  # Only send the message. Other properties are bound on the listener-side.
        level=logging.NOTSET,
        handlers=[queue_handler],
    )


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
