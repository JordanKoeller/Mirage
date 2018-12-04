from .Result import Result, Trial
from .MagnificationMap import MagnificationMap
from .CausticMap import CausticMap
from .LightCurves import LightCurveBatch, LightCurve, LightCurveSlice

def load_simulation(filename):
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
    from mirage.io import ResultFileManager
    fm = ResultFileManager()
    fm.open(filename)
    sim = fm.read()
    result = Result(fm,sim)
    if trial_number is not None:
        trial = result[trial_number]
        return trial 
    elif sim.num_trials == 1:
        trial = result[0]
        return trial
    else:
        return result

def show_map(data,trial_number=0):
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


# def load_result(filename):


