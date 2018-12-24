from __future__ import division, print_function
from abc import ABC, abstractmethod
import random


from scipy.stats import ks_2samp, anderson_ksamp, mannwhitneyu, energy_distance
from scipy.signal import argrelmax
from scipy.signal import wiener
from scipy.optimize import minimize
from astropy import units as u
import numpy as np

# from matplotlib import pyplot as plt


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
    for ind in range(int(len(lc1)/2-5)):
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
    for ind in range(int(len(lc1)/2-5)):
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
    for i in peak_slices.shape[0]:
        for j in peak_slices.shape[1]:
            asym = ret_asyms[i]
            shifts = ret_shifts[i]
            ret_df.append(i,j,asym,shifts,peak_slices[i,j])
    return ret_df



def calculate_peak_shifts(data:'np.ndarray'):
    shifts = np.ndarray(data.shape,dtype=np.int16)
    for i in range(data.shape[0]):
        baseline = np.argmax(data[i,0])
        for j in range(data.shape[1]):
            shift = abs(np.argmax(data[i,j]) - baseline)
            shifts[i,j] = shift
    return shifts


def step_through_buckets(buccs): 
    for k in sorted(buccs.keys()): 
        bucket = buccs[k] 
        plt.errorbar(np.linspace(1,30,20),bucket['mean'],yerr=bucket['std']) 
        plt.title("Asymmetry = %.2f, N = %d" % (bucket['asym'],bucket['num']))  
        input("Press Enter!")  
        plt.close()

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

   # ...: peaks = map(lambda e: e.get_events(min_separation=20*data[0].parameters.


    # In [120]: def iterator(): 
    #      ...:     peak_batch = next(peaks) #each peak_batch is a LightCurveBatch of isolated events.
    #      ...:     for peak in peak_batch: #Data is the datafile from la.open
    #      ...:         symm = peak.symmetry(20*data[0].parameters.quasar.r_g) 
    #      ...:         ret_asyms.append(symm) 
    #      ...:         lines = data.correlate_lc_peaks([peak],matrix) #matrix is the lookup of all light curves from Result.lookup_matrix
    #      ...:         shifts = calculate_peak_shifts(lines) 
    #      ...:         ret_shifts.append(shifts)


# I need to make a common interface and weigh pros and cons.
# For this, I will pass around query points as well.
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
        total = self._data.append(other._data)
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
        self._data = np.array(data)
        self._start = start
        self._end = end
        self._line_id = line_id

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

    def get_event_slices(self,threshold=0.8,smoothing_factor=1.1,min_separation=u.Quantity(5.0,'uas'),require_isolation=False):
        x = self.distance_axis.to(min_separation.unit)
        dx = x[1] - x[0]
        min_sep = int((min_separation/dx).value)
        peaks = self.get_peaks(threshold,smoothing_factor,min_sep,require_isolation)
        obj_list = []
        for p in peaks:
            s_min = max([0,p-min_sep])
            s_max = min([p+min_sep,len(x)-1])
            obj_list.append(slice(s_min,s_max,1))
        return obj_list


    def get_events(self,threshold=0.8,smoothing_factor=1.1,min_separation=u.Quantity(5.0,'uas'),require_isolation=False):
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

    def smooth_with_window(self,window:int):
        data = self._data
        data = wiener(data,window)
        return LightCurve(data,self._start,self._end,self._line_id)

    # @property
    def symmetry(self,slice_length:u.Quantity):
        line = self.curve
        peak_left_scan = int(len(line)/2 - 1)
        peak = np.argmax(line[peak_left_scan:peak_left_scan+3]) + peak_left_scan
        dist_ax = self.distance_axis.to(slice_length.unit)
        slice_length = int(slice_length/2/(dist_ax[1] - dist_ax[0]))
        slice_length = min([slice_length,peak, len(line) - peak])
        line = line[peak-slice_length+1:peak+slice_length+1]
        min_val = line.min()
        line += abs(min_val)
        line /= line.max()
        l_side = line[1:slice_length+1]
        right_side = line[slice_length:]
        r_flipped = right_side[::-1]
        dw = 2.0/len(line)
        diff = dw*0.5*abs(l_side[0:-1]+l_side[1:] - r_flipped[0:-1] - l_side[1:]).sum()
        return diff
        # possibles = argrelmax(line,order=5)[0] 
        # p1 = possibles[0] 
        # p2 = possibles[0] 
        # for i in possibles: 
        #     if line[i] >= line[p1]: 
        #         p1 = i 
        # if p1 == p2: 
        #     p2 = possibles[1] 
        # for i in possibles: 
        #     if i != p1 and line[i] >= line[p2]: 
        #         p2 = i 
        # curve_min = None
        # slice_length = None
        # l_side = None
        # r_side = None
        # if p2 < p1: 
        #     curve_min = np.argmin(line[p2:p1]) + p2 
        #     slice_length = min([p1-curve_min,len(line)-p1])
        #     l_side = line[curve_min+1:p1+1] 
        #     r_side = line[p1:p1+slice_length].copy()
        # else: 
        #     curve_min = np.argmin(line[p1:p2]) + p1 
        #     slice_length = min([curve_min-p1,p1]) 
        #     l_side = line[p1-slice_length+1:p1+1] 
        #     r_side = line[p1:p1+slice_length].copy()
        #Normalization Step
        # min_val = min([l_side.min(),r_side.min()])
        # l_side += abs(min_val)
        # r_side += abs(min_val)
        # max_val = max([l_side.max(),r_side.max()])
        # l_side /= abs(max_val)
        # r_side /= abs(max_val)
        #To find the difference value, we take the (normalized) lines and take the absolute value of the difference and their integrals
        #Integral simply through a trapezoidal sum.
        # dw = 1.0/(len(l_side)*2)
        # r_flipped = r_side[::-1] 


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
    


class LightCurveClassificationTable(object):

    def __init__(self,curves,p_value_threshold=0.2,method='craimer',maximum_length=None,minimum_height=None,*args,**kwargs):
        # LightCurveBatch.__init__(self,curves,*args,**kwargs)
        if method == 'Craimer':
            self._chooser = CraimerChooser()
        elif method == 'KS':
            self._chooser = KSChooser()
        elif method == 'MannWhitney':
            self._chooser = MannWhitneyChooser()
        elif method == 'AndersonDarling':
            self._chooser = AndersonDarlingChooser()
        elif method == "PeakCounting":
            self._chooser = ExtremaChooser()
        elif method == "Prominence":
            self._chooser = ProminenceChooser()
        elif method == "User":
            self._chooser = UserChooser()
        self._maximum_length = maximum_length
        self._minimum_height = minimum_height
        self._p_threshold = p_value_threshold
        self._table = []
        for curve in curves:
            self.insert(curve)

    def _qualifies(self,lc:LightCurve) -> bool:
        if self._maximum_length != None and lc.length < self._maximum_length:
            return False
        if self._minimum_height != None:
            minimum = lc.curve.min()
            maximum = lc.curve.max()
            if maximum - minimum < self._minimum_height:
                return False
        return True


    def insert(self,lightcurve):
        assert isinstance(lightcurve,LightCurve)
        if self._qualifies(lightcurve):
            if len(self._table) == 0:
                self._table.append([lightcurve])
            else:
                unique, ind = self.get_classification(lightcurve)
                if unique:
                    self._table.append([lightcurve])
                else:
                    self._table[ind].append(lightcurve)
        else:
            pass


    def get_classification(self,curve):
        """Method that gives a "dry-run" classification, saying the index in the table
        that the value falls into, or if it is unique and warrants a new classification be added.
        
        
        Arguments:
            curve {:class:`LightCurve`} -- The light curve to classify.
        Returns:
            unique {`bool`} -- If true, no curve was found that is similar to `curve`
                inside the :class:`LightCurveClassificationTable` instance.
            classification_id {`into`} -- The index in the table where this curve would
            be inserted.
        """
        best_p = self._p_threshold
        best_I = -1
        for curve_typeI in range(self.category_count):
            representative = self.get_representative_curve(curve_typeI)
            if representative:
                p_value = self._chooser.choose(curve,representative)
                if p_value < best_p:
                        best_p = p_value
                        best_I = curve_typeI
        if best_I == -1:
            return (True, self.category_count)
        else:
            return (False, best_I)

    @property
    def category_count(self):
        return len(self._table)

    def describe(self):
        for i in range(len(self._table)):
            print("Group " + str(i) + " with " + str(len(self._table[i])) + " elements.")

    def get_representative_curve(self,cat_ind:int) -> LightCurve:
        try:
            if cat_ind >= len(self._table):
                raise IndexError("curve group " + str(cat_ind) + "does not exist out of the " + str(len(self._table)) + " tabulated curve groups")
            else:
                rand_elem = 0
                if len(self._table[cat_ind]) > 1:
                    rand_elem = random.randint(0,len(self._table[cat_ind])-1)
                return self._table[cat_ind][rand_elem]
        except IndexError as e:
            # print("Catching an indexing error in get_representative_curve.")
            return None

    def __getitem__(self,ind):
        if ind < self.category_count:
            return LightCurveBatch(self._table[ind])
        else:
            raise IndexError("curve group " + str(ind) + "does not exist out of the " + str(len(self._table)) + " tabulated curve groups")

    def __len__(self):
        counter = 0
        for i in self._table:
            counter += len(i)
        return counter

        

class Chooser(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def choose(self,a:LightCurve,b:LightCurve) -> float:
        '''Compares the light curves `a` and `b` and returns the p-value of their similarity.
        
        Abstract method, that must be overriden by :class:`Chooser` sub-classes.
        
        Arguments:
            a {:class:`LightCurve} -- The light curve to compare to curve `b`
            b {:class:`LightCurve`} -- The reference curve for comparison.
        Returns:
            p_value {`float`} -- The p-value ranking for similarity between the two curves. 
            A lower p-value represents curves that are more similar to each other.
        '''
        pass

class CraimerChooser(Chooser):

    def __init__(self):
        Chooser.__init__(self)


    def choose(self,a:LightCurve,b:LightCurve) -> float:
        c1 = a.curve
        c2 = b.curve
        return energy_distance(c1,c2)


class KSChooser(Chooser):

    def __init__(self):
        Chooser.__init__(self)


    def choose(self,a:LightCurve,b:LightCurve) -> float:
        c1 = a.curve
        c2 = b.curve
        d,pv = ks_2samp(c1,c2)
        return pv

class MannWhitneyChooser(Chooser):

    def __init__(self):
        Chooser.__init__(self)

    def choose(self,a:LightCurve,b:LightCurve) -> float:
        c1 = a.curve
        c2 = b.curve
        d,pv = mannwhitneyu(c1,c2)
        return pv

class AndersonDarlingChooser(Chooser):

    def __init__(self):
        Chooser.__init__(self)

    def choose(self,a:LightCurve,b:LightCurve) -> float:
        c1 = a.curve
        c2 = b.curve
        a,c,p = anderson_ksamp([c1,c2])
        return p


class CountingChooser(Chooser):
    def __init__(self):
        Chooser.__init__(self)

    def choose(self,a:LightCurve, b:LightCurve) -> float:
        p1 = self.find_peak_count(a)
        p2 = self.find_peak_count(b)
        if p1 == p2:
            return 0
        else:
            return 1

    def find_peak_count(self,a:LightCurve) -> int:
        pass

class ExtremaChooser(CountingChooser):

    def __init__(self):
        CountingChooser.__init__(self)
        self.min_width = 10
            

    def find_peak_count(self,a:LightCurve) -> int:
        peaks, = argrelmax(a.curve,order=self.min_width)
        return len(peaks)

class FittingChooser(CountingChooser):

    def __init__(self,method='lorentzian'):
        CountingChooser.__init__(self)
        if method == 'lorentzian':
            self._method = _lorentzian
        elif method == 'caustic_crossing':
            from mirage.calculator import caustic_crossing
            self._method = caustic_crossing
        else:
            self._method = _gaussian

    def choose(self,a:LightCurve, b:LightCurve) -> float:
        pass

    def find_peak_count(self,a:LightCurve) -> int:
        pass

    def get_optimal(self,a:LightCurve,num_funcs:int,num_iters):
        x,y0 = a.plottable()
        x = x.value
        x0 = np.ndarray((num_funcs*5))
        for i in range(num_funcs):
            x0[i*5] = x[int(len(a)/num_funcs)]
            x0[i*5+1] = 1
            x0[i*5+2] = 1
            x0[i*5+3] = 1
            x0[i*5+4] = -1

        def min_func(params):
            y = np.zeros_like(x)
            for i in range(num_funcs):
                y += self._method(x,params[i*5],params[i*5+1],params[i*5+2],params[i*5+3],params[i*5+4])
            yy = y - y0
            return (yy*yy).sum()
        return minimize(min_func,x0,method='Nelder-Mead',options={'maxiter':num_iters,'maxfev':num_iters})

class ProminenceChooser(CountingChooser):

    def __init__(self,threshold=12):
        CountingChooser.__init__(self)
        self._threshold = threshold

    def calc_prominence(self,curve,I):
        flag = True
        i = 1
        peak_height = curve[I]
        ret = 1e10
        while flag:
            flag = False
            if I + i < len(curve):
                flag = True
                if curve[I+i] > peak_height:
                    ret = curve[I] - curve[I:I+i].min()
                    break
            if I - i >= 0:
                flag = True
                if curve[I-i] > peak_height:
                    ret = curve[I] - curve[I-i:I].min()
                    break
            i += 1
        return ret

    def prominences(self,line,peaks):
        ret = []
        for i in range(len(peaks)):
            r = self.calc_prominence(line,peaks[i])
            ret.append(r)
        return np.array(ret)

    def find_peak_count(self,curve:LightCurve) -> int:
        line = curve.curve
        possibles, = argrelmax(line)
        proms = self.prominences(line,possibles)
        # print(proms)
        c = 0
        thresh = (line.max() - line.min())/self._threshold
        for i in proms:
            if i > thresh:
                c += 1
        return c

class UserChooser(CountingChooser):

    def __init__(self):
        CountingChooser.__init__(self)
        self._ref = {}


    def find_peak_count(self,curve:LightCurve) -> int:
        from matplotlib import pyplot as plt
        if curve in self._ref:
            return self._ref[curve]
        else:
            plt.figure()
            plt.plot(*curve.plottable())
            response = 0
            while True:
                try:
                    response = input("How many peaks do you see? --> ")
                    if response == "cancel" or response == "exit":
                        return None
                    response = int(response)
                    break
                except:
                    continue
            plt.close()
            self._ref[curve] = response
            return response

def _lorentzian(x,x0,gam,i,*args):
    dx = x-x0
    return i*gam*gam/(dx*dx+gam*gam)

def _gaussian(x,x0,gam,i,*args):
    dx = x - x0
    return i*np.exp(-dx*dx/2/gam/gam)

class CausticTypeChooser(object):
    def __init__(self,width=4):
        self.window_width = width

    def characterize(self,a:LightCurve) -> int:
        try:
            y = a.curve
            peak = np.argmax(y)
            rise_seg = self.get_rise_to(y,peak)
            # plt.figure()/2
            # plt.plot(rise_seg)
            # wait = input("Done?")
            # plt.close()
            interp = np.linspace(rise_seg[0],rise_seg[-1],len(rise_seg))
            delta = (rise_seg - interp).sum()
            return delta/abs(delta)
        except:
            return 2

    def get_rise_to(self,curve:np.ndarray,peak:int):
        left_of = curve[:peak+1]
        right_of = curve[peak:]
        curve_segment = curve
        if left_of[0] < right_of[-1]:
            curve_segment =  left_of[max(0,peak-self.window_width):]
        else:
            curve_segment =  right_of[:min(peak+self.window_width,len(right_of))][::-1]
        return curve_segment



