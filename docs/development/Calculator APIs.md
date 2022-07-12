# Calculation APIs

I want to re-evaluate the way that the system computes lensing results. The approach that's used right now is really rigid.

# Glossary:

+ Successful rays -> Rays that connect observer to source (represented by query region)
+ R -> Number of rays in the bundle
+ S -> Number of stars in the bundle
+ N -> Number of queries in a lens result

# Map-Reduce based System

At the end of the day, `Mirage` is a map-reduce system. So MapReduce is probably
a reasonable way to think about the problem.

## Map Phase: The Ray-Tracer

The map phase is the ray-tracer. We go from a bundle of rays in a grid, deflect them, and sort into a kD-Tree (or Quadtree, or whatever).

Three steps:
+ Generate the bundle of rays `RayGenerator`
+ Deflect the bundle of rays `RayDeflector`
+ Sort into a spatial datastructure `RayDatastructure`

Overall: Go from (`I`, `J`, `LensX`, `LensY`) -> (`I`, `J`, `QuasarX`, `QuasarY`, `Parity`)*

*Parity isn't always necessary, but I include it for the sake of completeness.

## Reduce Phase: Lens Results

Getting lens results is much more variable. My system needs produce:
+ Lightcurves
+ Magnification Maps
+ Parity Maps
+ Image Rendering
+ Extensible to more results in the future.

There are a few different queryables in here:
+ Number of Successful rays per query position
+ The set of succesful rays per query position
+ The statistical moment of successful rays per query position
+ A combination of the three above.

# Implementation Design

I can avoid keeping all partitions in memory and just process chunks and then discard immediately if I can do all my aggregation at one time. So I should make my reducer phase fast and do all steps at once.

I want to support arbitrarily complicated query patterns (counting, statistical moments, parity, etc).

So, abstract what varies. THe code that does the accumulation of all ways for a query needs to be delegated

I'll make a RayReducer delegate that specifies a query to happen and accumulates the result.

```

# NOTE: To make this code fast, everything can be `cdef`ed in the future.

@Dataclass
class RayReducer:
  identifier: ValueIndex
  x: float
  y: float
  radius: float

  def reduce_ray(self, ray: (float64, float64)) -> None:
    """
    Reduces one ray into the RayReducer's internal state.
    """

  def get_result(self) -> float64:
    """
    Get internal value, ready to be saved off in the principal datastructure.
    """

class LensResultReducer:
  def query_iterator() -> Iterator[RayReducer]:
    """
    Returns an iterator of query points and a unique ID for the query point.

    After querying the ray bundle, the ValueIndex is used to save the result
    usign the `save_value` method.
    """

  def save_value(value_id: ValueIndex, value: float64) -> None:
    """
    Given an id for the value you want to save, save the value.
    """

  def merge(self, other: LensResultReducer) -> LensResultReducer:
    """
    Merges the result of this lens reducer with another lens reducer. Returns a new LensResultReducer.
    """
```

