# distutils: language = c++
from libcpp.vector cimport vector


cdef extern from "ckd_tree.h":
  cdef cppclass CKDTree:
      CKDTree()
      CKDTree(double*, unsigned long, unsigned long, unsigned long)
      unsigned long PointsInCircle(double, double, double)
      void PointsInCircle(double*, unsigned long, double, double*)
      double MagnificationCoefficient(double, double, double)
      void MagnificationCoefficient(double*, unsigned long, double, double*)
      vector[int] LensPlaneCoordinates(double, double, double)
      unsigned long size()
      unsigned long buf_size()
      unsigned long tree_size()
      unsigned long queried_nodes_count()
      unsigned long queried_points_count()
