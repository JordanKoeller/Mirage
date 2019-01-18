

def get_renderer(sim):
    from .Renderer import LensRenderer
    return LensRenderer(sim)
    

try:
    from .View import ImageCurveView
    from .MagmapView import MagnificationMapView
    from .LensView import LensView, AnimationController
except ImportError as e:
    print("Warning: Matplotlib not detected. Everything inside the View package is disabled.")
try:
    from .Window import Window
    from .Widgets import ParametersWidget, SimulationWidget
except ImportError as e:
    print("Warning: PyQt5 not detected.")


