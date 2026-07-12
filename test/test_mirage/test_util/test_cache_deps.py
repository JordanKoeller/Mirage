import pytest
import dataclasses


@dataclasses.dataclass
class MyClass:
  a: int
  b: str
  c: int

  calls: dict[str, int]

  @cache_deps("a", "b")
  def call_a_b(self, arg1, arg2):
    calls["call_a_b"] = (self.a, self.b, arg1, arg2)
    return f"{b}: {self.a * arg1} - {arg2}"

  @cache_deps("c")
  def call_c(self, arg1, **kwargs):
    calls["call_c"] = (self.c, arg1, kwargs)
    return f"{arg1}: {self.a} - {kwargs}"
