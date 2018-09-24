import numpy as np
from astropy import units as u

from mirage import io
from .Result import Result, Trial
from .MagnificationMap import MagnificationMap
from .LightCurves import LightCurveBatch, LightCurve, LightCurveSlice, \
LightCurveClassificationTable, Chooser, CraimerChooser, KSChooser, \
MannWhitneyChooser, AndersonDarlingChooser, CountingChooser, ExtremaChooser, \
FittingChooser, ProminenceChooser, UserChooser

def load_simulation(filename):
	from mirage.io import SimulationFileManager
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
	if trial_number != None:
		trial = result[trial_number]
		return trial 
	elif sim.num_trials == 1:
		trial = result[0]
		return trial
	else:
		return result

def show_map(filename,trial_number=0):
	trial = load(filename,trial_number)
	view = MagnificationMapView(filename)
	view.display(trial.magmap)
	return (view,trial)

# def load_result(filename):


