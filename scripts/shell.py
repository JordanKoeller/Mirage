import math
import os

import numpy as np
# Import general things
from astropy import units as u

import mirage
from mirage import lens_analysis as la
from mirage.parameters import *
from mirage.util import *

if "LA_EXIT_ON_COMPLETE" in os.environ:
  from main import run_simulation
  run_simulation(os.environ['LA_INFILE'], os.environ['LA_OUTFILE'])
  import sys
  sys.exit()

if "LA_IS_SIMULATION" in os.environ:
  from main import run_simulation
if os.environ["LA_WITH_GUI"] == "YES":
  try:
    from matplotlib import pyplot as plt
    from IPython import get_ipython
    get_ipython().magic("matplotlib")
  except:
    print("Matplotlib imported. To run matplotlib interractively with ipython, run the command \n\n>>> %matplotlib")


# A few ipython things to manipulate the environment
