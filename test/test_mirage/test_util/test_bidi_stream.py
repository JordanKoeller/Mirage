from unittest import TestCase
import threading

from mirage.util import BidiStream


def stream_echo(rx: BidiStream) -> None:
  while True:
    try:
      msg = rx.recv()
      if msg is None:
        return
      rx.send(msg, blocking=True)
    except EOFError:
      print("Stream closed. Exiting echo thread.")
      return


def stream_send(rx: BidiStream, msgs: list[int]) -> None:
  for msg in msgs:
    rx.send(msg, blocking=True)
  rx.close()


def stream_rcv(rx: BidiStream) -> None:
  while True:
    try:
      msg = rx.recv()
      print("Received", msg)
    except EOFError:
      return


class TestBidiStream(TestCase):
  def testEcho(self):
    tx, rx = BidiStream.create(max_size=10)
    thread = threading.Thread(target=stream_echo, args=(rx,))
    thread.start()
    for i in range(10):
      tx.send(i)
      j = tx.recv()
      self.assertEqual(i, j)
    tx.close()
    thread.join()

  def testSend(self):
    tx, rx = BidiStream.create(max_size=10)
    thread = threading.Thread(target=stream_rcv, args=(rx,))
    thread.start()
    for i in range(10):
      tx.send(i)
    tx.close()
    thread.join()

  def testRecvCanStillReceiveMessagesAfterClosingSender(self):
    tx, rx = BidiStream.create(max_size=10)
    msgs = [i for i in range(10)]
    thread = threading.Thread(target=stream_send, args=(rx, msgs))
    tx.close()
    thread.start()
    for msg in msgs:
      try:
        self.assertEqual(tx.recv(), msg)
      except EOFError:
        return

  def testBidiStreamDoesNotCauseThreadsToHang(self):
    tx, rx = BidiStream.create(max_size=10)
    tx.send("hello")
    msg = rx.recv()
    self.assertEqual(msg, "hello")
    # Do not close tx or rx. Their dtor's should do it
