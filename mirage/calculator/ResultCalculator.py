import numpy as np

from mirage.util import zero_vector,PixelRegion, Region

class ResultCalculator(object):

	def __init__(self):
		pass

	def calculate(self,simulation,name=None):
		from mirage.engine import getCalculationEngine
		from mirage.io import ResultFileManager
		#initialize the filemanager
		filemanager = ResultFileManager()
		fname = simulation.name + filemanager.extension
		filemanager.open(fname)
		#Start calculating
		engine = getCalculationEngine()
		num_trials = simulation.num_trials
		for trial_number in range(num_trials):
			filemanager.next_trial()
			simulation.set_trial(trial_number)
			params = simulation.parameters
			engine.update_parameters(params)
			results = self.calculate_trial(simulation, engine)
			for result in results:
				filemanager.write(result)
		filemanager.close_simulation(simulation)
		filemanager.close()
		return engine


	def calculate_trial(self,simulation,engine):
		params = simulation.parameters
		src_plane = params.source_plane
		radius = params.quasar.radius.to(params.eta_0)
		dims = src_plane.dimensions
		zv = zero_vector('rad')
		results = []
		if 'magmap' in simulation:
			resolution = simulation['magmap'].resolution
			pr = PixelRegion(zv,dims,resolution)
			pts = pr.pixels.to(params.eta_0)
			ret = engine.query_points(pts.value,radius)
			results.append(ret)
		if 'lightcurves' in simulation:
			region = Region(zv,dims)
			lines = simulation['lightcurves'].lines(region)
			scaled = np.array(list(map(lambda line: line.to(params.eta_0).value,lines)))
			ret = engine.query_points(scaled,radius)
			results.append(ret)
		return results



