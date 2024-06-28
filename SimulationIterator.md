# SimulationIterator

There's some awkwardness behind how simulations are sent to the engine. I think
it comes from the `Simulation` class.

The `Simulation` keeps everything unified, which is nice from a user point of
view for defining an experiment, but doesn't give the flexibility for multiple
iterations.

Another approach would be a `SimulationTemplate` approach:

## SimulationTemplate:

```


@dataclass(frozen=True)
SimulationMemo:
  ray_tracer: RayTracer
  reducers: list[Reducer]
  label: str | None

class SimulationTemplate:

  def get_experiment(self) -> SimulationMemo
    """
    Generator to get tuple[RayTracer, list[Reducer]] for executing an experiment.

    Each time this is called, the next "Simulation" should be resolved and
    returned.

    Called until None is returned, meaning all "Simulation"s have been created.

    May also return an Optional[str] `label` to give a "name" to the experiment.
    This name is used to look up the result of the simulation after it is computed.

    The labels do not have to be unique - if a label already existed, it will be
    postfixed with a `.$i`, where `i` is an int counting how many times that label
    has been seen.

    Example:
      myLabel.0 - The result of the first simulation labeled with "myLabel".
      myLabel.1 - The result of the second simulation labeled with "myLabel".
      myLabel.2 - The result of the third simulation labeled with "myLabel".

    """
```

## Isn't this just the SimulationBatch?

No. This is a replacement of the `Simulation`. The key difference is that the 
`Simulation` is no longer the source of truth of an execution. Instead it is a 
generator of the (ray_tracer, reducers) that control execution. This decouples
the Simulation from the execution itself, enabling a many-to-one relationship
between `SimulationTemplate` and an execution.
