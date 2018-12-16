import os

if "LA_IS_SIMULATION" in os.environ:
    from main import run_simulation


from mirage import lens_analysis as la
from mirage.util import *
from mirage.parameters import *
import mirage


#Import general things
from astropy import units as u
import numpy as np
import math

# A few ipython things to manipulate the environment
