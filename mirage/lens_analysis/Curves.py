#
#
# class LightCurve(object):
#
#     def __init__(self,data,start_pt,end_pt):
#         self._data = np.array(data)
#         self._start = start_pt
#         self._end = end_pt
#
#     def __len__(self):
#         return len(self._data)
#
#     @@property
#     def ends(self):
#         return self._start,self._end
#
#     @property
#     def magnitude_curve(self):
#         return -2.5*np.log10(self._data+0.0001)
#
#     @property
#     def magnification_curve(self):
#         return self._data
#
#     @property
#     def query_points(self):
#         x = np.linspace(self._start.x.value,self._end.x.value,len(self))
#         y = np.linspace(self._start.y.value,self._end.y.value,len(self))
#         ret = np.ndarray((len(x),2))
#         ret[:,0] = x
#         ret[:,1] = y
#         return u.Quantity(ret,self._start.unit)
#
#     @property
#     def distance_axis(self):
#         qpts = self.query_points
#         x = qpts[:,0]
#         y = qpts[:,1]
#         x = x - x[0]
#         y = y - y[0]
#         return (x**2 + y**2)**(0.5)
#
#     def plottable(self,unit='uas'):
#         x = self.distance_axis.to(unit)
#         y = self.curve
#         return x,y
#
#
#     def smooth_with_window(self,window:int):
#         data = self._data.copy()
#         data = wiener(data,window)
#         return LightCurve(data,self.query_points)
#


