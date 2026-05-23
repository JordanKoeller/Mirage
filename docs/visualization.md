# Lensed Image Visualization

All Visualization tools are in the `viz` package, which generally follows a
model-view-controller architecture.


TODO: Fill in details about the MVC design.


## Real-Time Result Visualization

It is possible to have a persistent connection to an engine so that results
are visualized as they are produced.

This can be accomplished by providing RealTimeParameters whe calling `la.visualize`.

## Implementation Details

Under the hood, when RealTimeParameters are provided a `RealTimeVizState` is constructed,
which includes a connection to an Engine. This object is comparable to the regular `VizState`
but computes `SimulationResult`s on-the-fly instead reading from-file.
