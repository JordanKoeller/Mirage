import numpy as np
from matplotlib import pyplot as plt
from matplotlib.pyplot import figure, show
from matplotlib.lines import Line2D

from mirage.util import Vec2D
from mirage.parameters import Simulation
from mirage.lens_analysis.MagnificationMap import MagnificationMap

class MagnificationMapView:
    def __init__(self,name=None):
        # self.rect = rect
        self.figure, self.axes, self.lc_view = MagnificationMapView.get_view(True,name)
        self.connect()
        self._cmap = plt.get_cmap('RdBu_r')
        # self.figure = fig
        # self.axes= ax
        self.press = None
        self.line = Line2D([0,0],[0,0],color='r',antialiased=True)
        self.axes.add_line(self.line)
        self._current_curve = None

    def connect(self):
        'connect to all the events we need'
        self.cidpress = self.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self, event):
        'on button press we will see if the mouse is over us and store some data'
        if event.inaxes != self.axes or event.button != 3: return

        canvas = self.figure.canvas
        self.line.set_xdata([0,0])
        self.line.set_ydata([0,0])
        # self.line.set_animated(True)
        canvas.draw()
        self.background = canvas.copy_from_bbox(self.axes.bbox)
        self.press = event.xdata, event.ydata
        self.axes.draw_artist(self.line)
        canvas.blit(self.axes.bbox)

    def on_motion(self, event):
        'on motion we will move the rect if the mouse is over us'
        if self.press is None: return
        if event.inaxes != self.axes or event.button != 3: return
        xpress, ypress = self.press
        self.line.set_xdata([xpress,event.xdata])
        self.line.set_ydata([ypress,event.ydata])
        self.figure.canvas.restore_region(self.background)
        self.axes.draw_artist(self.line)
        self.figure.canvas.blit(self.axes.bbox)

    def on_release(self, event):
        'on release we reset the press data'
        if event.button != 3: return
        start = self.press
        end = event.xdata, event.ydata
        if not start or not end: return
        self.press = None
        sv = Vec2D(start[0],start[1],self.map_unit)
        ev = Vec2D(end[0],end[1],self.map_unit)
        if self._magmap:
            curve = self._magmap.slice_line(sv,ev)
            self.plot(curve)
            # self.lc_view.draw(self.figure.canvas.renderer)

    def plot(self,curve,x_ax=None,clear=True):
        if clear:
            self.lc_view.clear()
        if x_ax is not None:
            self.lc_view.plot(x_ax,curve)
        else:
            self.lc_view.plot(curve)
        self.figure.canvas.draw()
        self.axes.draw_artist(self.line)




    def disconnect(self):
        'disconnect all the stored connection ids'
        self.figure.canvas.mpl_disconnect(self.cidpress)
        self.figure.canvas.mpl_disconnect(self.cidrelease)
        self.figure.canvas.mpl_disconnect(self.cidmotion)

    @staticmethod
    def get_view(with_figure=False,name=None):
        fig, axes = plt.subplots(2,1,num=name,gridspec_kw = {'height_ratios':[1, 5]})
        curve_ax, img_ax = axes
        img_ax.set_axis_off()
        img_ax.set_frame_on(True)
        fig.subplots_adjust(top=0.988,bottom=0.006,left=0.039,right=0.983,hspace=0.075)
        if not with_figure:
            return img_ax,curve_ax
        else:
            return fig, img_ax,curve_ax

    @property
    def magmap(self):
        return self._magmap

    @property
    def map_unit(self):
        return self.magmap.region.dimensions.unit

    def display(self,magmap:MagnificationMap):
        extent = magmap.region.dimensions/2
        x = extent.x.value
        y = extent.y.value
        self.axes.imshow(magmap.data.T,cmap=self._cmap,extent=[-x,x,-y,y])
        self._magmap = magmap
        self.figure.show()

    def show(self,*args,**kwargs):
        return self.display(*args,**kwargs)

    def show_curve(self,curve):
        x,y = curve.plottable('uas')
        # print(x.shape)
        # print(y.shape)
        start,end = curve.ends
        start = start.to(self.map_unit)
        end = end.to(self.map_unit)
        self.line.set_ydata([start.x.value,end.x.value]) #NOTE: I need to transpose to be consistent with theview
        self.line.set_xdata([end.y.value,start.y.value])
        self.plot(y,x_ax=x.flatten())

    def get_curve(self):
        x,y = self.line.get_data()
        start = Vec2D(x[0],y[0],self.map_unit)
        end = Vec2D(x[1],y[1],self.map_unit)
        if start == end:
            return None
        if self.magmap:
            from mirage.lens_analysis import LightCurve
            curve = self._magmap.slice_line(start,end)
            qpts = [[x[0],y[0]],[x[1],y[1]]]
            return LightCurve(curve,qpts)

