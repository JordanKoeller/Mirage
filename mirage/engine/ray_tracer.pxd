cimport numpy as np

cpdef ray_trace(np.ndarray[np.float64_t, ndim=3] rays,
    double dL,
    double dS,
    double dLS,
    double shear_mag,
    double shear_angle,
    double el_mag,
    double el_angle,
    double b,
    int thread_count)

cpdef int raw_brightness(object parameters)
