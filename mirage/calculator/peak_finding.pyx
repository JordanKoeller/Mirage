# cython: cdivision=True
# cython: wraparound=False
# cython: boundscheck=False
# cython: language_level=3
# cython: unraisable_tracebacks=True
import numpy as np
cimport numpy as np
from scipy.stats import sigmaclip
from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.stack cimport stack
from scipy.ndimage import gaussian_filter, sobel
from libc.math cimport sqrt 
# from cython.operator cimport dereference as deref, preincrement as inc

cdef determine_baseline(np.ndarray[np.float64_t,ndim=1] y,double sigma=3.0):
    clipped = sigmaclip(y,sigma,sigma)
    mean = clipped.clipped.mean()
    noise = (clipped.upper + clipped.lower)/2.0
    return (mean, noise)

cpdef find_events(np.ndarray[np.float64_t, ndim=1] line,
    double area_tolerance=1.0, #TBD
    double peak_threshold=1.0,
    int smoothing_window=55,
    int max_length=-1,
    int stitching_max_length=10000000):
    debug = True
    cdef:
        np.ndarray[np.float64_t,ndim=1] threshold_line = gaussian_filter(line,len(line)*3/smoothing_window)
    diff = line - threshold_line
    cdef:
        np.ndarray[np.float64_t,ndim=1] integral = diff.copy()
    integral[1:] = 0.5*(diff[0:-1] + diff[1:])
    cdef:
        np.ndarray[np.float64_t,ndim=1] cumulative_sum = np.cumsum(integral)
        int i, length = len(cumulative_sum), slice_end
    ret = []
    if debug:
        print("area_tol = %.2f\npeak_thresh = %.2f\nmax_length = %d\nstitch = %d" % (area_tolerance, peak_threshold, max_length, stitching_max_length))
        from matplotlib import pyplot as plt
        plt.plot(line,label="line")
        plt.plot(threshold_line,label="threshold = %d" % smoothing_window)
        plt.legend()
    while i < length:
        if integral[i] > 0:
            slice_end = stitch_end(integral, cumulative_sum, length, stitching_max_length, max_length, i, area_tolerance, peak_threshold)
            if slice_end != -1:
                ret.append([i-1,slice_end])
                i = slice_end + 1
            else:
                i += 1
        else:
            i += 1
    if debug:
        print("Exited find events, having found %d events " % len(ret))
        x_ax = np.arange(len(line))
        for pair in ret:
            plt.plot(x_ax[pair[0]:pair[1]],line[pair[0]:pair[1]])
    return ret

cdef stitch_end(np.ndarray[np.float64_t,ndim=1] integral,
    np.ndarray[np.float64_t, ndim=1] cumsum,
    int line_length,
    int stitch_length,
    int max_length,
    int start_index,
    double area_tolerance,
    double threshold):# nogil:
    cdef:
        int ret, i, next_fall
        int check1, check2
        double a1, a2
    i = start_index
    #Find the end of the current high section
    while i < line_length and integral[i] > 0:
        i += 1
    ret = i
    if i == line_length:
        #short-circuit out now!
        #Don't isolate half of a caustic
        return -1
    elif cumsum[i] - cumsum[start_index] < area_tolerance and integral[start_index:i].max() < threshold:
        #Didn't rise high enough or integrate high enough. short-circuit out.
        return -1
    elif max_length <= 0:
        #IF I HAVE MAX_LENGTH < 0, JUST FIND THE END OF THE CURRENT PEAK AND DON'T TRY TO STITCH
        return ret
    else:
        #Look ahead and see if you can stitch the next high section
        #Have three conditions to meet: 1) The stitch is short enough 2) The total is short enough 3) The value < 0
        check1 = stitch_length + ret
        check2 = max_length + start_index
        while i < line_length and i < check1 and i  < check2 and integral[i] <= 0:
            i += 1
        if integral[i] > 0 and i != line_length and check1 != i and i != check2:
            #Found the next rise point. So recursively call and see if you can add it on.
            next_fall = stitch_end(integral, cumsum, line_length, stitch_length, max_length - i, i, area_tolerance, threshold)
            if next_fall != -1 and (cumsum[next_fall] > area_tolerance + cumsum[i] or integral[i:next_fall].max() > threshold): #Maybe switch to and?
                #Add on the block
                return next_fall
            else:
                #Back-track
                return ret
        else:
            #Escaped out early because hit the end of the array. Time to backtrack.
            return ret


cpdef sobel_detect(np.ndarray[np.float64_t, ndim=1] curve, double threshold, double smoothing_factor, int min_separation, bint require_isolation):
    smoothed = gaussian_filter(curve,smoothing_factor)
    cdef np.ndarray[np.float64_t, ndim=1] sobelled = sobel(smoothed)
    cdef int i,j,length = len(curve), peak_index, k
    cdef stack[int] ret
    cdef double neg_thresh = - threshold
    while i < length:
        #Option 1: We have a positive edge
        if sobelled[i] > threshold:
            j = scan_ahead(sobelled, i, length, threshold) + 1
            #Found the end of the edge. First make sure it didn't hit the end of the curve
            if j != 0:
                #Great. Can now add it to the list
                k = j + min_separation
                peak_index = argmaxI(curve,i,minci(k,length),length)
                #And make sure that it is a RELATIVE max as well.
                if curve[peak_index-1] < curve[peak_index] and curve[peak_index+1] < curve[peak_index]:
                    if ret.size() > 0:
                        #Make sure it is far enough away from last discovered peak
                        if peak_index - ret.top() > min_separation:
                            ret.push(peak_index)
                        else:
                            if not require_isolation:
                                if curve[ret.top()] < curve[peak_index]:
                                    #Prior peak is smaller so replace with larger.
                                    ret.pop()
                                    ret.push(peak_index)
                            else:
                            #     #Requiring isolation. So presence of the current peak invalidates the prior peak.
                                ret.pop()
                    else:
                        ret.push(peak_index)
                    i = k
                else:
                    i = j+1
                # print("Skipping to index %d of %d" % ())
            else:
                i = length * 2
        #Option 2: We have a negative edge
        if sobelled[i] < neg_thresh:
            j = scan_ahead_negative(sobelled, i, length, neg_thresh) + 1
            #Found the end of the edge. First make sure it didn't hit the end of the curve
            if j != 0:
                #Great. Can now add it to the list
                k = i - min_separation
                peak_index = argmaxI(curve,maxci(0,k),j,length)
                # print("Scanning from %d to %d for max." % (maxci(0,2*i-j),j))
                if curve[peak_index-1] < curve[peak_index] and curve[peak_index+1] < curve[peak_index]:
                    if ret.size() > 0:
                        if peak_index - ret.top() > min_separation:
                            ret.push(peak_index)
                        else:
                            if not require_isolation:
                                if curve[ret.top()] < curve[peak_index]:
                                    ret.pop()
                                    ret.push(peak_index)
                            else:
                                ret.pop()
                    else:
                        ret.push(peak_index)
                    i = j + 1
                else:
                    i = j + 1
            else:
                i = length * 2
        #Option 3: We don't have an edge
        else:
            i += 1
    # print("While done. Now copying")
    cdef np.ndarray[np.int32_t,ndim=1] ret_arr =  np.ndarray((ret.size(),),dtype=np.int32)
    i = 0
    while ret.size() > 0:
        ret_arr[i] = ret.top()
        ret.pop()
        i += 1
    return ret_arr

cdef int argmaxI(np.float64_t[:] &line, int a, int b, int line_length) nogil:
    cdef int best = a
    while a < line_length and a < b:
        if line[a] > line[best]:
            best = a
        a += 1
    return best

cdef int argminI(np.float64_t[:] &line, int a, int b, int line_length) nogil:
    cdef int best = a
    while a < line_length and a < b:
        if line[a] > line[best]:
            best = a
        a += 1
    return best

cdef scan_ahead_negative(np.ndarray[np.float64_t, ndim=1] sobelled, int i, int length, double threshold):
    cdef int j = i
    while j < length and sobelled[j] < threshold:
        j += 1
    if j == length:
        return -1
    else:
        return j


cdef scan_ahead(np.ndarray[np.float64_t, ndim=1] sobelled, int i, int length, double threshold):
    cdef int j = i
    while j < length and sobelled[j] > threshold:
        j += 1
    if j == length:
        return -1
    else:
        return j


    


cpdef isolate_events(np.ndarray[np.float64_t, ndim=1] line,
    double tolerance=1.0,
    int smoothing_window=55,
    int max_length=-1,
    int stitching_max_length=10000000,
    double min_height = 0.1):
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

cpdef prominence(np.float64_t[:] &curve, int peak):
    cdef:
        # double local_min = curve[peak]
        double left_min = curve[peak]
        double right_min = curve[peak]
        int i = 1
        int n = curve.shape[0]
        int flag = 0
    while flag == 0:
        if peak + i < n:
            if curve[peak+i] < right_min:
                right_min = curve[peak+i]
            elif curve[peak+i] > curve[peak]:
                return curve[peak] - right_min
        if peak - i >= 0:
            if curve[peak-i] < left_min:
                left_min = curve[peak-i]
            elif curve[peak-i] > curve[peak]:
                return curve[peak] - left_min
        if peak + i >= n and peak - i < 0:
            return curve[peak] - min(left_min,right_min)
        i += 1

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
