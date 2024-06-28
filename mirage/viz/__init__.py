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


"""
from .viz import Viz
from .window import VizWindow
from .lensed_image_view import LensedImageView
from .magmap_view import MagmapView
from .viz_runner import VizRunner

__all__ = ["Viz", "LensedImageView", "MagmapView", "VizRunner", "VizWindow"]
