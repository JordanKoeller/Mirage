# distutils: language = c++

cdef extern from "ckd_tree.h":
  cdef cppclass CKDTree:
      CKDTree(double*, unsigned long, bool, unsigned long)
      unsigned long PointsInCircle(double, double, double)
      double MagnificationCoefficient(double, double, double)
