import os

if "IS_SIMULATION" in os.environ:
    from main import run_simulation

from mirage import lens_analysis as la
from mirage.util import *
from mirage.parameters import *
import mirage


#Import general things
from astropy import units as u
import numpy as np
from math import *
import math

# A few ipython things to manipulate the environment

try:
    from IPython import get_ipython
    ipython = get_ipython()
    ipython.magic('matplotlib')
    from matplotlib import pyplot as plt
    #cleanup
    del(ipython)
except ImportError:
    print("Running without ipython")
