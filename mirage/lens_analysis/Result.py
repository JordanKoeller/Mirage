
import numpy as np
from astropy import units as u

from mirage.io import ResultFileManager
from mirage.parameters import Simulation


class ResultError(Exception):
  """Error thrown if a result type does not exist within a simulation."""

  def __init__(self, value):
    self.value = value

  def __repr__(self):
    return repr(self.value)


class Result(object):
  """
  Main object for encapsulating a multi-run simulation.
  This is the main entry point for access to |Mirage|'s analysis tools.
  Recommend construction via the :func:`la.load <mirage.lens_analysis.load>` function.

  Note that this object does not perform any calculations itself.
  It is used to analyze the results from simulations that were performed in the past.


  Arguments:

  * `file_manager` (|ResultFileManager|): File manager for interracting with the result data.
  * `simulation` (|Simulation|): Reference to the simulation instance enclosed by the file handled by `file_manager`.
  """

  def __init__(self, file_manager: ResultFileManager, simulation: Simulation):
    self._fm = file_manager
    self._sim = simulation

  def __getitem__(self, ind):
    if isinstance(ind, int):
      if ind < self.num_trials:
        return Trial(self.file_manager, self.simulation, ind)
      else:
        raise IndexError("Item %d does not exist in Result of size %d" %
                         (ind, self.simulation.num_trials))

  @property
  def num_trials(self):
    """
    The number of trials that were computed in this result.
    """
    return self.simulation.num_trials

  @property
  def simulation(self):
    """
    A reference to the |Simulation| object used to construct the |Result| instance.
    """
    return self._sim

  @property
  def file_manager(self):
    """
    Reference to the |ResultFileManager| passed in while constructing the |Result| instance.
    """
    return self._fm

  def __len__(self):
    return self.num_trials

  @property
  def lightcurve_matrix(self):
    """
    Returns a two-dimensional numpy array of all light curves generated across all trials of this simulation.

    Each element of the matrix is a numpy array with the data for a light curve.

    As an example, if `N` many trials were ran, each producing `C` many light curves, the returned array would
    be of shape `(N,C)`.
    """
    matrix_dims = (self.num_trials, self.simulation['lightcurves'].num_curves)
    lc_matrix = np.ndarray(matrix_dims, dtype=object)
    lightcurve_data_index = self.simulation.keys.index('lightcurves')
    for i in range(self.num_trials):
      lc_matrix[i] = self._fm.get_result(i, lightcurve_data_index)
    return lc_matrix

  def event_generator(self, peaks: 'LightCurveBatch', ref_index: int, lc_matrix=None) -> 'np.ndarray[object,ndim=2]':
    """
    Returns a two-dimensional numpy array where each light curve in `peaks` is grouped with the corresponding
    light curve(s) from all other trials.

    As an example, let there be `N` many light curves in `peaks` and `T` many trials. This would produce a matrix
    of dimensions `(N,T)`.

    Arguments:

    * `peaks` (|LightCurveBatch|): The set of light curves to correlate to.
    * `lc_matrix` (`np.ndarray`): The matrix of all light curves computed returned by :func:`lightcurve_matrix`. Providing the matrix saves the |Result| from having to compute the matrix itself, which may save time. If none is supplied, will call :func:`lightcurve_matrix` internally.

    Returns:

    * peak_matrix (`map[np.ndarray]`): The matrix of each light curve grouped with the corresponding light curves from all trials.

    """
    # First, I need to construct the lightcurve matrix
    # First axis: the number of trials
    # Second axis: the number of lightcurves per trial
    from .LightCurves import Event, LightCurve
    if lc_matrix is None:
      lc_matrix = self.lightcurve_matrix()
    ret_matrix = np.ndarray((len(peaks), self.num_trials), dtype=object)
    errors = 0
    for pI in range(len(peaks)):
      try:
        peak = peaks[pI]
        line_index = peak.line_id
        to_batch = []
        peak_slice = peak.slice_object
        s, e = peak.ends
        lid = line_index
        ret_list = [LightCurve(lc_matrix[i, line_index][peak_slice], s, e, lid)
                    for i in range(self.num_trials)]
        yield Event(ret_list, ref_index)
      except IndexError as e:
        errors += 1
    print("Caught %d errors" % errors)


def requires(dtype):
  def decorator(fn):
    def decorated(self, *args, **kwargs):
      if dtype in self.simulation:
        index = self.simulation.keys.index(dtype)
        dataset = self._fm.get_result(self.trial_number, index)
        return fn(self, dataset, *args, **kwargs)
      else:
        raise ResultError("Trial does not contain " + dtype + " data.")
    setattr(decorated, '__doc__', getattr(fn, '__doc__'))
    return decorated
  return decorator


class Trial(object):
  """
  Object for encapsulating all information and results from a single trial of a simulation. This is mostly a container for accessing results, parameters, and the |Simulation| instance associated with a specific trial of a result.

  Note that it is not recommended for constructing a |Trial| directly. A |Trial| instance should be constructed from a |Result| or one of the convenience methods in the |lens_analysis| module.

  Arguments:

  * `file_manager` (|ResultFileManager|): The |ResultFileManager| for handling this trial's data.
  * `simulation` (|Simulation|): the simulation specified in the file handled by `file_manager`.
  * `index` (`int`):  The index of this trial in its simulation.

  """

  def __init__(self, file_manager: ResultFileManager, simulation: Simulation, index: int):
    self._fm = file_manager
    simulation.set_trial(index)
    self._sim = simulation
    self._index = index

  @property
  def trial_number(self):
    """
    the trial number of this |Trial| in the |Result| it was produced from.
    """
    return self._index

  @property
  def simulation(self):
    """
    The |Simulation| instance used to calculate this |Trial|'s data.
    """
    return self._sim

  @property
  def parameters(self):
    """
    convenience function to access the |Parameters| used to specify this trial's lensing system. This attribute is equivalent to accessing the `parameters` attribute on the |Simulation| used to compute this |Trial|.
    """
    return self.simulation.parameters

  @property
  @requires('magmap')
  def magmap(self, dataset):
    """
    Assuming a magnification map was computed with this trial's simulation, returns a |MagnificationMap| instance. If a magnification map was not calculated, raises a |ResultError|.
    """
    from mirage.lens_analysis import MagnificationMap
    return MagnificationMap(self.simulation, dataset)

  @property
  @requires('causticmap')
  def caustics(self, dataset):
    """
    Assuming a caustic map was computed with this trial's simulation, returns a |CausticMap| instance. If a caustic map was not calculated, raises a |ResultError|.
    """
    from mirage.lens_analysis import CausticMap
    return CausticMap(self.simulation, dataset)

  @property
  @requires('lightcurves')
  def lightcurves(self, dataset):
    """
    Assuming a lightcurve batch was computed with this trial's simulation, returns a |LightCurveBatch| instance. If a lightcurve batch was not calculated, raises a |ResultError|.
    """
    from mirage.lens_analysis import LightCurveBatch
    qpts = self.simulation['lightcurves'].line_ends(self.simulation.parameters.source_plane)
    return LightCurveBatch.from_arrays(dataset, qpts, with_id=True)
