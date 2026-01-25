# distutils: language = c++

from mirage.calc cimport ckd_tree
cimport numpy as cnp

import numpy as np

cdef class KDTree:
    cdef ckd_tree.CKDTree* c_tree_

    def __cinit__(self, cnp.float64_t[::1] data, unsigned long leaf_size):
        cdef unsigned long sz = data.shape[0] * data.shape[1]
        self.c_tree_ = new ckd_tree.CKDTree(&data[0], sz, data.shape[2] > 2, leaf_size)

    def __dealloc__(self):
        del self.c_tree_

    cdef unsigned long points_in_circle(self, double cx, double cy, double r):
        return self.c_tree_.PointsInCircle(cx, cy, r)

    cdef double magnification_coefficient(self, double cx, double cy, double r):
        return self.c_tree_.MagnificationCoefficient(cx, cy, r)
