# import matplotlib.style as mplstyle
# mplstyle.use(['dark_background','fast'])
from abc import ABC, abstractmethod

from .MagmapView import MagnificationMapView


class ImageCurveView:
    def __init__(self):
        self._cmap = plt.get_cmap('RdBu_r')

    @staticmethod
    def get_view(with_figure=False,name=None):
        from matplotlib import pyplot as plt
        fig = plt.figure(-1)
        axes = fig.subplots(2,1,gridspec_kw={'height_ratios':[1,5]})
        fig.show()
        # fig, axes = plt.subplots(2,1,num=name,gridspec_kw = {'height_ratios':[1, 5]})
        curve_ax, img_ax = axes
        img_ax.set_axis_off()
        img_ax.set_frame_on(True)
        fig.subplots_adjust(top=0.988,bottom=0.006,left=0.039,right=0.983,hspace=0.075)
        if not with_figure:
            return img_ax,curve_ax
        else:
            return fig, img_ax, curve_ax


def run_example_rect():
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    class DraggableRectangle:
        def __init__(self,fig,ax):
            # self.rect = rect
            self.figure = fig
            self.axes= ax
            self.press = None
            self.line = Line2D([0,0],[0,0],color='k',antialiased=True)#,animated=True)
            self.axes.add_line(self.line)

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
            if event.inaxes != self.axes: return

            canvas = self.figure.canvas
            self.line.set_xdata([0,0])
            self.line.set_ydata([0,0])
            self.line.set_animated(True)
            canvas.draw()
            self.background = canvas.copy_from_bbox(self.axes.bbox)
            self.press = event.xdata, event.ydata
            self.axes.draw_artist(self.line)
            canvas.blit(self.axes.bbox)

        def on_motion(self, event):
            'on motion we will move the rect if the mouse is over us'
            if self.press is None: return
            if event.inaxes != self.axes: return
            xpress, ypress = self.press
            dx = event.xdata - xpress
            dy = event.ydata - ypress
            self.line.set_xdata([xpress,event.xdata])
            self.line.set_ydata([ypress,event.ydata])
            self.figure.canvas.restore_region(self.background)
            self.axes.draw_artist(self.line)
            self.figure.canvas.blit(self.axes.bbox)

        def on_release(self, event):
            'on release we reset the press data'
            self.press = None
            self.figure.canvas.draw()

        def disconnect(self):
            'disconnect all the stored connection ids'
            self.figure.canvas.mpl_disconnect(self.cidpress)
            self.figure.canvas.mpl_disconnect(self.cidrelease)
            self.figure.canvas.mpl_disconnect(self.cidmotion)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    dr = DraggableRectangle(fig,ax)
    dr.connect()
    plt.show()
    return dr
