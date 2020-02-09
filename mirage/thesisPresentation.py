import numpy as np

from mirage import lens_analysis as la


def overlay_sizes(result, num):
  from matplotlib import pyplot as plt
  fig = plt.figure()
  for res in result:
    x, y = res.lightcurves[num].plottable("uas")
    label_sz = "%.3f $theta_E$" % res.parameters.quasar.radius.to(res.parameters.theta_E).value
    plt.plot(x, y, label=label_sz)
  return fig

def export_vid(infile, outfile):
  from imageio import get_writer
  from matplotlib import cm
  from matplotlib.colors import Normalize
  norm = Normalize(vmin=-4, vmax=4)
  writer = get_writer(outfile, "mp4", fps=10)
  cmap = cm.BuPu_r
  data = la.load(infile)
  for i in range(data[0].simulation.num_trials):
    mm = data[i].magmap.data
    normald = cmap(norm(mm))
    normald = (normald * 255).astype(np.uint8)
    writer.append_data(normald)
  writer.close()
  print("Video exported to %s" % outfile)

# Things I want to show:
  # Start a simulation and let it run while I talk about background.
  # Show magnification maps, and how they vary as a function of quasar size.
  # Show lightcurves, and how variable they are.
  # Show how caustic events shift as a function of quasar size.
  # Hilight the peaks with a + to show peaks more clearly and how they shift.
  # Possible question of interest - how far apart are doublets, typically? Can we constrain
  # The speed of the quasar because of that?
  # Give an example of a fold and a cusp, and analyze the differences.
