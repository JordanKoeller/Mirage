# distutils: language=c++
# cython: profile=False, boundscheck=False, wraparound=False
# cython: cdivision=True
# cython: language_level=3


cdef class QueryAccumulator:

    """
    Ingest in a ray and add it to the accumulator
    """
    cpdef void reduce_ray(self, const double[:] ray):
        pass

    """
    Return the final accumulator value
    """
    cpdef double get_result(self):
        return 0.0

    cpdef Query query_point(self):
        return Query(0.0, 0.0, 0.0)

cdef class LensReducer:

    """
    Merge this reducer with another of the same type.
    """
    cpdef LensReducer merge(self, LensReducer other):
        return self

    """
    Create a copy of this LensReducer that is empty with no
    values saved in it yet.
    """
    cpdef LensReducer clone_empty(self):
        return self

    """
    Given a key and value, save off the value to 
    the reducer.
    """
    cpdef void save_value(self, double value):
        pass

    """
    Returns the enclosed value of this reducer.

    This typically returns a numpy array.
    """
    cpdef object value(self):
        return "Not Implemented"

    """
    Set up internal iterator to start iterating query points
    """
    cpdef void start_iteration(self):
        pass

    """
    Advance iteration
    """
    cpdef QueryAccumulator next_accumulator(self):
        return None

    """
    Indicate if there are more QueryAccumulators to iterate or not
    """
    cpdef bint has_next_accumulator(self):
        return True

    cpdef object transport(self):
        return None