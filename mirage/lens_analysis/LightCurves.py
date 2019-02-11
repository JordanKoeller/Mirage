from __future__ import division, print_function
from abc import ABC, abstractmethod
import random


from scipy.stats import ks_2samp, anderson_ksamp, mannwhitneyu, energy_distance
from scipy.signal import argrelmax
from scipy.signal import wiener
from scipy.optimize import minimize
from astropy import units as u
import numpy as np

# 1) Sobell Edge detection working beautifully
# 2) Doublet isolation
# 3) Asymmetry binning - show pulling from bins
# 4) Histograms 
# 5) Best fit line for the peak shift

def get_analyzed_events(filename:str,base,min_sep_coeff,with_peaks=False,**event_finding_args):
    from mirage import lens_analysis as la
    data = la.load(filename)
    matrix = data.lightcurve_matrix
    ret_asyms = []
    ret_shifts = []
    ret_peaks = []
    lc1 = data[base].lightcurves
    r_g = data.simulation.parameters.quasar.r_g
    peaks = map(lambda e: e.get_events(min_separation=min_sep_coeff*r_g,**event_finding_args),lc1)
    err = 0
    for ind in range(int(len(lc1)-1)):
        peak_batch = next(peaks)
        for peak in peak_batch:
            try:
                symm = peak.symmetry(min_sep_coeff*r_g)
                ret_asyms.append(symm)
                lines = data.correlate_lc_peaks([peak],matrix)
                shifts = calculate_peak_shifts(lines)
                ret_shifts.append(shifts)
                if with_peaks:
                    ret_peaks.append(peak.curve)
            except:
                err += 1
    print("Accumulated %d errors of %d total. Error rate of %.2f percent" % (err,len(ret_shifts)+err,100*err/((len(ret_shifts)+err))))
    if with_peaks:
        return {'shifts':ret_shifts, 'asymmetry':ret_asyms, 'peaks':ret_peaks}
    else:
        return {'shifts':ret_shifts, 'asymmetry':ret_asyms}

def get_all_lightcurves(filename:str,base,min_sep_coeff,**event_finding_args):
    from mirage import lens_analysis as la
    data = la.load(filename)
    matrix = data.lightcurve_matrix
    ret_asyms = []
    ret_shifts = []
    ret_peaks = []
    lc1 = data[base].lightcurves
    r_g = data.simulation.parameters.quasar.r_g
    peaks = map(lambda e: e.get_events(min_separation=min_sep_coeff*r_g,**event_finding_args),lc1)
    err = 0
    for ind in range(int(len(lc1)-1)):
        peak_batch = next(peaks)
        for peak in peak_batch:
            try:
                symm = peak.symmetry(min_sep_coeff*r_g)
                ret_asyms.append(symm)
                lines = data.correlate_lc_peaks([peak],matrix)
                shifts = calculate_peak_shifts(lines)
                ret_shifts.append(shifts)
                ret_peaks.append(peak)
            except:
                err += 1
    peak_slices = data.correlate_lc_peaks(ret_peaks, matrix)
    ret_df = []
    for i in range(peak_slices.shape[0]):
        for j in range(peak_slices.shape[1]):
            asym = ret_asyms[i]
            shifts = ret_shifts[i]
            ret_df.append([i,j,asym,shifts,peak_slices[i,j]])
    return ret_df



def calculate_peak_shifts(data:'np.ndarray'):
    shifts = np.ndarray(data.shape,dtype=np.int16)
    for i in range(data.shape[0]):
        baseline = np.argmax(data[i,0])
        for j in range(data.shape[1]):
            shift = abs(np.argmax(data[i,j]) - baseline)
            shifts[i,j] = shift
    return shifts

def into_buckets(dataset):
    buckets = {} 
    for i in range(len(dataset['asymmetry'])): 
        asym = dataset['asymmetry'][i] 
        shifts = dataset['shifts'][i] 
        try: 
            ind = int(float(asym)*100) 
            if ind in buckets: 
                buckets[ind].append(shifts) 
            else: 
                buckets[ind] = [shifts] 
        except: 
            pass 
    return buckets

def bucket_and_clean(dataset): 
    buckets = into_buckets(dataset)
    for k in buckets.keys(): 
        arr = np.array(buckets[k]) 
        mean = np.mean(arr,axis=0) 
        std = np.std(arr,axis=0) 
        buckets[k] = {'mean':mean.flatten(),'std':std.flatten(),'asym':k/100,'num':arr.shape[0]} 
    return buckets

def scatter_buckets(dataset):
    for k in sorted(buckets.keys()):
        asym = k
        for p in buckets[k]:
            plt.plot(p.flatten())
        plt.title(str(k))
    input("Press Enter!")
    plt.close()

def sample_buckets(dataset): 
    for k in sorted(dataset.keys()): 
        asym = k 
        print(len(dataset[k])) 
        for p in dataset[k][0:5]: 
            plt.plot(p.flatten()) 
        plt.title(str(k)) 
        input("Press Enter!") 
        plt.close()


class LightCurveBatch(object):

    def __init__(self,data:'list[LightCurve]'):
        # if isinstance(data,list):
        #     self._data = np.array(data)
        # else:
        self._data = data

    def plottables(self,unit='uas'):
        for curve in self:
            yield curve.plottable(unit)

    def smooth_with_window(self,window:int):
        d2 = self._data.copy()
        for curveI in range(len(self)):
            curve = self._data[curveI]
            d2[curveI] = curve.smooth_with_window(window)
        return LightCurveBatch(d2)

    def __add__(self,other):
        assert isinstance(other,LightCurveBatch)
        total = self._data + other._data
        return LightCurveBatch(total)

    def __getitem__(self,ind):
        if isinstance(ind,int):
            return self._data[ind]
        else:
            return LightCurveBatch(self._data[ind])

    def __len__(self):
        return len(self._data)

    @classmethod
    def from_arrays(cls,data:np.ndarray, query_ends:u.Quantity,with_id=False):
        ret_data = np.ndarray(len(data),dtype=object)
        for i in range(len(data)):
            datum = data[i]
            if len(datum) > 0:
                ends = query_ends[i]
                s = ends[0:2]
                e = ends[2:]
                if with_id:
                    ret_data[i] = LightCurve(datum,s,e,i)
                else:
                    ret_data[i] = LightCurve(datum,s,e)
        return cls(ret_data)



class LightCurve(object):

    def __init__(self,data,start,end,line_id = -1):
        self._data = np.array(data).flatten()
        # print(self._data.shape)
        self._start = start
        self._end = end
        self._line_id = line_id
        self._sample_density = self.distance_axis
        self._sample_density = (self._sample_density[1] - self._sample_density[0]).to('uas')

    def __len__(self):
        return len(self._data)

    def get_slices(self,slices):
        ret1 = list(map(lambda slice_object: self[slice_object],slices))
        return LightCurveBatch(ret1)

    @property
    def line_id(self):
        if self._line_id != -1:
            return self._line_id
        else:
            raise AttributeError("LightCurve instance does not have a trial id.")

    @property
    def sample_density(self):
        return self._sample_density
    
    

    @property
    def ends(self):
        return self._start,self._end
    

    @property
    def curve(self):
        return 2.5*np.log10(self._data)

    @property
    def magnification_curve(self):
        return self._data

    @property
    def query_points(self):
        x = np.linspace(self._start[0].value,self._end[0].value,len(self))
        y = np.linspace(self._start[1].value,self._end[1].value,len(self))
        ret = np.ndarray((len(x),2))
        ret[:,0] = x
        ret[:,1] = y
        return u.Quantity(ret,self._start.unit)

    @property
    def distance_axis(self):
        qpts = self.query_points.value
        x = qpts[:,0]
        y = qpts[:,1]
        xs = x[0]
        ys = y[0]
        diffx = x - xs
        diffy = y - ys
        res = (diffx**2+diffy**2)**0.5
        return u.Quantity(res,self.query_points.unit)

    @property
    def length(self):
        return self.distance_axis[-1]


    def plottable(self,unit='uas'):
        x = self.distance_axis.to(unit)
        y = self.curve
        return x,y

    def get_event_slices(self,threshold=0.8/u.uas,smoothing_factor=1.1*u.uas,min_separation=u.Quantity(5.0,'uas'),require_isolation=False):
        x = self.distance_axis.to(min_separation.unit)
        dx = x[1] - x[0]
        min_sep = int((min_separation/dx).value)
        threshold = (threshold*dx).to('').value
        smoothing_factor = (smoothing_factor/dx).to('').value
        peaks = self.get_peaks(threshold,smoothing_factor,min_sep,require_isolation)
        obj_list = []
        errors = 0
        for p in peaks:
            s_min = max([0,p-min_sep])
            s_max = min([p+min_sep,len(x)-1])
            if s_max - s_min > 3:
                obj_list.append(slice(s_min,s_max,1))
            else:
                errors += 1
        if errors > 0:
            print("Accumulated %d errors" % errors)
        return obj_list


    def get_events(self,threshold=0.8/u.uas,smoothing_factor=1.1*u.uas,min_separation=u.Quantity(5.0,'uas'),require_isolation=False):
        slice_list = self.get_event_slices(threshold, smoothing_factor, min_separation, require_isolation)
        ret = []
        for slicer in slice_list:
            lc = LightCurveSlice(self,slicer.start,slicer.stop,self._line_id)
            ret.append(lc)
        # print("Returning batch with %d events" % len(ret))
        return LightCurveBatch(ret)

    def get_peaks(self,threshold=0.8,smoothing_factor=1.1,min_sep=1,require_isolation=False):
        '''
            Locate peaks of this light curve via a sobel edge detection convolution.
            Recommended settings for my 80k batch, trail 5 R_g:
                threshold = 0.8
                smoothing_factor=1.1
        '''
        from mirage.calculator import sobel_detect
        curve = self._data
        return sobel_detect(curve,threshold,smoothing_factor,min_sep,require_isolation)

    # def get_event_slices(self,threshold=80/u.uas,smoothing_factor=0.011*u.uas,min_separation=u.Quantity(5.0,'uas'),require_isolation=False):
    #     x = self.distance_axis.to(min_separation.unit)
    #     dx = x[1] - x[0]
    #     min_sep = int((min_separation/dx).value)
    #     peaks = self.get_peaks(threshold,smoothing_factor,min_sep,require_isolation)
    #     obj_list = []
    #     for p in peaks:
    #         s_min = max([0,p-min_sep])
    #         s_max = min([p+min_sep,len(x)-1])
    #         obj_list.append(slice(s_min,s_max,1))
    #     return obj_list


    # def get_events(self,threshold=80/u.uas,smoothing_factor=0.011*u.uas,min_separation=u.Quantity(5.0,'uas'),require_isolation=False):
    #     slice_list = self.get_event_slices(threshold, smoothing_factor, min_separation, require_isolation)
    #     ret = []
    #     for slicer in slice_list:
    #         lc = LightCurveSlice(self,slicer.start,slicer.stop,self._line_id)
    #         ret.append(lc)
    #     # print("Returning batch with %d events" % len(ret))
    #     return LightCurveBatch(ret)

    # def get_peaks(self,threshold=80/u.uas,smoothing_factor=0.011*u.uas,min_sep=1,require_isolation=False):
    #     '''
    #         Locate peaks of this light curve via a sobel edge detection convolution.
    #         Recommended settings for my 80k batch, trail 5 R_g:
    #             threshold = 0.8
    #             smoothing_factor=1.1

    #     '''
    #     print(self.sample_density.to('uas')**-1)
    #     threshold = threshold.to('1/uas')
    #     smoothing_factor = smoothing_factor.to('uas')
    #     thresh = threshold*self.sample_density
    #     smoothFac = smoothing_factor/self.sample_density
    #     print("Passing %.3f,%.3f,%.3f" % (thresh.value,smoothFac.value,min_sep))
    #     from mirage.calculator import sobel_detect
    #     curve = self._data
    #     return sobel_detect(curve,0.7,1.1,200,False)
        # return sobel_detect(curve,thresh.value,smoothFac.value,min_sep,require_isolation)

    def smooth_with_window(self,window:int):
        data = self._data
        data = wiener(data,window)
        return LightCurve(data,self._start,self._end,self._line_id)

    @property
    def asymmetry(self):
        line = self.curve
        peak = np.argmax(line)
        slice_length = min(peak,len(line)-peak)-1
        lhs = line[peak-slice_length:peak][::-1]*100
        rhs = line[peak+1:peak+1+slice_length]*100
        diffs = (rhs-lhs)**2
        tot = np.sqrt(diffs.sum())
        return tot

    def __getitem__(self,given):
        if isinstance(given,slice):
            return LightCurveSlice(self,given.start,given.stop,self._line_id)
        elif isinstance(given,int):
            return (self.curve[given],self.query_points[given])
        else:
            raise TypeError("Must give a valid slice object")



class LightCurveSlice(LightCurve):
    def __init__(self,parent_curve,start,stop,line_id=-1):
        qpts = parent_curve.query_points
        curve = parent_curve._data
        begin = qpts[start]
        end = qpts[stop]
        LightCurve.__init__(self,curve[start:stop],begin,end,line_id)
        self._s = start
        self._e = stop
        self._parent_curve = parent_curve

    @property
    def curve_segment(self):
        y = self._parent_curve.curve
        return y[self._s:self._e]

    def plottable_segment(self,unit='uas'):
        x, y = self._parent_curve.plottable(unit)
        x = x[self._s:self._e]
        y = y[self._s:self._e]
        return x, y

    def trimmed_to_size(self,size:u.Quantity):
        from mirage.calculator import trimmed_to_size_slice
        x,y = self.plottable_segment(size.unit)
        dx = x[1] - x[0]
        slice_length = int((size / dx).value)
        slc = trimmed_to_size_slice(y,slice_length)
        return self[slc[0]:slc[1]]

    def __getitem__(self,slc):
        if isinstance(slc,slice):
            start,stop = (slc.start,slc.stop)
            return self.parent_curve[self._s+start:self._s+stop]

    @property
    def slice_object(self):
        return slice(self._s,self._e,1)
    
    @property
    def parent_curve(self):
        return self._parent_curve


class Event(object):

    def __init__(self,light_curves,parent_index):
        self._data = np.array(list(map(lambda l: l._data,light_curves)))
        self._parent_index = parent_index
        self._asymmetry = light_curves[parent_index].asymmetry

    @property
    def asymmetry(self):
        return self._asymmetry

    @property
    def curve(self):
        return self._data[self._parent_index]

    def plot(self):
        from matplotlib import pyplot as plt
        for lc in self._data:
            plt.plot(lc)

    @property
    def shift_array(self):
        maxes = np.argmax(self._data,axis=1)
        return maxes - maxes[0]


class EventClassificationTable(object):

    def __init__(self,events,group_count):
        self._bins = {}
        self._numGroups = group_count
        events = list(events)
        separations = list(map(lambda e: e.asymmetry,events))
        min_sep = min(separations)
        max_sep = max(separations)
        dx = (max_sep - min_sep)/group_count
        get_ind = lambda asym: int(round((asym - min_sep)/dx))
        errors = 0
        for event in events:
            try:
                key = get_ind(event.asymmetry)
                if key not in self._bins:
                    self._bins.update({key:[event]})
                else:
                    self._bins[key].append(event)
            except IndexError as e:
                errors += 1
        # print("Accumuldated %d errors" % errors)
    @property
    def keys(self):
        return list(self._bins.keys())

    def __getitem__(self,idd):
        return self._bins[idd]

    def plot_samples(self,key,num):
        from matplotlib import pyplot as plt
        import random
        bucket = self[key]
        samples = random.sample(bucket,num)
        for sample in samples:
            # Need to normalize our curves
            curve = sample.curve
            curve -= curve.min()
            if curve[0] >= curve[-1]: curve = curve[::-1]
            peak_index = np.argmax(curve)
            x_ax = np.arange(-peak_index,len(curve)-peak_index)
            plt.plot(x_ax,curve)

    def merge_buckets(self,key_list):
        ret = []
        for key in key_list:
            ret = ret + key_list[key]
        return ret

    def __repr__(self):
        lines = "EventClassificationTable"
        for k,v in self._bins.items():
            lines += ("\n\t" + str(k) + " : " + str(len(v)))
        return lines






