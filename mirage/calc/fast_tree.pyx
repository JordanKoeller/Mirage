# distutils: language = c++

from mirage.calc cimport ckd_tree
cimport numpy as cnp

import numpy as np

cdef class FastTree:
    cdef ckd_tree.CKDTree _tree
    cdef object _data

    def __init__(self, cnp.ndarray[cnp.float64_t, ndim=3] data, unsigned long leaf_size):
        cdef unsigned long sz = data.shape[0] * data.shape[1]
        if not np.isfortran(data):
            data = np.asfortranarray(data)
        self._data = data
        cdef cnp.float64_t[:, :, :] data_view = self._data
        self._tree = ckd_tree.CKDTree(&data_view[0, 0, 0], sz, data.shape[2], leaf_size)
        print("Created tree with ", self._tree.tree_size(), " nodes")

    def points_in_circle(self, double cx, double cy, double r):
        ret = self._tree.PointsInCircle(cx, cy, r)
        print("Queried", self._tree.queried_nodes_count(), " nodes,", self._tree.queried_points_count(), "points")
        return ret

    def magnification_coefficient(self, double cx, double cy, double r):
        return self._tree.MagnificationCoefficient(cx, cy, r)
