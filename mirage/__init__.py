import json 
import multiprocessing
import os
import numpy as np
# import random 


class _PreferencesParser(object):
    '''
    classdocs
    '''
    _prefMap = {}
    
    def __init__(self,filename):
        '''
        Constructor
        '''
        self.fileLoc = filename
        with open(self.fileLoc,encoding='utf-8') as file:
            data = json.load(file)
            self._prefMap = data
         
    def __getitem__(self,key):
        if isinstance(key, str):
            try:
                return self._prefMap[key]
            except KeyError:
                raise KeyError("Preference Not Found")
        else:
            raise KeyError("Key Must Be a String")
        
    def updatePreferences(self,kv):
        self._prefMap.update(kv)

    def items(self):
        return self._prefMap.items()

    def get_random_int(self):
        return np.random.randint(2**32-1)
        


class _GlobalPreferences(_PreferencesParser):
    """docstring for _GlobalPreferences"""
    def __init__(self,path):
        _PreferencesParser.__init__(self,path)
        from mirage.util import Jsonable
        defaults = _PreferencesParser(project_directory+'.default_preferences.json')

        #Load in defaults
        for k,v in defaults.items():
            if k not in self._prefMap:
                self._prefMap[k] = v

        #Convert from keywords to settings, etc.
        if self['core_count'] == 'all':
            self._prefMap['core_count'] = multiprocessing.cpu_count()
        self._prefMap['dt'] = Jsonable.decode_quantity(self['dt'])
        if self['star_rng_seed'] == None:
            self._prefMap['star_rng_seed'] = self.get_random_int()
        if self['lightcurve_rng_seed'] == None:
            self._prefMap['lightcurve_rng_seed'] == self.get_random_int()
        # if self['use_openCL']:
        #     if self['cl_device'] != 'discover':
        #         os.environ['PYOPENCL_CTX'] = str(self['cl_device'])

project_directory = os.path.abspath(__file__).split('mirage')[0]
GlobalPreferences = _GlobalPreferences(project_directory+'.custom_preferences.json')