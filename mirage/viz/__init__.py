"""
viz package.
=============

`viz` includes tools for visualizing results from simulations.

Two approaches:

1. Modular approach
2. Superset approach

At the core of it there are three main things I need to visualize - then each
has its own flavor:

    1. Magnification map / parity maps
      1. Image-based
      2. Colorbar-based coloring
      3. May have a need for animation - evolving starfields.
    2. Lensed Images
      1. Image-based.
      2. Explicit coloring.
      3. Have a need for animation and interractivity.
    3. Lightcurves
      1. Two-dimensional
      2. Have need to overlay many curves.

With this in mind, it feels like there are three fundamental views, following
that pattern. But there is some complexity in that we may want to display
multiple views in a unified interface. So it would be good to have that
flexibility.

With that in mind, I'm going to make sure that the render-surface is just an
Axes as defined in matplotlib. Then can have special builders that build
to a new figure, an existing figure, etc.

## API Example

We use a simple object-oriented approach, with a `VizWindow` that acts as the
UI window.

From this window, you can bind an `ExperimentResult` to it. This just associates
the window with a set of Simulation results. By default, it will inspect what
reducers exist in the ExperimentResult and bind reducers in a sensible way. If
there is ambiguity in how the reducers should bind, the user is prompted. Of
course, this can be changed later via an api. Something like 
`window.bind_top_pane('reducer_name')`.

The UI includes arrow buttons to step forward or backward through the set of
simulations in the ExperimentResult.


"""
from .viz import Viz
from .window import VizWindow
from .lensed_image_view import LensedImageView
from .magmap_view import MagmapView
from .viz_runner import VizRunner

__all__ = ["Viz", "LensedImageView", "MagmapView", "VizRunner", "VizWindow"]
