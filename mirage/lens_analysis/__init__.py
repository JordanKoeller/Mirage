from .Result import Result, Trial
from .MagnificationMap import MagnificationMap
from .CausticMap import CausticMap
from .LightCurves import LightCurveBatch, LightCurve, LightCurveSlice




def load_simulation(filename):
    """
    
    Convenience function for loading a |Simulation| instance specified in the file named `filename`.

    If more data is included in the file, terminates reading at the ending of the |Simulation| specification.

    Arguments:

    * `filename` (`str`): File containing JSON specifying a |Simulation| instance. Accepted file extensions include `.sim`, `.res`, `.msim`. Note that `.msim` files return a |AnimationSimulation| instance.
    """
    from mirage.io import SimulationFileManager, AnimationFileManager
    try:
        fm = AnimationFileManager()
        fm.open(filename)
        ret = fm.read()
        fm.close()
        return ret
    except:
        fm = SimulationFileManager()
        fm.open(filename)
        ret = fm.read()
        fm.close()
        return ret


def load(filename,trial_number=None):
    """
    Function for loading in the results of a simulation.

    Arguments:

    * `filename` (`str`): File containing the results of a simulation. Accepts files with the `.res` extension.
    * `trial_number` (`int`): If specified, returns a |Trial| instance with all the information and results
    of that specific trial. 
    
    Returns:

    * If `trial_number` is unspecified, return a |Result| instance. Else, returns a |Trial| instance.

    """
    from mirage.io import ResultFileManager
    fm = ResultFileManager()
    fm.open(filename)
    sim = fm.read()
    result = Result(fm,sim)
    if trial_number is not None:
        trial = result[trial_number]
        return trial 
    else:
        return result

def show_map(data,trial_number=0):
    """
    Convenience function for automatically loading in a simulation and displaying the enclosed magnification map.

    Arguments:

    * `filename` (`str`): The file to load data in from.
    * `trial_number` (`int`): The trial number of the magnification map you want displayed. Default: `0`

    Returns:

    * `view` (|MagnificationMapView|): The created view instance.
    * `trial` (|Trial|): The trial information for the magnification map being displayed.

    """
    from mirage.views import MagnificationMapView
    if isinstance(data,Trial):
        trial = data
        trial_number = trial.trial_number
    elif isinstance(data,Result):
        trial = data[trial_number]
    else:
        trial = load(data,trial_number)
    view = MagnificationMapView(trial.simulation.name + (": Trial %d" % trial_number))
    view.display(trial.magmap)
    return view,trial

def animate(simulation):
    """
    Constructs and returns a |LensView|, ready to displayed lensed images of `simulation`.

    Arguments:

    * `simulation` (|AnimationSimulation|) The simulation to animate. 

    Returns:

    * |LensView|

    """
    from mirage.parameters import AnimationSimulation
    from mirage.views import LensView, AnimationController
    from mirage.engine import getVisualEngine
    if isinstance(simulation,str):
        simulation = load_simulation(simulation)
    view = LensView("Lens View")
    eng = getVisualEngine(simulation.parameters)
    controller = AnimationController(simulation,eng)
    eng.update_parameters(simulation.parameters)
    view.connect_runner(controller)
    return view

def describe(filename_or_result_type):
    """
    Convenience function to print a synopsis of the data included in a file, |Result|, or |Trial| instance.
    """
    if isinstance(filename_or_result_type,str):
        filename_or_result_type = load(filename_or_result_type)
    print(filename_or_result_type.simulation)


# def load_result(filename):


