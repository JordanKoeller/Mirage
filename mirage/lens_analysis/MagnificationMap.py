import numpy as np


from mirage.util import PixelRegion, zero_vector


class MagnificationMap(object):

    def __init__(self,simulation,data):
        sp = simulation.parameters.source_plane
        theta_E = simulation.parameters.theta_E
        r = simulation['magmap'].resolution
        self._source_plane = PixelRegion(zero_vector(theta_E),sp.dimensions.to(theta_E),r)
        self._data = data

    @property
    def data(self):
        return 2.5*np.log10(self._data+0.001)

    @property    
    def region(self):
        return self._source_plane

    def slice_line(self,start,end):
        from mirage.calculator import arbitrary_slice_axis
        return arbitrary_slice_axis(start,end,self.region,self.data)


    def export(self,filename,fmt='fits',**kwargs):
        '''
        Saves the magnification map image to the specified file.
        
        Parameters:
        
        `filename` (:class:`str`): Name of the file to save the map to.
        `fmt` (:class:`str`): File format to use. Options include `fits`, `png`, `jpeg`. Note that with `fits`, a default header
        is also included, describing the map. Default option is `fits`.
        If additional keyword arguments are supplied and `fmt` is `fits`, then the extra arguments will be converted to strings
        and saved in the `fits` header.
        '''

        if fmt == 'fits':
            from mirage.io import FITSFileManager
            fm = FITSFileManager()
            fm.open(filename+'.'+fmt)
            # headers = {''}
            fm.write(self.data,**kwargs)
            fm.close()
            return "Magmap saved to " + filename + '.' + fmt
        else:
            print("NEED TO DECIDE WHAT TO DO IF NOT SAVING TO FITS")

