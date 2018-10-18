from mirage import lens_analysis as la
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
    #cleanup
    del(ipython)
    del(get_ipython)
except ImportError:
    print("Running without ipython")