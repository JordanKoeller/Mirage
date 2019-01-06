
from mirage.io import ResultFileManager
from mirage.parameters import Simulation#, MagnificationMapParameters, LightCurvesParameters

import numpy as np
from astropy import units as u


class Result(object):

    def __init__(self,file_manager:ResultFileManager, simulation:Simulation):
        self._fm = file_manager
        self._sim = simulation


    def __getitem__(self,ind):
        if isinstance(ind,int):
            if ind < self.num_trials:
                return Trial(self.file_manager, self.simulation, ind)
            else:
                raise IndexError("Item %d does not exist in Result of size %d" % (ind,self.simulation.num_trials))


    @property
    def num_trials(self):
        return self.simulation.num_trials

    @property
    def simulation(self):
        return self._sim

    @property
    def file_manager(self):
        return self._fm
    
    def __len__(self):
        return self.num_trials

    @property
    def lightcurve_matrix(self):
        matrix_dims = (self.num_trials,self.simulation['lightcurves'].num_curves)
        lc_matrix = np.ndarray(matrix_dims, dtype=object)
        lightcurve_data_index = self.simulation.keys.index('lightcurves')
        for i in range(self.num_trials):
            lc_matrix[i] = self._fm.get_result(i,lightcurve_data_index)
        return lc_matrix

    def correlate_lc_peaks(self,peaks:'LightCurveBatch',lc_matrix=None) -> 'np.ndarray[object,ndim=2]':
        #First, I need to construct the lightcurve matrix
        #First axis: the number of trials
        #Second axis: the number of lightcurves per trial
        if lc_matrix is None:
            lc_matrix =  self.lightcurve_matrix()
        ret_matrix = np.ndarray((len(peaks),self.num_trials),dtype=object)
        for pI in range(len(peaks)):
            peak = peaks[pI]
            line_index = peak.line_id
            to_batch = []
            peak_slice = peak.slice_object
            for i in range(self.num_trials):
                ret_matrix[pI,i] = lc_matrix[i,line_index][peak_slice]
        return ret_matrix



def requires(dtype):
    def decorator(fn):
        def decorated(self,*args,**kwargs):
            if dtype in self.simulation:
                index = self.simulation.keys.index(dtype)
                # index = 0
                # if len(self.simulation) > 1:
                #     if dtype == 'magmap':
                #         index = 0
                #     elif dtype == 'lightcurves':
                #         index = 1
                #     elif dtype == 'causticmap':
                #         index = 2
                dataset = self._fm.get_result(self.trial_number,index)
                return fn(self,dataset,*args,**kwargs)
            else:
                raise AttributeError("Trial does not contain " + dtype + " data.")
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
        return self.simulation.parameters

    @property
    @requires('magmap')
    def magmap(self,dataset):
        from mirage.lens_analysis import MagnificationMap
        return MagnificationMap(self.simulation,dataset)

    @property
    @requires('causticmap')
    def caustics(self,dataset):
        from mirage.lens_analysis import CausticMap
        return CausticMap(self.simulation,dataset)

    @property
    @requires('lightcurves')
    def lightcurves(self,dataset):
        from mirage.lens_analysis import LightCurveBatch
        qpts = self.simulation['lightcurves'].line_ends(self.simulation.parameters.source_plane)
        return LightCurveBatch.from_arrays(dataset, qpts,with_id=True)
    

    
