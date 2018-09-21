import numpy as np

from mirage.parameters import MagnificationMapParameters
from mirage.parameters import Simulation
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
		return self._data

	@property	
	def region(self):
		return self._source_plane

	def slice_line(self,start,end):
		start = self.region.loc_to_pixel(start)
		end = self.region.loc_to_pixel(end)
		delta = (end - start)
		length = int(delta.magnitude.value)
		unit_vec = (end - start).unit_vector
		ret = np.ndarray((length))
		for i in range(length):
			loc = start + unit_vec * i
			x = int(loc.x.value)
			y = int(loc.y.value)
			ret[i] = self.data[x,y]
		return ret

	def export(filename,fmt='fits',**kwargs):
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

