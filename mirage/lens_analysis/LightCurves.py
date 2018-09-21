from __future__ import division, print_function
from abc import ABC, abstractmethod
import random


from scipy.stats import ks_2samp, anderson_ksamp, mannwhitneyu, energy_distance
from scipy.signal import argrelmax
from scipy.signal import wiener
from scipy.optimize import minimize, curve_fit
from astropy import units as u
import numpy as np


from mirage.util import Vec2D, zero_vector



class LightCurveBatch(object):


    def __init__(self,data):
        self._data = data

    def plottables(self,unit='uas'):
        for curve in self:
            yield curve.plottable(unit)

    def smooth_with_window(self,window:int):
        data = []
        for curve in self:
            data.append(curve.smooth_with_window(window))
        return LightCurveBatch(data)

    def __add__(self,other):
        assert isinstance(other,LightCurveBatch)
        total = self._data + other._data
        return LightCurveBatch(total)

    def __getitem__(self,ind):
        if isinstance(ind,int):
            if ind < len(self):
                return LightCCurve(self._data[ind])
            else:
                raise IndexError("Index out of range.")
        elif isinstance(ind,slice):
            return LightCurveBatch(self._data[ind])
        else:
            raise ValueError("Could not understand ind as an index or slice.")

    def __len__(self):
        return len(self._data)


class LightCurve(object):


    _scaling = "mag"


    def __init__(self,data,query_points):
        self._data = data.flatten()
        start = query_points[0]
        end = query_points[-1]
        self._start = Vec2D(start[0],start[1],'rad')
        self._end = Vec2D(end[0],end[1],'rad')

    def __len__(self):
        return len(self._data)

    def get_slices(self,slices):
        ret = list(map(lambda slice_object: self[slice_object],slices))
        return LightCurveBatch(ret)

    @property
    def curve(self):
        if self._scaling == "mmag":
            return -2.5*np.log10(self._data+0.1)
        else:
            return self._data

    @property
    def query_points(self):
        x = np.linspace(self._start.x,self._end.x,len(self))
        y = np.linspace(self._start.y,self._end.y,len(self))
        ret = np.ndarray((len(x),2))
        ret[:,0] = x
        ret[:,1] = y
        return u.Quantity(ret,'rad')

    @property
    def distance_axis(self):
        qpts = self.query_points.value
        x = qpts[:,0]
        y = qpts[:,1]
        xs = x[0]
        ys = y[0]
        diffx = x -xs
        diffy = y - ys
        res = (diffx**2+diffy**2)**(0.5)
        return u.Quantity(res,'rad')

    @property
    def length(self):
        return self.distance_axis[-1]


    def plottable(self,unit='uas'):
        x = self.distance_axis.to(unit)
        y = self.curve
        return (x,y)

    def get_event_slice_points(self,tolerance=1.0,
        smoothing_window=55,
        max_length=u.Quantity(1000000,'uas'),
        stitch_length=u.Quantity(1000000,'uas'),
        min_height=1.2):
        from mirage.calculator import isolate_events
        ret = []
        x,curve = self.plottable()
        x = x.to(max_length.unit)
        dx = x[1] - x[0]
        slice_length = int((max_length/dx).value)
        stitch_length = int((stitch_length/dx).value)
        # print("Slice length = " + str(slice_length))
        # print("Stitch length = " + str(stitch_length))
        slice_list = isolate_events(curve,tolerance,smoothing_window,slice_length,stitch_length,min_height)
        return slice_list

    def get_events(self,tolerance=1.0,
        smoothing_window=55,
        max_length=u.Quantity(1000000,'uas'),
        stitch_length=u.Quantity(1000000,'uas'),
        min_height=1.2):
        slice_list = self.get_event_slice_points(tolerance,smoothing_window,max_length,stitch_length,min_height)
        ret = []
        curve = self.curve
        qpts = self.query_points
        for start,end in slice_list:
            slice_x = qpts[start:end]
            slice_y = curve[start:end]
            lc = LightCurveSlice(slice_y,slice_x,start,end,self)
            ret.append(lc)
        return LightCurveBatch(ret)











class LightCurveSlice(LightCurve):
    def __init__(self,data,query_points,slice_start,slice_end,parent_curve):
        LightCurve.__init__(self,data,query_points)
        self._s = slice_start
        self._e = slice_end
        self._parent_curve = parent_curve

    @property
    def curve_segment(self):
        y = self._parent_curve.curve
        return y[self._s:self._e]

    def plottable_segment(self,unit='uas'):
        x,y = self._parent_curve.plottable(unit)
        x = x[self._s:self._e]
        y = y[self._s:self._e]
        return (x,y)

    def trimmed_to_size(self,size:u.Quantity):
        from mirage.calculator import trimmed_to_size_slice
        from scipy.interpolate import UnivariateSpline
        x,y = self.plottable_segment(size.unit)
        dx = x[1] - x[0]
        slice_length = int((size / dx).value)
        slc = trimmed_to_size_slice(y,slice_length)
        # center = np.argmax(y)
        # print("Center at " + str(center))
        # print("Slice length of " + str(slice_length))
        # max_found = -1.0
        # index = center - slice_length
        # for i in range(max(index,0),center):
        #     tmp = y[i:min(i+slice_length,len(y))].sum()
        #     if tmp > max_found:
        #         index = i
        #         max_found = tmp
        # print("From " + str(index) + " to " + str(index+slice_length))
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
        for i in table:
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
            # plt.figure()
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



