
class ParametersError(Exception):
    def __init__(self,value):
        self.value = value

    def __repr__(self):
        return repr(self.value)

from .Cosmic import Cosmic
from .CalculationDependency import CalculationDependency
from .Quasar import Quasar
from .MassModel import Lens
from .Parameters import Parameters, MicrolensingParameters
from .ResultParameters import ResultParameters, MagnificationMapParameters, \
    LightCurvesParameters, MomentMapParameters
from .Simulation import Simulation, AnimationSimulation


def QSO2237():
    from astropy import units as u
    from mirage.util import Vec2D, PolarVec, PixelRegion,Region
    q = Quasar(1.69,0.1*u.arcsec,1000000000*u.solMass)
    shear = PolarVec(0.0001,0.0)
    ellip = PolarVec(1,0.0)
    rays = PixelRegion(Vec2D(0.0,0.0,'arcsec'),Vec2D(40.0,40.0,'arcsec'),Vec2D(2000,2000))
    lens = Lens(0.04,177.95*u.km/u.s,shear,ellip)
    params = Parameters(q,lens,rays)
    return params

def QSO2237_ImageC(root_rays,percent_stars):
    from mirage.util import Vec2D, Region, zero_vector
    qso = QSO2237()
    src_plane = Vec2D(40,40,qso.theta_E)
    qso.quasar.update(radius=80*qso.quasar.r_g)
    center = zero_vector('rad')
    src_plane = Region(center,src_plane)
    img_center = Vec2D(1.4,1.4,'arcsec')
    ray_count = Vec2D(int(root_rays),int(root_rays))
    return MicrolensingParameters(qso.quasar,qso.lens,percent_stars,img_center,ray_count,src_plane)

