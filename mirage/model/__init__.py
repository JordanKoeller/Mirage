"""
Model
=====

The "Model" consists of all the necessary data to describe a gravitational lensing system.
This system may be macrolensing and/or microlensing.

For the sake of consistency, when documentation says "mirage.model" it is referring to the
python module named "model" that encapsulates the code used to define a Model. When referring
to the concept of a Model (a mathematical model of gravitationl lensing), we use capital-M "Model".

At the high level, a Model is defined as a :py:class:`mirage.model.Lens` (referring to the lensing galaxy)
and a :py:class:`mirage.model.Quasar` (referring to the QSO being lensed.) 
"""

from .quasar import Quasar
from .source_plane import SourcePlane
from .tracing_parameters import TracingParameters
from .lensing_system import LensingSystem
from .starfield import Starfield

from . import impl as lenses