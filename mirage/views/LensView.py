import time

from astropy import units as u
from matplotlib .animation import FuncAnimation
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap


from . import ImageCurveView
from . import get_renderer
from mirage import GlobalPreferences


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
        self._imgAx.add_artist(self._galPatch)
        self._imgAx.add_artist(self._quasarPatch)
        # self._dt = GlobalPreferences['dt']

    def _get_img_colormap(self):
        bg = GlobalPreferences['background_color']
        fg = GlobalPreferences['image_color']
        clist = [(0,bg),(1,fg)]
        return LinearSegmentedColormap.from_list("LensViewCMap",clist)
    

    def show(self):
        self._fig.show()

    def connect_runner(self,runner_controller:AnimationController):
        sim = runner_controller.simulation
        extent = sim.parameters.ray_region.dimensions/2
        x = extent.x.value
        y = extent.y.value
        renderer = get_renderer(runner_controller.simulation)
        cmap = self._get_img_colormap()
        self._frame_number = 0
        def run(*args):
            self._frame_number += 1
            q_center, pixels = runner_controller.get_at_frame(self._frame_number)
            frame = renderer.get_frame(pixels)
            self._quasarPatch.center = q_center.as_value_tuple()
            return [self._imgAx.imshow(frame,animated=True,extent=[-x,x,y,-y],cmap=cmap),self._galPatch, self._quasarPatch]
        self._runner = run

    def toggle(self):
        if not self._playing:
            self.play()
        else:
            self.pause()

    def play(self):
        self._playing = True
        self._animation = FuncAnimation(self._fig,self._runner,blit=True,interval=60)

    def pause(self):
        self._playing = False
        if self._animation:
            self._animation.event_source.stop()
            self._animation = None

    def reset(self):
        if self._playing:
            self.pause()
        self._frame_number = self._frame_number*0
            




        