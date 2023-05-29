from abc import ABC, abstractmethod, abstractclassmethod
from typing import TypeVar, Self, Generic, Type, Set, List

from mirage.calc import Reducer

# R = TypeVar('R', Reducer)


class Viz(ABC):
  _registry: List[type] = []

  @abstractmethod
  def show(self, reducer: Reducer):
    """
    Visualize the provided reducer
    """

  @classmethod
  @abstractmethod
  def compatible_reducers(cls) -> List[Type[Reducer]]:
    """
    Returns the list of reducers that can be visualized by this visualizer
    """

  @staticmethod
  def register(klass):
    if not issubclass(klass, Viz):
      raise ValueError("Visualizers must be a subclass of mirage.viz.Viz")
    Viz._registry.append(klass)

  @staticmethod
  def get_visualizer(reducer: Reducer) -> Self:  # type: ignore
    reducer_type = type(reducer)
    for visualizer_type in Viz._registry:
      if reducer_type in visualizer_type.compatible_reducers():  # type: ignore
        return visualizer_type()
    raise ValueError(
        f"Could not find a registered Visualizer for reducer {reducer_type.__name__}. Are you sure"
        " you registered the Visuailzer with @Visualizer.register annotating its definition?"
    )
