

import json
import multiprocessing
import os

import numpy as np

# import random


class _PreferencesParser(object):
  '''
  classdocs
  '''
  _prefMap = {}

  def __init__(self, filename):
    '''
    Constructor
    '''
    self.fileLoc = filename
    with open(self.fileLoc, encoding='utf-8') as file:
      data = json.load(file)
      self._prefMap = data

  def __getitem__(self, key):
    if isinstance(key, str):
      try:
        return self._prefMap[key]
      except KeyError:
        raise KeyError("Preference Not Found")
    else:
      raise KeyError("Key Must Be a String")

  def updatePreferences(self, kv):
    self._prefMap.update(kv)

  def items(self):
    return self._prefMap.items()

  def get_random_int(self):
    return np.random.randint(2**32 - 1)


class _GlobalPreferences(_PreferencesParser):
  """docstring for _GlobalPreferences"""

  def __init__(self, path):
    _PreferencesParser.__init__(self, path)
    from mirage.util import Jsonable
    defaults = _PreferencesParser(project_directory + '.default_preferences.json')

    #Load in defaults
    for k, v in defaults.items():
      if k not in self._prefMap:
        self._prefMap[k] = v

    # Convert from keywords to settings, etc.
    if self['core_count'] == 'all':
      self._prefMap['core_count'] = multiprocessing.cpu_count()
    self._prefMap['dt'] = Jsonable.decode_quantity(self['dt'])
    if self['star_generator_seed'] == None:
      self._prefMap['star_generator_seed'] = self.get_random_int()
    if self['lightcurve_rng_seed'] == None:
      self._prefMap['lightcurve_rng_seed'] == self.get_random_int()
    # if self['use_openCL']:
    #     if self['cl_device'] != 'discover':
    #         os.environ['PYOPENCL_CTX'] = str(self['cl_device'])


project_directory = os.path.abspath(__file__).split('mirage')[0]
GlobalPreferences = _GlobalPreferences(project_directory + '.custom_preferences.json')

def getParametersView(file_or_object=None):
  from mirage.views import ParametersWidget, Window
  window = Window()
  view = ParametersWidget()
  window.bind_widget(view)
  window.show()
  if file_or_object:
    params = None
    from mirage.parameters import Parameters, Simulation
    if isinstance(file_or_object, str):
      from mirage import io
      params = io.open_parameters(file_or_object)
    else:
      if isinstance(file_or_object, Simulation):
        params = file_or_object.parameters
      elif isinstance(file_or_object, Parameters):
        params = file_or_object
    view.set_object(params)
  return window

def getSimulationView(window=None, filename=None):
  from mirage.views import SimulationWidget
  window = window or getParametersView()
  sw = SimulationWidget(window.widget)
  window.bind_widget(sw)
  if filename:
    from mirage.lens_analysis import load_simulation
    window.set_object(load_simulation(filename))
  return window

def getLensedView(params_or_sim):
  from mirage.views import LensView, AnimationController
  from mirage.engine import getVisualEngine
  from mirage.util import Vec2D
  from mirage.parameters import AnimationSimulation
  anim = None
  if isinstance(params_or_sim, AnimationSimulation):
    anim = params_or_sim
    params = params_or_sim.parameters
  else:
    params = params_or_sim
    sp = Vec2D(0.0, 0.0, 'arcsec')
    vel = Vec2D(0, 0, 'arcsec/s')
    anim = AnimationSimulation(params, sp, vel)
  eng = getVisualEngine(params)
  controller = AnimationController(anim, eng)
  eng.update_parameters(params)
  view = LensView("Lens View")
  view.connect_runner(controller)
  return view


def runSimulation(simfile, savefile):
  """
  Entry point function for running a simulation. Given a `.sim` file, computes the described simulation and saves the results to `savefile`.

  Arguments:

  * `simfile` (`str`): The file containing a specification of a simulation to compute. Should have a `.sim` extension.
  * `savefile` (`str`): The filename to save the result of the simulation to. If `savefile` does not have the proper extension, the proper extension (`.res`) will be appended on to `savefile`.

  .. seealso:: This method **does not** include any options for specifying the context that should be used to perform the computation. In order to learn how to choose a context, see |GettingStartedWithMirage|.

  .. warning:: If `savefile` already exists in the file system, this method will overwrite `savefile`!
  """
  from mirage.calculator import ResultCalculator
  from mirage.io import SimulationFileManager
  loader = SimulationFileManager()
  loader.open(simfile)
  sim = loader.read()
  loader.close()
  calculator = ResultCalculator()
  print("Input accepted. Starting computation.")
  print("_____________________________________\n\n")
  saver = calculator.calculate(sim, name=savefile)
  print("Done. All results saved to " + saver.filename)
  try:
    from mirage import lens_analysis as la
    return la.load(saver.filename)
  except:
    return

run_simulation = runSimulation