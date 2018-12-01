

def get_renderer(sim):
    from .Renderer import LensRenderer
    return LensRenderer(sim)
    

try:
    from .View import ImageCurveView
    from .MagmapView import MagnificationMapView
    from .LensView import LensView
except ImportError as e:
    print("Warning: Matplotlib not detected. Everything inside the View package is disabled.")


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


