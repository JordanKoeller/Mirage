import os

if "LA_EXIT_ON_COMPLETE" in os.environ:
    from main import run_simulation
    run_simulation(os.environ['LA_INFILE'],os.environ['LA_OUTFILE'])
    import sys
    sys.exit()

if "LA_IS_SIMULATION" in os.environ:
    from main import run_simulation

if os.environ["LA_WITH_GUI"] == "yes":
    try:
        pass
#        from matplotlib import pyplot as plt
#        from IPython import get_ipython
#        get_ipython().magic("matplotlib")
    except:
        print("Matplotlib imported. To run matplotlib interractively with ipython, run the command \n\n>>> %matplotlib")

from mirage import lens_analysis as la
from mirage.util import *
from mirage.parameters import *
import mirage


#Import general things
from astropy import units as u
import numpy as np
import math

# A few ipython things to manipulate the environment
