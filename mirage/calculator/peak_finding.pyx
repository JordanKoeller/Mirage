# cython: cdivision=True
# cython: wraparound=False
# cython: boundscheck=False

import numpy as np
cimport numpy as np
from scipy.stats import sigmaclip
from libcpp.vector cimport vector
from libcpp.pair cimport pair
from scipy.ndimage.filters import gaussian_filter
from libc.math cimport sqrt 

cdef determine_baseline(np.ndarray[np.float64_t,ndim=1] y,double sigma=3.0):
    clipped = sigmaclip(y,sigma,sigma)
    mean = clipped.clipped.mean()
    noise = (clipped.upper + clipped.lower)/2.0
    return (mean, noise)

cpdef isolate_events(np.ndarray[np.float64_t, ndim=1] line, double tolerance=1.0, int smoothing_window=55,int max_length=-1, int stitching_max_length=10000000,double min_height = 0.1):
#NEW IDEA: Use maximizing summed curvature as a heuristic for when an event has occurred?
    cdef:
        np.ndarray[np.float64_t, ndim=1] x = np.arange(len(line),dtype=np.float64)
        np.ndarray[np.float64_t, ndim=1] threshold_line = gaussian_filter(line,len(line)*3/smoothing_window)
        double deriv_baseline, deriv_noise, deriv_threshold, center, split, scaled, slice_max, slice_min
        int i, cross_I,  event_end, event_start, line_length, num_groups, line_length2, k, j
        vector[pair[int,int]] cross_point_groups, events, events2
        pair[int,int] group1, group2, group3
        int w1, w2, w3
    line_length = len(line) - 1 
    line_length2 = len(line)
    i = 0
    #Identify locations that cross the threshold and get high enough
    with nogil:
        while i < line_length:
            if line[i] >= threshold_line[i]:
                j = i + 1
                while j < line_length and line[j] >= threshold_line[j]: j += 1
                slice_max = -1.0
                slice_min = 1e10
                for k in range(max(0,i-1),j):
                    slice_max = maxc(slice_max,line[k] - threshold_line[k])
                    slice_min = minc(slice_min,line[k] - threshold_line[k])
                if slice_max - slice_min > min_height:
                    cross_point_groups.push_back(pair[int,int](maxci(0,i - 1),minci(line_length2,j+1)))
                i = j + 1
            else:
                i += 1
        cross_I = 0
        num_groups = cross_point_groups.size()
        if num_groups == 0:
            with gil:
                return []
        #Stitch together multi-cross events
        while cross_I < num_groups - 1:
            group1 = cross_point_groups[cross_I]
            group2 = cross_point_groups[cross_I+1]
            if group2.second - group1.first < max_length and group2.first - group1.second < stitching_max_length:
                max_found = -1.0
                for i in range(group1.second,group2.first):
                    max_found = maxc(max_found,absc(line[i] - threshold_line[i]))
                if max_found < tolerance:
                    events.push_back(pair[int,int](group1.first,group2.second))
                    cross_I += 2
                else:
                    events.push_back(group1)
                    cross_I += 1
            else:
                events.push_back(group1)
                cross_I += 1
        if cross_I < num_groups:
            events.push_back(cross_point_groups[cross_I])
    ret = []
    i = 0
    for i in range(0,events.size()):
        slc = [events[i].first,events[i].second]
        ret.append(slc)
    return ret


cpdef find_peaks(np.ndarray[np.float64_t,ndim=1] y, int min_width, double min_height):
    cdef int i,j,k
    cdef np.ndarray[np.float64_t,ndim=1] dy = y[1:] - y[:len(y)-1]
    cdef np.ndarray[np.float64_t,ndim=1] ddy = dy[1:] - dy[:len(dy)-1]
    cdef int line_length = len(y)
    cdef int min_wid2 = min_width/2
    cdef double diff_y = 0.0
    cdef double avg = 0.0
    cdef vector[int] maxes
    j = min_wid2
    while j+min_wid2 < line_length:
        diff_y = ((y[j]-y[j-min_wid2]) + (y[j] - y[j+min_wid2]))/2.0
        if diff_y > min_height:
            k = 0
            for i in range(j-min_wid2,j+min_wid2):
                avg += y[i]
                if y[i] > y[k]:
                    k = i
            # if avg/min_width < 0:
            maxes.push_back(k)
            j += min_wid2
        else:
            j += 1
    cdef np.ndarray[np.int32_t,ndim=1] ret = np.ndarray(maxes.size(),dtype=np.int32)
    for j in range(0,maxes.size()): ret[j] = maxes[j]
    return maxes



cpdef caustic_crossing(np.float64_t[:] &x,double x0, double s, double d,double x_factor,double vert_shift):
    cdef np.ndarray[np.float64_t,ndim=1] ret = np.zeros_like(x)
    cdef int i = 0
    cdef int x_length = len(x)
    cdef double sd2 = s/d/2.0
    cdef double ds4 = 4.0*d/s
    cdef double z, zd
    for i in range(0,x_length):
        z = x_factor*x[i] - x0
        zd = z/d
        if z > sd2:
            ret[i] = ds4*(sqrt(zd+sd2) - sqrt(zd-sd2))
        elif z > -sd2:
            ret[i] = ds4*sqrt(zd+sd2)
    return ret + vert_shift

cdef double min_array(np.float64_t[:] &a,int s, int e) nogil:
    cdef double minn = 1e10
    cdef int i
    for i in range(s,e):
        if a[i] < minn:
            minn = a[i]
    return minn

cdef double max_array(np.float64_t[:] &a,int s, int e) nogil:
    cdef double minn = -1.0
    cdef int i
    for i in range(s,e):
        if a[i] > minn:
            minn = a[i]
    return minn

cdef double maxc(double a, double b) nogil:
    if a > b:
        return a
    else:
        return b

cdef double minc(double a, double b) nogil:
    if a > b:
        return b
    else:
        return a

cdef double absc(double a) nogil:
    return sqrt(a*a)

cdef int maxci(int a, int b) nogil:
    if a > b:
        return a
    else:
        return b

cdef int minci(int a, int b) nogil:
    if a > b:
        return b
    else:
        return a

cdef int absci(int a) nogil:
    return <int> sqrt(a*a)


cpdef prominences(np.float64_t[:] &curve,np.int64_t[:] &peaks):
    cdef:
        int flag = 0
        double peak_height = 0.0
        np.ndarray[np.float64_t,ndim=1] ret = np.zeros_like(peaks,dtype=np.float64) * 1e10
        int i, j, I
        double slice_min
        int peaks_sz = peaks.shape[0]
        int curve_sz = curve.shape[0]
    for j in range(0,peaks_sz):
        I = peaks[j]
        peak_height = curve[I]
        i = 1
        flag = 0
        while flag == 0:
            flag = 1
            if I + i < curve_sz:
                flag = 0
                if curve[i+I] > peak_height:
                    ret[j] = curve[I] - min_array(curve,I,i+I)
                    break
            if I - i >= 0:
                flag = 0
                if curve[I-i] > peak_height:
                    ret[j] = curve[I] - min_array(curve,I-i,I)
                    break
            i += 1
    return ret

cpdef trimmed_to_size_slice(np.float64_t[:] &curve,int slice_length):
    cdef int center, index, i, j
    cdef double tmp, max_found
    cdef int curve_length = len(curve)
    center = 0
    max_found = -1.0
    for i in range(curve_length):
        if curve[i] > max_found:
            max_found = curve[i]
            center = i
    index = center - slice_length
    for i in range(max(center - slice_length,0),center):
        tmp = 0.0
        max_found = -1.0
        for j in range(i,min(i+slice_length,curve_length)):
            tmp += curve[j]
        if tmp > max_found:
            max_found = tmp
            index = i
    return [index,min(index+slice_length,curve_length)]

def old_trimmer(y,slice_length):
        center = np.argmax(y)
        max_found = -1.0
        index = center - slice_length
        for i in range(max(index,0),center):
            tmp = y[i:min(i+slice_length,len(y))].sum()
            if tmp > max_found:
                index = i
                max_found = tmp
        return [index,min(index+slice_length,len(y))]
