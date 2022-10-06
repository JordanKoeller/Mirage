# distutils: language=c++
# cython: profile=False, boundscheck=False, wraparound=False
# cython: cdivision=True
# cython: language_level=3

cdef struct Query:
    double x
    double y
    double r

cdef class QueryAccumulator:

    """
    Ingest in a ray and add it to the accumulator
    """
    cpdef void reduce_ray(self, const double[:] ray)

    """
    Return the final accumulator value
    """
    cpdef double get_result(self)

    cpdef Query query_point(self)


cdef class LensReducer:

    """
    Merge this reducer with another of the same type.
    """
    cpdef LensReducer merge(self, LensReducer other)

    """
    Create a copy of this LensReducer that is empty with no
    values saved in it yet.
    """
    cpdef LensReducer clone_empty(self)

    """
    Given a key and value, save off the value to 
    the reducer.
    """
    cpdef void save_value(self, double value)

    """
    Returns the enclosed value of this reducer.

    This typically returns a numpy array.
    """
    cpdef object value(self)

    """
    Set up internal iterator to start iterating query points
    """
    cpdef void start_iteration(self)

    """
    Advance iteration
    """
    cpdef QueryAccumulator next_accumulator(self)

    """
    Indicate if there are more QueryAccumulators to iterate or not
    """
    cpdef bint has_next_accumulator(self)

    cpdef object transport(self)