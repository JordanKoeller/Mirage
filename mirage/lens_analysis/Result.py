
from mirage.io import ResultFileManager
from mirage.parameters import Simulation#, MagnificationMapParameters, LightCurvesParameters

class Result(object):

    def __init__(self,file_manager:ResultFileManager, simulation:Simulation):
        self._fm = file_manager
        self._sim = simulation


    def __getitem__(self,ind):
        return Trial(self.file_manager, self.simulation, ind)

    @property
    def simulation(self):
        return self._sim

    @property
    def file_manager(self):
        return self._fm
    


def requires(dtype):
    def decorator(fn):
        def decorated(self,*args,**kwargs):
            if dtype in self.simulation:
                index = 0
                if len(self.simulation) > 1:
                    if dtype == 'magmap':
                        index = 0
                    elif dtype == 'lightcurves':
                        index = 1
                dataset = self._fm.get_result(self.trial_number,index)
                return fn(self,dataset,*args,**kwargs)
            else:
                raise AttributeError("Trial does not contain "+dtype +" data.")
        setattr(decorated,'__doc__',getattr(fn, '__doc__'))
        return decorated
    return decorator



class Trial(object):

    def __init__(self,file_manager:ResultFileManager, simulation:Simulation, index:int):
        self._fm = file_manager
        simulation.set_trial(index)
        self._sim = simulation
        self._index = index

    @property
    def trial_number(self):
        return self._index
    
    @property
    def simulation(self):
        return self._sim

    @property
    def parameters(self):
        return self.simulation.parameters(self._index)

    @property
    @requires('magmap')
    def magmap(self,dataset):
        from mirage.lens_analysis import MagnificationMap
        return MagnificationMap(self.simulation,dataset)

    @property
    @requires('lightcurves')
    def lightcurves(self,dataset):
        from mirage.lens_analysis import LightCurveBatch
        qpts = self.simulation['lightcurves'].lines(self.simulation.parameters.source_plane)
        return LightCurveBatch(dataset,qpts)
    

    