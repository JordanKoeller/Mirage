import numpy as np
from astropy import units as u

from mirage import io
from .Result import *

def load_simulation(filename):
	from mirage.io import SimulationFileManager
	fm = SimulationFileManager()
	fm.open(filename)
	ret = fm.read()
	fm.close()
	return ret

def load_result(filename):


