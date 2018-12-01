import numpy as np
cimport numpy as np

cdef class LensRenderer:

	cdef:
		object region

	cpdef np.ndarray[np.int8_t,ndim=2] get_frame(self,np.ndarray[np.int32_t,ndim=1] pixels)
