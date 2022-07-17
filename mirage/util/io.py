from abc import ABC, abstractmethod, abstractproperty
import json
import tempfile

import numpy as np
from astropy.io import fits

class FileManager(ABC):

    def __init__(self):
        self._filename = ''
        self._file = None

    def open(self,filename,force_extension=False):
#        if force_extension or filename[-len(self.extension):] == self.extension:
        self._filename = filename
#        else:
#            self._filename = filename + self.extension
        self._file = "exists"

    @abstractmethod
    def write(self,data):
        pass

    @abstractmethod
    def read(self):
        pass

    @property
    def file(self):
        return self._file

    def close(self):
        if self._file:
            self._file.close()
        else:
            raise EnvironmentError("Cannot close a file that was never opened")

    @abstractproperty
    def extension(self):
        pass

class JsonFileManager(FileManager):

    def __init__(self,class_object,extension):
        self._class_object = class_object
        self._extension = extension

    @property
    def class_object(self):
        return self._class_object

    @property
    def filename(self):
        return self._filename
    
    
    def read(self):
        self._file = open(self._filename,'rb')
        ret_pt = self._file.tell()
        ending = self.find_end(self._file,ret_pt)
        bites = None
        if ending != -1:
            bites = self._file.read(ending - ret_pt)
        else:
            bites = self._file.read()
        decoder = json.JSONDecoder()
        string = str(bites,'utf-8', errors = 'ignore')
        js, ind = decoder.raw_decode(string)
        return self.class_object.from_json(js)

    def write(self,obj:'Jsonable'):
        self._file = open(self._filename,'wb+')
        js = obj.json
        formatted = self.format_json(js)
        self._file.write(bytes(formatted,'utf-8'))
        # self._file.write(b'\x93')

    def find_end(self,file,start_point,end_char=b'\x93'):
        '''Returns the location of the first appearance of `end_char` in `file`, after `start_point`. If `end_char` is never found, returns -1'''
        flag = True
        buf_sz = int(1e6)
        file.seek(start_point)
        last_pt = start_point
        while flag:
            tmp = file.read(buf_sz)
            if end_char in tmp:
                flag = False
                ind = tmp.index(end_char)
                file.seek(start_point)
                last_pt = last_pt + ind
            elif len(tmp) == 0:
                file.seek(start_point)
                flag = False
                last_pt = -1
            else:
                last_pt = file.tell()
                # file.seek(start_point)
        return last_pt

    def format_json(self,js):
        ret = json.dumps(js,indent=2)
        return ret

    @property
    def extension(self):
        return self._extension


def SimulationFileManager():
    from mirage.parameters import Simulation
    return JsonFileManager(Simulation,'.sim')

def AnimationFileManager():
    from mirage.parameters import AnimationSimulation
    return JsonFileManager(AnimationSimulation,'.anim')


def ParametersFileManager():
    from mirage.parameters import Parameters
    return JsonFileManager(Parameters,'.param')


def MicroParametersFileManager():
    from mirage.parameters import MicrolensingParameters
    return JsonFileManager(MicrolensingParameters,'.mp')

class ResultFileManager(FileManager):

    def __init__(self):
        FileManager.__init__(self)

    def open(self,filename):
        self._filename = filename
        self.trialCount = 0
        self._pfw = SimulationFileManager()
        self._lookup = []
        # self._file = open(self._filename,'ab+')
        self._tmpfile = tempfile.TemporaryFile()

    def write(self,result):
        self._lookup[-1].append(self._tmpfile.tell())
        np.save(self._tmpfile,result.value)

    def next_trial(self):
        self._lookup.append([])

    def close_simulation(self,simulation):
        lookup_np = np.array(self._lookup,dtype=np.int)
        self._pfw.open(self._filename,force_extension=True)
        self._pfw.write(simulation)
        file = self._pfw.file
        np.save(file,lookup_np)
        ResultFileManager.copy_to_from(file,self._tmpfile)

    def close(self):
        self._pfw.close()

    def read(self):
        self._pfw.open(self._filename,force_extension=True)
        self._simulation = self._pfw.read()
        file = self._pfw.file
        # file.read()
        self._lookup = np.load(file)
        self._lookup_shift = file.tell()
        return self._simulation

    def get_result(self,trial,result_index):
        shift = self._lookup[trial,result_index] + self._lookup_shift
        self._pfw.file.seek(shift)
        return np.load(self._pfw.file)

    def get_simulation(self):
        return self._simulation

    @property
    def extension(self):
        return '.res'

    @property
    def filename(self):
        return self._filename

    @staticmethod
    def copy_to_from(dest,src):
        src.seek(0)
        buff = int(1e6)
        chunk = src.read(buff)
        while len(chunk) > 0:
            dest.write(chunk)
            chunk = src.read(buff)






class FITSFileManager(FileManager):
    '''
    classdocs
    '''



    def __init__(self):
        '''
        Constructor
        '''
        FileManager.__init__(self)
        
    def write(self,data,**headerFields):
        header = fits.Header(headerFields)
        hdu = fits.PrimaryHDU(data,header=header)
        hdulist = fits.HDUList([hdu])
        hdulist.writeto(self._filename)

    def read(self,with_headers=False):
        hdulist = fits.open(self._filename)
        if not with_headers:
            return hdulist[0].data
        else:
            return hdulist[0].data,hdulist[0].header

        
    def close(self):
        pass
        
    @property
    def extension(self):
        return ".fits"

def open_parameters(filename):
    if '.res' in filename or '.sim' in filename:
        from mirage import lens_analysis as la
        params = la.load_simulation(filename).parameters
        return params
    else:
        fm = None
        if '.mp' in filename:
            fm = MicroParametersFileManager()
        else:
            fm = ParametersFileManager()
        fm.open(filename)
        params = fm.read()
        fm.close()
        return params

