# distutils: language = c++

from mirage.calc cimport ckd_tree
from math import floor
cimport numpy as cnp
from libcpp.vector cimport vector

import numpy as np

cdef class FastTree:
    cdef ckd_tree.CKDTree _tree
    cdef object _data
    cdef object _indices
    cdef object _splits
    cdef unsigned long _leaf_size

    def __init__(self, cnp.ndarray[cnp.float64_t, ndim=3] data, unsigned long leaf_size,
                 indices=None, splits=None):
        cdef unsigned long sz = data.shape[0] * data.shape[1]
        if not np.isfortran(data):
            data = np.asfortranarray(data)
        self._data = data
        self._leaf_size = leaf_size
        self._indices = indices if indices is not None else np.ndarray(sz, dtype=np.int64)
        self._splits = splits if indices is not None else np.ndarray(max(1, floor(2 * sz / leaf_size - 1)), dtype=np.float64)
        cdef cnp.float64_t[:, :, :] data_view = self._data
        cdef cnp.float64_t[:] splits_view = self._splits
        cdef long[:] indices_view = self._indices
        if indices is not None and splits is not None:
            self._tree = ckd_tree.CKDTree.CreatePreconstructed(&data_view[0, 0, 0], sz, &indices_view[0], &splits_view[0], data.shape[2], leaf_size)
        else:
            self._tree = ckd_tree.CKDTree.Create(&data_view[0, 0, 0], sz, &indices_view[0], &splits_view[0], data.shape[2], leaf_size)

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
        cdef cnp.ndarray[cnp.int64_t, ndim=1] ret = np.ndarray((indices.size(),), dtype=np.int64)
        for i in range(0, indices.size()):
            ret[i] = indices[i]
        return ret

    def __reduce__(self):
        return _pickle, (self._data, self._leaf_size, self._indices, self._splits)

def _pickle(*args, **kwargs):
    return FastTree(*args, **kwargs)
