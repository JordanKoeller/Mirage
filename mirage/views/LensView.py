import time
from multiprocessing import Process, Queue, Pipe

from astropy import units as u
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from PyQt5.QtCore import QTimer
import numpy as np

from . import ImageCurveView
from . import get_renderer
from mirage import GlobalPreferences
from mirage.util import Vec2D


def _processThreadFunc(dt,sim,engine,queue,in_queue):
    time = dt*0
    flag = True
    renderer = get_renderer(engine.parameters)
    from mirage.parameters import Simulation
    while True:
        flag = False
        data = None
        data = in_queue.get(True)
        if isinstance(data,Vec2D):
            location = data
            time *= 0
            sim.update(start_position = location)
            pixels = engine.get_pixels(location,radius)
            frame = renderer.get_frame(pixels)
            queue.put([location,frame])
        elif isinstance(data,u.Quantity):
            time = data
            flag = True
        elif isinstance(data,Simulation):
            simulation = data
            engine.update_parameters(simulation.parameters)
            flag = True
        elif isinstance(data,str):
            time += dt
            location,radius = sim.query_info(time)
            pixels = engine.get_pixels(location,radius)
            frame = renderer.get_frame(pixels)
            queue.put([location,frame])

class AnimationController(object):

    buffer_sz = 10

    def __init__(self,simulation:'AnimationSimulation', engine:'AbstractEngine'):
        self._simulation = simulation
        self._engine = engine
        self._engine.update_parameters(simulation.parameters)
        self._dt = u.Quantity(0.1,'s')
        self._queue = Queue(maxsize=self.buffer_sz)
        self._sender = Queue(maxsize=10)
        # recv, self._sim_send = Pipe()
        self._process = Process(target=_processThreadFunc,args=(self._dt,self._simulation,self._engine,self._queue,self._sender),daemon=True)
        self._process.start()

    def close(self):
        self._process.close()

    def update_simulation(self,sim):
        self._simulation = sim
        self._sender.put(sim,True)

    @property
    def simulation(self):
        return self._simulation

    @property
    def engine(self):
        return self._engine

    @property
    def extent(self):
        extent = self.simulation.parameters.ray_region.dimensions.to(self.unit)/2
        x = extent.x.value
        y = extent.y.value
        return [-x,x,y,-y]

    @property
    def unit(self):
        if self.simulation.parameters.ray_region.dimensions.to(self.simulation.parameters.theta_E).magnitude.value > 1000:
            return u.arcsec
        else:
            return self.simulation.parameters.theta_E
    
    def query_location(self,loc,blocking=False):
        self.simulation.update(start_position=loc)
        self._sender.put(loc,blocking)

    def next_frame(self,block=False):
        if block:
            return self._queue.get(True)
        elif self._queue.empty():
            return None
        else:
            return self._queue.get(False)

    def request_next(self,force=False):
        if force or self._queue.empty():
            try:
                self._sender.put("Next",False)
            except:
                pass

class LensView(ImageCurveView):

    def __init__(self,name=None) -> None:
        self._fig, self._imgAx, self._lcAx, self._dynamic_canvas = self.get_view(True,name,True)
        # toolbar = self._window.toolbar
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
        self._cmap = self._get_img_colormap()

    def _get_img_colormap(self):
        bg = GlobalPreferences['background_color']
        fg = GlobalPreferences['image_color']
        clist = [(0,bg),(1,fg)]
        return LinearSegmentedColormap.from_list("LensViewCMap",clist)

    @property
    def cmap(self):
        return self._cmap

    @property
    def controller(self):
        return self._controller_ref

    def show(self):
        self._fig.show()

    @property
    def simulation(self):
        return self._controller_ref.simulation 

    def connect_runner(self,runner_controller:AnimationController):
        self._controller_ref = runner_controller
        if self._animation:
            self._animation._stop()
            del(self._animation)
            self._animation = None
        def run(*args,**kwargs):
            if self._playing:
                self.controller.request_next()
            ret = runner_controller.next_frame()
            if ret is not None:
                q_center, frame = ret
                self._set_frame(q_center,frame)
        self._runner = run
        self._playing = False
        self.controller.request_next()
        q_center, frame = runner_controller.next_frame(True)
        self._set_frame(q_center,frame,default_limits=True)
        self._animation = self._dynamic_canvas.new_timer(100/60,[(self._runner,(),{})])
        self._animation.start()

    def _set_frame(self, q_loc, frame,default_limits=False):
        if not default_limits:
            xlim = self._imgAx.get_xlim()
            ylim = self._imgAx.get_ylim()
        self._imgAx.clear()
        self._quasarPatch.center = q_loc.to(self.controller.unit).as_value_tuple()
        self._quasarPatch.set_radius(0.04)
        self._imgAx.imshow(frame,animated=True,extent=self.controller.extent,cmap=self.cmap)
        self._imgAx.add_artist(self._quasarPatch)
        if not default_limits:
            self._imgAx.set_xlim(xlim)
            self._imgAx.set_ylim(ylim)
        self._imgAx.figure.canvas.draw()

    def toggle(self):
        if not self._playing:
            self.play()
        else:
            self.pause()

    def play(self):
        self._playing = True
        # if self._animation:
        #     pass
        # else:

    def pause(self):
        self._playing = False
        # if self._animation:
        #     self._animation.stop()
        #     del(self._animation)
        #     self._animation = None
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
        if self._quasarPatch.contains(event):
            self._grabbed_quasar = True
        else:
            canvas = self._fig.canvas
            self.line.set_xdata([0,0])
            self.line.set_ydata([0,0])
            canvas.draw()
            self.background = canvas.copy_from_bbox(self._imgAx.bbox)
            self._imgAx.draw_artist(self.line)
            canvas.blit(self._imgAx.bbox)
        self.press = event.xdata, event.ydata

    def on_motion(self, event):
        'on motion we will move the rect if the mouse is over us'
        if self.press is None: return
        if event.inaxes != self._imgAx or event.button != 3: return
        xpress, ypress = event.xdata,event.ydata
        if self._grabbed_quasar:
            sim = self._controller_ref.simulation
            loc = Vec2D(xpress,ypress,self.controller.unit)
            self._controller_ref.query_location(loc)
        else:
            self.line.set_xdata([xpress,event.xdata])
            self.line.set_ydata([ypress,event.ydata])
            self._fig.canvas.restore_region(self.background)
            self._imgAx.draw_artist(self.line)
            self._fig.canvas.blit(self._imgAx.bbox)

    def on_release(self,event):
        if event.button != 3: return
        start = self.press
        if self._grabbed_quasar:
            xpress, ypress = event.xdata,event.ydata
            sim = self._controller_ref.simulation
            loc = Vec2D(xpress,ypress,self.controller.unit)
            self._controller_ref.query_location(loc,blocking=True)
            self._grabbed_quasar = False
        else:
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
