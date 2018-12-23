# cython: cdivision=True
# cython: wraparound=False
# cython: boundscheck=False
# cython: language_level=3
# cython: unraisable_tracebacks=True

import numpy as np
cimport numpy as np


cdef determine_baseline(np.ndarray[np.float64_t, ndim=1] y,double sigma=*)

cpdef isolate_events(np.ndarray[np.float64_t, ndim=1] line, double tolerance=*, int smoothing_window=*,int max_length=*, int stitching_max_length=*,double min_height=*)

cpdef find_peaks(np.ndarray[np.float64_t,ndim=1] y, int min_width, double min_height)

cpdef caustic_crossing(np.float64_t[:] &x,double x0, double size, double caustic_strength,double x_factor, double vert_shift)

cdef double min_array(np.float64_t[:] &a,int s, int e) nogil

cpdef prominences(np.float64_t[:] &curve, np.int64_t[:] &peaks)

cpdef trimmed_to_size_slice(np.float64_t[:] &curve,int slice_length)

cpdef find_events(np.ndarray[np.float64_t, ndim=1] line,
    double area_tolerance=*,
    double peak_threshold=*,
    int smoothing_window=*,
    int max_length=*,
    int stitching_max_length=*)

cdef stitch_end(np.ndarray[np.float64_t,ndim=1] integral,
    np.ndarray[np.float64_t, ndim=1] cumsum,
    int line_length,
    int stitch_length,
    int max_length,
    int start_index,
    double area_tolerance,
    double threshold)# nogil

cpdef sobel_detect(np.ndarray[np.float64_t, ndim=1] curve, double threshold, double smoothing_factor, int min_separation, bint require_isolation)