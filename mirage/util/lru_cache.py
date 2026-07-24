from dataclasses import dataclass
from typing import Any
import logging

from .conversions import size_to_bytes, bytes_to_size


logger = logging.getLogger(__name__)


@dataclass
class _CacheNode:
  key: tuple
  value: Any
  size: int
  index: int
  prev_node: int | None
  next_node: int | None


class LRUCache:
  """
  Implements a simple LRU-Cache.

  The cache is configured with a max size, and will accumulate until that size is
  met. After which, it will begin evicting based on the LRU algorithm.

  Args:
    max_size: (str | int) - Specify how large the LRU cache footprint is allowed
        to be. If a string is provided, it should be a human
        number of bytes (like '5G'), or the number of bytes
        as an int.

  ---

  The datastructure is implemented as a Linked List over an array, with a
  dict for fast key lookups.
  """

  def __init__(self, max_size: str | int) -> None:
    if isinstance(max_size, str):
      max_size = size_to_bytes(max_size)
    self._max_size = max_size
    self._consumed_bytes = 0
    self._items: dict[tuple, Any] = {}
    self._holes: list[int] = []
    self._priority_queue: list[_CacheNode] = []
    self._priority_queue_head = None
    self._priority_queue_back = None

  def __contains__(self, key: tuple, *args, **kwargs) -> bool:
    return key in self._items

  def keys(self) -> list[tuple]:
    return [k for k in self._items.keys()]

  @property
  def bytes_size(self) -> int:
    """
    Returns the total size of cached values in bytes.
    """
    return self._consumed_bytes

  def __len__(self, *args, **kwargs) -> int:
    return len(self._items)

  def lazy_get(self, key: tuple, func: callable[None, tuple(Any, int)]) -> Any:
    """
    get a value from the cache, or lazily construct and insert into the cache.

    If the key is not already in the cache then func() will be called to
    create the value, and inserted into the cache before returning.

    Args:
      key: A unique identifier key for the cached value.
      func: () -> tuple[Any, int] - A parameterless function, returning a
          tuple of the object and a size hint as bytes.
    """
    if key in self._items:
      node = self._items[key]
      self._move_to_back(key)
      return node.value
    obj, size = func()
    if size > self._max_size:
      raise ValueError(
        f"Key {key} has size {bytes_to_size({size})}, which exceeds max of {bytes_to_size(self._max_size)}."
      )
    while self._consumed_bytes + size > self._max_size:
      self._evict_front()
    self._insert_value(key, obj, size)
    logger.debug(
      f"Adding obj {key} of {bytes_to_size(size)} size (total={bytes_to_size(self._consumed_bytes)})"
    )
    return obj

  def _insert_value(self, key: tuple, obj: Any, size: int) -> None:
    node = _CacheNode(key, obj, size, 0, self._priority_queue_back, None)
    self._consumed_bytes += size
    self._items[key] = node
    inserted = None
    if not self._holes:
      inserted = len(self._priority_queue)
      self._priority_queue.append(node)
    else:
      inserted = self._holes[-1]
      self._holes.pop()
      self._priority_queue[inserted] = node
    node.index = inserted
    if self._priority_queue_head is None:
      self._priority_queue_head = inserted
    if self._priority_queue_back is not None:
      self._priority_queue[self._priority_queue_back].next_node = inserted
    self._priority_queue_back = inserted

  def _evict_front(self) -> None:
    if self._priority_queue_head is None:
      raise ValueError("Tried to evict an empty cache.")
    head_ind = self._priority_queue_head
    head = self._priority_queue[head_ind]
    self._consumed_bytes -= head.size
    logger.debug(
      f"Evicting back of cache with size {bytes_to_size(head.size)} (total={bytes_to_size(self._consumed_bytes)})"
    )
    if head.next_node is not None:
      self._priority_queue[head.next_node].prev_node = head.prev_node
    if head.prev_node is not None:
      self._priority_queue[head.prev_node].next_node = head.next_node
    self._priority_queue_head = head.next_node
    self._priority_queue[head_ind] = None
    self._holes.append(head_ind)
    del self._items[head.key]

  def _move_to_back(self, key: tuple) -> None:
    node = self._items[key]
    if self._priority_queue_back == node.index:
      return
    if node.prev_node is not None:
      self._priority_queue[node.prev_node].next_node = node.next_node
    if node.next_node is not None:
      self._priority_queue[node.next_node].prev_node = node.prev_node
    if self._priority_queue_head == node.index:
      self._priority_queue_head = node.next_node
    self._priority_queue[self._priority_queue_back].next_node = node.index
    node.prev_node = self._priority_queue_back
    node.next_node = None
    self._priority_queue_back = node.index
