from dataclasses import dataclass
from typing import Any, Optional, TypeVar, Tuple, Self, Literal
from multiprocessing import Queue
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)

MAX_TIMEOUT = 300  # seconds


class StructuredEventType(IntEnum):
  PAYLOAD = 0
  CLOSE = 1
  EMPTY = 2


@dataclass
class StructuredEvent:
  event_type: StructuredEventType
  value: Optional[Any] = None

  @classmethod
  def empty_event(cls) -> Self:
    return cls(StructuredEventType.EMPTY)

  @classmethod
  def close_event(cls) -> Self:
    return cls(StructuredEventType.CLOSE)

  @classmethod
  def payload_event(cls, payload: Any) -> Self:
    return cls(StructuredEventType.PAYLOAD, payload)

  @property
  def closed(self) -> bool:
    return self.event_type == StructuredEventType.CLOSE

  @property
  def empty(self) -> bool:
    return self.value is None or self.event_type == StructuredEventType.EMPTY


@dataclass
class DuplexChannel:
  sender: Queue
  receiver: Queue
  _closed: bool = False

  @classmethod
  def create(cls, max_size: int = 0) -> Tuple[Self, Self]:
    forward_queue: Queue = Queue(maxsize=max_size)
    reverse_queue: Queue = Queue(maxsize=max_size)
    return (cls(forward_queue, reverse_queue), cls(reverse_queue, forward_queue))

  def send(self, msg: Any) -> bool:
    """
    Nonblocking attempt to send a message. If the message was sent,
    returns True. Else False.
    """
    msg = StructuredEvent.payload_event(msg)
    try:
      self.sender.put_nowait(msg)
      return True
    except:
      return False

  def send_blocking(self, msg: Any):
    """
    Blocking send a message. This method will wait for a max of 5
    minutes to send the message. If the message could not be sent
    in 5 minutes an exception is thrown.
    """
    msg = StructuredEvent.payload_event(msg)
    self.sender.put(msg, True)

  def recv(self) -> StructuredEvent:
    """
    Non-blocking check to receive a message. If no message is waiting in the inbox or the channel
    has been closed, returns None.
    """
    try:
      structured_event: StructuredEvent = self.receiver.get_nowait()
      if structured_event.closed:
        self.close()
      return structured_event
    except:
      return StructuredEvent.empty_event()

  def recv_blocking(self) -> StructuredEvent:
    """
    Blocking check to receive a message. This method waits a max of 5 minutes
    before timing out and throwing an exception.
    """
    structured_event: StructuredEvent = self.receiver.get(True, MAX_TIMEOUT)
    if structured_event.closed:
      self.close()
    return structured_event

  def close(self):
    # TODO: Implement a close method that blocks and waits for the queue to terminate
    try:
      self.sender.put(StructuredEvent.close_event(), True)
      self.sender.close()
      self.sender.cancel_join_thread()
    except Exception as e:
      logger.info("Encountered an error in close-send:\n", e)

    try:
      while not self.receiver.empty():
        self.recv_blocking()
    except Exception as e:
      logger.info("Encountered an error in close-recv:\n", e)

    self._closed = True

  @property
  def closed(self):
    return self._closed
