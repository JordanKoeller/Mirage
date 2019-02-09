# cython: cdivision=True
# cython: wraparound=False
# cython: boundscheck=False
# cython: language_level=3

import numpy as np
cimport numpy as np

cdef class LensRenderer:

	def __init__(self,object parameters):
		self.region = parameters.ray_region.resolution.as_value_tuple()

	def blank_frame(self):
		return np.zeros(self.region,dtype=np.int8)

	cpdef np.ndarray[np.int8_t,ndim=2] get_frame(self,np.ndarray[np.int32_t,ndim=1] pixels):
		cdef np.ndarray[np.uint8_t, ndim=2] frame = np.zeros(self.region,dtype=np.uint8)
		cdef int n, max_ind = len(pixels), w = self.region[0]
		cdef np.int32_t i,j
		for n in range(max_ind):
			j = pixels[n] % w
			i = pixels[n] // w
			frame[i,j] = 1
		return frame

	