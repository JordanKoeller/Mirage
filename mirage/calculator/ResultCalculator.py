from mirage.util import zero_vector,PixelRegion

class ResultCalculator(object):

	def __init__(self):
		pass

	def run_simulations(self,simulation):
		from mirage.engine import getCalculationEngine
		from mirage.io import SimulationFileManager
		engine = getCalculationEngine()
		num_trials = simulation.num_trials


	def calculate_trial(self,simulation,engine,trial_number):
		params = simulation.parameters(trial_number)
		src_plane = params.source_plane
		radius = pr.quasar.radius.to(params.eta_0)
		results = []
		if 'magmap' in simulation:
			resolution = simulation['magmap'].resolution
			dims = src_plane.dimensions
			zv = zero_vector('rad')
			pr = PixelRegion(zv,dims,resolution)
			pts = pr.pixels.to(params.eta_0)
			ret = engine.query_points(pts.value,radius)
			results.append(ret)
		if 'lightcurves' in simulation:
			lines = simulation['lightcurves'].lines(src_plane)
			scaled = list(map(lambda line: line.to(params.eta_0).value,lines))
			ret = engine.query_points(scaled,radius)
			results.append(ret)
		return results



