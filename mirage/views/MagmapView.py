from matplotlib.lines import Line2D
from matplotlib import pyplot as plt
import matplotlib
import numpy as np

from mirage.util import Vec2D
from mirage.lens_analysis.MagnificationMap import MagnificationMap

from . import ImageCurveView

class MagnificationMapView(ImageCurveView):
    def __init__(self,name=None):
        ImageCurveView.__init__(self)
        self.figure, self.axes, self.lc_view = ImageCurveView.get_view(True,name)
        self.connect()
        self.press = None
        self.line = Line2D([0,0],[0,0],color='r',antialiased=True)
        self.axes.add_line(self.line)
        self._current_curve = None
        self._with_colorbar = True

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
            curve = 2.5*np.log10(self._magmap.slice_line(sv,ev))
            dist = (ev-sv).magnitude.value
            x_ax = np.linspace(0,dist,len(curve))
            self.plot(curve,x_ax=x_ax)
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

    def save_image(self,filename,dpi=300):
        extent = self.axes.get_window_extent().transformed(self.figure.dpi_scale_trans.inverted())
        self.figure.savefig(filename, bbox_inches=extent.expanded(1.5,1.0),dpi=dpi)

    def save(self,filename,dpi=300):
        self.figure.savefig(filename,dpi=dpi)


    def disconnect(self):
        'disconnect all the stored connection ids'
        self.figure.canvas.mpl_disconnect(self.cidpress)
        self.figure.canvas.mpl_disconnect(self.cidrelease)
        self.figure.canvas.mpl_disconnect(self.cidmotion)


    @property
    def magmap(self):
        return self._magmap

    @property
    def map_unit(self):
        return self._unit

    def display(self,magmap:MagnificationMap=None):
        # if magmap is None:
        #     self.figure.show()
        # else:
        extent = magmap.region.dimensions/2
        x = extent.x.value
        y = extent.y.value
        img = self.axes.imshow(magmap.data.T,cmap=self._cmap,extent=[-x,x,-y,y])
        if self._with_colorbar:
            cb = self.figure.colorbar(img,ax=self.axes,pad=0.01,fraction=0.05)
            cb.set_label("Magnitudes")
        self._magmap = magmap
        self._unit = magmap.region.dimensions.unit
            # self.figure.show()

    def show(self,*args,**kwargs):
        return self.display(*args,**kwargs)

    def show_curve(self,curve):
        x,y = curve.plottable(self.map_unit)
        # print(x.shape)
        # print(y.shape)
        start,end = curve.ends
        start = start.to(self.map_unit)
        end = end.to(self.map_unit)
        self.line.set_xdata([start[0].value,end[0].value])
        self.line.set_ydata([start[1].value,end[1].value]) #NOTE: I need to transpose to be consistent with theview
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
            s = start.quantity
            e = end.quantity
            return LightCurve(curve,s,e)

