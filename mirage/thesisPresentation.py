from matplotlib import pyplot as plt
import numpy as np
from mirage import lens_analysis as la


def overlay_sizes(result,num):
    fig = plt.figure()
    for res in result:
        x,y = res.lightcurves[num].plottable("uas")
        plt.plot(x,-y,label=str(res.parameters.quasar.radius.to(res.parameters.xi_0)))
    return fig


#Things I want to show:
    #Start a simulation and let it run while I talk about background.
    #Show magnification maps, and how they vary as a function of quasar size.
    #Show lightcurves, and how variable they are.
    #Show how caustic events shift as a function of quasar size.
    #Hilight the peaks with a + to show peaks more clearly and how they shift.
    #Possible question of interest - how far apart are doublets, typically? Can we constrain
    #The speed of the quasar because of that?
    #Give an example of a fold and a cusp, and analyze the differences.
