cimport numpy as np
# cpdef generate_pixels(object region)

cpdef interpolate(object region, object two_points_list,sample_density)
cpdef arbitrary_slice_axis(pt1,pt2,region,data)
cpdef caustic_characteristic_inplace(np.ndarray[np.float64_t,ndim=2] stars, np.ndarray[np.float64_t,ndim=2] locations, double &macro_convergence, double &macro_shear)
cpdef isolate_caustics(np.ndarray[np.float64_t,ndim=2] magmap, np.ndarray[np.uint8_t, ndim=2] caustics)
