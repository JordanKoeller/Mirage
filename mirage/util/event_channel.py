from dataclasses import dataclass
from typing import Any, Optional, Tuple, Self, TypeVar, Generic
from multiprocessing import Queue
import queue
from enum import IntEnum
import logging
import time
import threading

logger = logging.getLogger(__name__)

MAX_TIMEOUT = 300  # seconds

T = TypeVar("T")


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
    def close_event(cls, needs_response: bool) -> Self:
        return cls(StructuredEventType.CLOSE, needs_response)

    @classmethod
    def payload_event(cls, payload: Any) -> Self:
        return cls(StructuredEventType.PAYLOAD, payload)

    @property
    def closed(self) -> bool:
        return self.event_type == StructuredEventType.CLOSE

    @property
    def empty(self) -> bool:
        return self.value is None or self.event_type == StructuredEventType.EMPTY

    @property
    def has_payload(self) -> bool:
        return self.value is not None and self.event_type == StructuredEventType.PAYLOAD


class StreamState(IntEnum):
    OPEN = 0
    SHUTDOWN_STARTING = 1
    SHUTDOWN_COMPLETE = 2


@dataclass
class Message(Generic[T]):
    data: T | None  # None on half_close message.
    half_close: bool = False  # True on the half-close message


class BidiStream(Generic[T]):
    """
    Bidirectional stream for IPC.

    This does NOT support message-passing between machines and is not
    multi-producer / multi-consumer. Only one thread should read from the queue
    or write to the queue at a time.
    """

    def __init__(self, forward_queue: Queue, reverse_queue: Queue) -> None:
        self._forward_queue = forward_queue
        self._reverse_queue = reverse_queue
        self._forward_queue_state = StreamState.OPEN
        self._reverse_queue_state = StreamState.OPEN
        self._shutdown_thread = None

    @classmethod
    def create(cls, max_size: int = 0) -> tuple[Self, Self]:
        forward_queue: Queue = Queue(maxsize=max_size)
        reverse_queue: Queue = Queue(maxsize=max_size)
        return (
            cls(forward_queue, reverse_queue),
            cls(reverse_queue, forward_queue),
        )

    def send(self, message: T, blocking: bool = True) -> bool:
        """
        Send a message over the stream.

        This method blocks until the message can be enqueued in the stream, unless
        the optional kwarg `blocking` is set to False.

        Returns a boolean, indicating if the message was successfully sent or not.

        Throws a EOFError if the stream has been closed.
        """
        if self._forward_queue_state != StreamState.OPEN:
            raise EOFError("Forward queue is closing")
        try:
            self._forward_queue.put(Message(data=message, half_close=False), blocking)
            return True
        except queue.Full:
            return False
        except (ValueError, OSError):
            self._forward_queue_state = StreamState.SHUTDOWN_COMPLETE
            raise EOFError("Forward queue is closed")

    def recv(self, blocking: bool = True) -> T | None:
        """
        Receive a message over the queue.

        By default this is a blocking call and waits for a message to arrive.

        If the kwarg `blocking` is set to False, this method does not block and
        will return None if no message is waiting to be consumed.

        Throws a EOFError if the stream has been closed.
        """
        if self._reverse_queue_state == StreamState.SHUTDOWN_COMPLETE:
            raise EOFError("Receiving stream is closed")
        try:
            msg = self._reverse_queue.get(block=blocking)
        except queue.Empty:
            return None
        except (ValueError, OSError):
            self._reverse_queue_state = StreamState.SHUTDOWN_COMPLETE
            raise EOFError("Forward queue is closed")
        if msg.half_close:
            self._reverse_queue_state = StreamState.SHUTDOWN_COMPLETE
            self._reverse_queue.close()
            self.close()
            raise EOFError("Receiving stream is closed")
        return msg.data

    def close(self) -> None:
        """
        Half-closes the bidirectional stream.

        Once called, no more messages can be sent from this side of the stream,
        and a message is sent to the other side of the stream to begin shutting
        down the remote.

        Messages may still be received, until the remote side finishes its
        shutdown routine.
        """
        if self._forward_queue_state != StreamState.OPEN:
            return
        self._forward_queue_state = StreamState.SHUTDOWN_STARTING
        self._shutdown_thread = threading.Thread(target=self._shutdown)
        self._shutdown_thread.start()

    def _shutdown(self) -> None:
        try:
            self._forward_queue.put(Message(data=None, half_close=True), block=True)
        except (ValueError, OSError):
            logging.error("Encountered a shutdown forward-queue while trying to close.")
        self._forward_queue_state = StreamState.SHUTDOWN_COMPLETE
        self._reverse_queue_state = StreamState.SHUTDOWN_STARTING


@dataclass
class DuplexChannel:
    sender: Queue
    receiver: Queue
    _sender_closed: bool = False
    _receiver_closed: bool = False

    @classmethod
    def create(cls, max_size: int = 0) -> Tuple[Self, Self]:
        forward_queue: Queue = Queue(maxsize=max_size)
        reverse_queue: Queue = Queue(maxsize=max_size)
        return (
            cls(forward_queue, reverse_queue),
            cls(reverse_queue, forward_queue),
        )

    def send(self, msg: Any) -> bool:
        """
        Nonblocking attempt to send a message. If the message was sent,
        returns True. Else False.
        """
        if self.sender_closed:
            return False
        msg = StructuredEvent.payload_event(msg)
        try:
            self.sender.put_nowait(msg)
            return True
        except BaseException:
            return False

    def send_blocking(self, msg: Any):
        """
        Blocking send a message. This method will wait for a max of 5
        minutes to send the message. If the message could not be sent
        in 5 minutes an exception is thrown.
        """
        if self.sender_closed:
            return
        msg = StructuredEvent.payload_event(msg)
        self.sender.put(msg, True)

    def recv(self) -> StructuredEvent:
        """
        Non-blocking check to receive a message. If no message is waiting in the inbox or the channel
        has been closed, returns None.
        """
        try:
            structured_event: StructuredEvent = self.receiver.get_nowait()
            return self._recv_helper(structured_event)
        except BaseException:
            return StructuredEvent.empty_event()

    def recv_blocking(self) -> StructuredEvent:
        """
        Blocking check to receive a message. This method waits a max of 5 minutes
        before timing out and throwing an exception.
        """
        structured_event: StructuredEvent = self.receiver.get(True, MAX_TIMEOUT * 100)
        return self._recv_helper(structured_event)

    def close(self):
        try:
            logger.info("Called EventChannel.close()")
            self.sender.put(StructuredEvent.close_event(needs_response=True), True)
            self._sender_closed = True
        except Exception as e:
            logger.info("Encountered an error in close-send:\n%s", e)

        try:
            while not self.receiver_closed:
                logger.debug("Waiting for close() caller to receiv close response")
                logger.debug(f"With queue {self.receiver.qsize()}")
                self.recv_blocking()
                time.sleep(0.1)
        except Exception as e:
            logger.info("Encountered an error in close-recv:\n", e)

    @property
    def sender_closed(self) -> bool:
        return self._sender_closed

    @property
    def receiver_closed(self) -> bool:
        return self._receiver_closed

    @property
    def closed(self):
        return self.sender_closed and self.receiver_closed

    def _recv_helper(self, structured_event: StructuredEvent) -> StructuredEvent:
        if structured_event.closed:
            logger.debug("Recv_blocking got closed response")
            if structured_event.value:  # Needs response
                logger.debug("Recv sending needs_response=True close event")
                self.sender.put(StructuredEvent.close_event(needs_response=False), True)
                self._sender_closed = True
                logger.debug("Response sent")
            self.receiver.close()
            self.receiver.cancel_join_thread()
            logger.debug("Receiver closed")
            self._receiver_closed = True
        return structured_event
