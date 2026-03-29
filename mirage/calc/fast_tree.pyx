# distutils: language = c++

from mirage.calc cimport ckd_tree
cimport numpy as cnp
from libcpp.vector cimport vector

import numpy as np

cdef class FastTree:
    cdef ckd_tree.CKDTree _tree
    cdef object _data
    cdef unsigned long _leaf_size

    def __init__(self, cnp.ndarray[cnp.float64_t, ndim=3] data, unsigned long leaf_size):
        cdef unsigned long sz = data.shape[0] * data.shape[1]
        if not np.isfortran(data):
            data = np.asfortranarray(data)
        self._data = data
        self._leaf_size = leaf_size
        cdef cnp.float64_t[:, :, :] data_view = self._data
        self._tree = ckd_tree.CKDTree(&data_view[0, 0, 0], sz, data.shape[2], leaf_size)

    def points_in_circle(self, double cx, double cy, double r):
        ret = self._tree.PointsInCircle(cx, cy, r)
        return ret

    def batch_points_in_circle(self, cnp.ndarray[cnp.float64_t, ndim=3] centers, double r):
        cdef cnp.float64_t[:, ::1] ret = np.ndarray((centers.shape[0], centers.shape[1]))
        cdef cnp.float64_t[:, :, ::1] centers_view = centers
        self._tree.PointsInCircle(&centers_view[0,0, 0], centers.shape[0] * centers.shape[1], r, &ret[0, 0])
        return ret

    def magnification_coefficient(self, double cx, double cy, double r):
        return self._tree.MagnificationCoefficient(cx, cy, r)

    def batch_magnification_coefficients(self, cnp.ndarray[cnp.float64_t, ndim=2] centers, double r):
        cdef cnp.float64_t[::1] ret = np.ndarray(centers.shape[0], dtype=np.float64_t)
        cdef cnp.float64_t[:, ::1] centers_view = centers
        self._tree.MagnificationCoefficient(&centers_view[0,0], centers.shape[0], r, &ret[0])
        return ret

    def query_rays(self, double cx, double cy, double r):
        cdef vector[long] indices = self._tree.LensPlaneCoordinates(cx, cy, r)
        cdef cnp.int64_t[::1] ret = np.ndarray((indices.size(),), dtype=np.int64)
        for i in range(0, indices.size()):
            ret[i] = indices[i]
        return ret

    def __reduce__(self):
        return _reducer, (self._data, self._leaf_size)

def _reducer(*args, **kwargs):
    return FastTree(*args, **kwargs)
