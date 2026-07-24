from mirage.util import LRUCache
from unittest import TestCase
import random


class _EmplaceMock:
  def __init__(self, ret: object, size: int) -> None:
    self.ret = ret
    self.size = size
    self.called = 0

  def __call__(self, *ags, **kwargs) -> tuple[object, int]:
    self.called += 1
    return self.ret, self.size


class TestLRUCache(TestCase):
  def test_canAddToEmptyCache(self) -> None:
    cache = LRUCache(100)
    emplace = _EmplaceMock("value", 5)
    cache.lazy_get((0,), emplace)
    assert len(cache) == 1
    assert cache.bytes_size == 5

  def test_dedupsEmplace(self) -> None:
    cache = LRUCache(100)
    emplace = _EmplaceMock("value", 5)
    cache.lazy_get((0,), emplace)
    cache.lazy_get((0,), emplace)
    assert emplace.called == 1
    assert len(cache) == 1
    assert cache.bytes_size == 5

  def test_emplacesUpToCacheSize(self) -> None:
    cache = LRUCache(10)
    emplace = _EmplaceMock("value", 1)
    for i in range(10):
      cache.lazy_get((i,), emplace)
    assert emplace.called == 10
    assert len(cache) == 10
    assert cache.bytes_size == 10

  def test_doesNotDedupOnDifferentKeys(self) -> None:
    cache = LRUCache(100)
    emplace = _EmplaceMock("value", 5)
    cache.lazy_get((1,), emplace)
    cache.lazy_get((0,), emplace)
    assert len(cache) == 2
    assert emplace.called == 2
    assert cache.bytes_size == 10

  def test_evictsIfNotEnoughSize(self) -> None:
    cache = LRUCache(10)
    emplace = _EmplaceMock("value", 6)
    cache.lazy_get((1,), emplace)
    cache.lazy_get((0,), emplace)
    assert len(cache) == 1
    assert emplace.called == 2
    assert cache.bytes_size == 6
    assert (1,) not in cache
    assert (0,) in cache

  def test_evictsUntilEnoughSpace(self) -> None:
    cache = LRUCache(10)
    emplace = _EmplaceMock("value", 1)
    big_emplace = _EmplaceMock("value", 5)
    for i in range(10):
      cache.lazy_get((i,), emplace)
    cache.lazy_get((11,), big_emplace)

    assert len(cache) == 6
    assert emplace.called == 10
    assert big_emplace.called == 1
    assert cache.bytes_size == 10
    for i in range(0, 5):
      assert (i,) not in cache
    for i in range(5, 10):
      assert (i,) in cache
    assert (11,) in cache

  def test_evictsUntilEmptyIfNecessary(self) -> None:
    cache = LRUCache(20)
    emplace = _EmplaceMock("value", 5)
    big_emplace = _EmplaceMock("value", 18)
    for i in range(3):
      cache.lazy_get((i,), emplace)
    cache.lazy_get((4,), big_emplace)
    assert len(cache) == 1
    assert (0,) not in cache
    assert (1,) not in cache
    assert (2,) not in cache
    assert (4,) in cache
    assert cache.bytes_size == 18

  def test_evictsLastAccessed(self) -> None:
    cache = LRUCache(15)
    emplace = _EmplaceMock("value", 5)
    cache.lazy_get((0,), emplace)
    cache.lazy_get((1,), emplace)
    cache.lazy_get((2,), emplace)
    cache.lazy_get((0,), emplace)
    cache.lazy_get((4,), emplace)
    assert len(cache) == 3
    assert (0,) in cache
    assert (4,) in cache
    assert (2,) in cache
    assert cache.bytes_size == 15
    assert emplace.called == 4

  def test_fuzzTest(self) -> None:
    keys = [i for i in range(1000)]
    cache = LRUCache(500)
    emplacers = [_EmplaceMock("v", i) for i in [3, 5, 8, 13, 21, 34, 55, 89]]
    for i in range(100000):
      c = random.choice(keys)
      emplacer = random.choice(emplacers)
      try:
        cache.lazy_get((c,), emplacer)
      except BaseException as e:
        print(cache.bytes_size)
        print(cache.keys())
        print(emplacer.size)
        raise e
