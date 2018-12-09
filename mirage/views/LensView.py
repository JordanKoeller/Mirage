import time

from astropy import units as u
from matplotlib .animation import FuncAnimation
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import numpy as np

from . import ImageCurveView
from . import get_renderer
from mirage import GlobalPreferences
from mirage.util import Vec2D


class AnimationController(object):

    def __init__(self,simulation:'AnimationSimulation', engine:'AbstractEngine'):
        self._simulation = simulation
        self._engine = engine
        self._dt = u.Quantity(0.1,'s')


    @property
    def simulation(self):
        return self._simulation
    @property
    def engine(self):
        return self._engine
    

    def get_at_frame(self,frame_number):
        time = frame_number*self._dt
        location, radius = self.simulation.query_info(time)
        pixels = self.engine.get_pixels(location,radius)
        return (location,pixels)


class LensView(ImageCurveView):

    def __init__(self,name=None) -> None:
        self._fig, self._imgAx, self._lcAx = self.get_view(True,name)
        self._playing = False
        self._frame_number = 0
        self._runner = None
        self._blank_frame = None
        self._animation = None
        self._galPatch = patches.Circle([0,0],0.1,color=GlobalPreferences['lens_color'])
        self._quasarPatch = patches.Circle([0,0],0.1,color=GlobalPreferences['quasar_color'])
        self.line = Line2D([0,0],[0,0],color='r',antialiased=True)
        self._imgAx.add_line(self.line)
        self.press = None
        self._curve_plot = np.zeros(100)
        self._curve_ax = np.arange(100)
        self._curve = self._lcAx.plot(self._curve_plot,animated=True)[0]
        self._curve_max = 1
        self._lcAx.set_ylim(0,self._curve_max)
        self.connect()

    def _get_img_colormap(self):
        bg = GlobalPreferences['background_color']
        fg = GlobalPreferences['image_color']
        clist = [(0,bg),(1,fg)]
        return LinearSegmentedColormap.from_list("LensViewCMap",clist)
    

    def show(self):
        self._fig.show()

    def connect_runner(self,runner_controller:AnimationController):
        self._controller_ref = runner_controller
        if self._animation:
            self._animation._stop()
            del(self._animation)
            self._animation = None
        sim = runner_controller.simulation
        extent = sim.parameters.ray_region.dimensions/2
        # minx,miny,maxx,maxy = sim.parameters.ray_region.to(sim.parameters.theta_E).extent
        x = extent.x.value
        y = extent.y.value
        self._galPatch.set_radius(extent.x.value/100)
        renderer = get_renderer(runner_controller.simulation)
        cmap = self._get_img_colormap()
        self._frame_number = 0
        def run(*args):
            if self._playing:
                self._imgAx.clear()
                self._frame_number += 1
                q_center, pixels = runner_controller.get_at_frame(self._frame_number)
                frame = renderer.get_frame(pixels)
                self._quasarPatch.center = q_center.as_value_tuple()
                self._quasarPatch.set_radius(min(sim.parameters.ray_region.dimensions.as_value_tuple())/200)
                if len(self._curve_plot) <= self._frame_number:
                    self._curve_plot = np.append(self._curve_plot,np.zeros(len(self._curve_plot)))
                    self._curve_ax = np.arange(len(self._curve_plot))
                    self._lcAx.set_xlim(0,len(self._curve_ax))
                self._curve_plot[self._frame_number] = len(pixels)
                if self._curve_plot[self._frame_number] > self._curve_max:
                    self._curve_max = self._curve_plot[self._frame_number]*2
                    self._lcAx.set_ylim(0,self._curve_max)
                self._curve.set_data(self._curve_ax,self._curve_plot)
                return [
                self._imgAx.imshow(frame,animated=True,extent=[-x,x,y,-y],cmap=cmap),
                self._curve,
                # self._imgAx.imshow(frame,animated=True,extent=[minx.value,maxx.value,maxy.value,miny.value],cmap=cmap),
                self._imgAx.add_artist(self._galPatch),
                self._imgAx.add_artist(self._quasarPatch),
                ]
            else:
                []
        self._runner = run
        self._playing = True
        self._runner()
        self._playing = False


    def toggle(self):
        if not self._playing:
            self.play()
        else:
            self.pause()

    def play(self):
        self._playing = True
        if self._animation:
            pass
        else:
            self._animation = FuncAnimation(self._fig,self._runner,blit=True,interval=200,save_count=0)

    def pause(self):
        self._playing = False
        if self._animation:
            self._animation._stop()
            del(self._animation)
            self._animation = None
        #     self._animation = None

    def reset(self):
        if self._playing:
            self.pause()
        self._frame_number = self._frame_number*0
        # self._curve_plot = np.zeros(100)
        # self._lcAx.plot(self._curve_plot)

    def connect(self):
        'connect to all the events we need'
        self.cidpress = self._fig.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self._fig.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self._fig.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def on_press(self,event):
        if event.inaxes != self._imgAx or event.button != 3 or self._playing: return
        canvas = self._fig.canvas
        self.line.set_xdata([0,0])
        self.line.set_ydata([0,0])
        # self.line.set_animated(True)
        canvas.draw()
        self.background = canvas.copy_from_bbox(self._imgAx.bbox)
        self.press = event.xdata, event.ydata
        self._imgAx.draw_artist(self.line)
        canvas.blit(self._imgAx.bbox)

    def on_motion(self, event):
        'on motion we will move the rect if the mouse is over us'
        if self.press is None: return
        if event.inaxes != self._imgAx or event.button != 3: return
        xpress, ypress = self.press
        self.line.set_xdata([xpress,event.xdata])
        self.line.set_ydata([ypress,event.ydata])
        self._fig.canvas.restore_region(self.background)
        self._imgAx.draw_artist(self.line)
        self._fig.canvas.blit(self._imgAx.bbox)

    def on_release(self,event):
        if event.button != 3: return
        start = self.press
        end = event.xdata, event.ydata
        if not start or not end: return
        self.press = None
        sim = self._controller_ref.simulation
        pos_unit = sim.start_position.unit
        vel_unit = sim.velocity.unit 
        self.line.set_xdata([0,0])
        self.line.set_ydata([0,0])
        sv = Vec2D(start[0],start[1],pos_unit)
        vel = Vec2D(end[0] - start[0],end[1] - start[1],vel_unit)
        sim.update(start_position=sv,velocity=vel/20)
