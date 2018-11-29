from datetime import datetime as DT

import numpy as np

from mirage.util import zero_vector,PixelRegion, Region

class ResultCalculator(object):

    def __init__(self):
        pass

    def calculate(self,simulation,name=None):
        from mirage.engine import getCalculationEngine
        from mirage.io import ResultFileManager
        print("Started Computation at %s" % str(DT.now()))
        #initialize the filemanager
        filemanager = ResultFileManager()
        if name:
            fname = name + filemanager.extension
        else:
            fname = simulation.name + filemanager.extension
        filemanager.open(fname)
        #Start calculating
        engine = getCalculationEngine()
        simulation.set_trial(0)
        # print("ERROR: NEEDS TO DETERMINE IF RECONFIGURING NECESSARY")
        num_trials = simulation.num_trials
        for trial_number in range(num_trials):
            start_time = DT.now()
            filemanager.next_trial()
            simulation.set_trial(trial_number)
            params = simulation.parameters
            engine.update_parameters(params)
            results = self.calculate_trial(simulation, engine)
            for result in results:
                filemanager.write(result)
            elapsed_time = DT.now() - start_time
            elapsed_sec = elapsed_time.total_seconds()
            start_time = DT.now()
            print("Finished Trial %d in %d hours, %d minutes, and %d seconds." \
             % (trial_number,elapsed_sec//3600,(elapsed_sec//60)%60,elapsed_sec%60))
        filemanager.close_simulation(simulation)
        filemanager.close()
        return filemanager


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
        if 'causticmap' in simulation:
            resolution = simulation['causticmap'].resolution
            pr = PixelRegion(zv,dims,resolution)
            pts = pr.pixels.to(params.eta_0)
            ret = engine.query_caustics(pts.value,radius)
            results.append(ret)
        return results



