from math import pi, sqrt

from astropy import units as u
from astropy import constants as const

from mirage.util import Jsonable, Vec2D, PixelRegion, Region, zero_vector, CircularRegion
from mirage.calculator import StationaryMassFunction, getMassFunction, MassFunction

from .Cosmic import Cosmic
from .CalculationDependency import CalculationDependency
from .Quasar import Quasar
from .MassModel import Lens
from . import ParametersError


class Parameters(Jsonable, CalculationDependency):

    def __init__(self, quasar:Quasar, lens:Lens, ray_region:PixelRegion=None) -> None:
        try:
            assert isinstance(quasar,Quasar)
            assert isinstance(lens,Lens)
        # assert isinstance(ray_region,PixelRegion)
        except AssertionError:
            from mirage.parameters import ParametersError
            raise ParametersError("Supplied arguments to Parameters were invalid")
        self._quasar = quasar
        self._lens = lens
        self._ray_region = ray_region

    @staticmethod
    def static_theta_E(z_s,z_l):
        dS = Cosmic.cosmology.angular_diameter_distance(z_s)
        dL = Cosmic.cosmology.angular_diameter_distance(z_l)
        dLS = Cosmic.cosmology.angular_diameter_distance_z1z2(z_l,z_s)
        Msun = 1*u.solMass
        tmp = (4*const.G*Msun/const.c/const.c)*(dL*dLS/dS)
        ret = (tmp**0.5/dL).to('').value
        return u.def_unit('theta_E',ret*u.rad)

    @property
    def quasar(self):
        return self._quasar

    @property
    def lens(self):
        return self._lens

    @property
    def ray_region(self):
        return self._ray_region

    @property
    def dLS(self):
        return Cosmic.cosmology.angular_diameter_distance_z1z2(self.lens.redshift,self.quasar.redshift)

    @property
    def dL(self):
        return self.lens.ang_diam_dist

    @property
    def dS(self):
        return self.quasar.ang_diam_dist

    @property
    def critical_density(self):
        tmp = const.c*const.c*self.dS/4/pi/const.G/self.dL/self.dLS
        distanced = tmp.to('solMass/m2')
        per_rad = (distanced*self.dL*self.dL).to('solMass').value
        ret = u.Quantity(per_rad,'solMass/rad2').to('solMass/uas2')
        # print("Critical Density of %.3f solMass/uas2" % (ret.value))
        return ret

    @property
    def einstein_radius(self):
        ret = 4 * pi * self.lens.velocity_dispersion**2*self.dLS/self.dL/const.c**2
        ret = ret.to('')
        return u.Quantity(ret.value,'rad')

    @property
    def einstein_radius_unit(self):
        return u.def_unit('einstein_rad', self.einstein_radius.value*u.rad)

    @property
    def theta_E(self):
        return Parameters.static_theta_E(self.quasar.redshift,self.lens.redshift)

    @property
    def raw_brightness(self) -> float:
        from mirage.engine import raw_brightness
        return float(raw_brightness(self))

    def convergence(self,loc:Vec2D) -> float:
        print("NOTE: Have not implimented convergence yet!")
        #Assumes SIE mass model with external shear.
        #STILL NOT GOOD _ NOT ACCOUNTING FOR EXTERNAL SHEAR
        try:
            loc = loc.to(self.xi_0)
            t1 = loc.x.value
            t2 = loc.y.value
            b = self.einstein_radius
            q = self.lens.ellipticity
            om = sqrt(q*q*t1*t1+t2*t2)
            conv = b/(2*om)
            print("Calculating conv of %f" % conv)
        except:
            pass
        return 0.7

    def shear(self,loc:Vec2D) -> float:
        print("NOTE: Have not implimented Shear yet!")
        #Expressions calculated using Sympy, from \Psi = \theta \dot \alpha
        #STILL NOT GOOD _ NOT ACCOUNTING FOR EXTERNAL SHEAR
        try:
            loc = loc.to(self.xi_0)
            b = self.einstein_radius
            t1 = loc.x.value
            t2 = loc.y.value
            q = self.lens.ellipticity
            psi_11 = b*q*t2**2/((t1**2 + t2**2)*sqrt(q**2*t1**2 + t2**2))
            psi_22 = b*q*t1**2/((t1**2 + t2**2)*sqrt(q**2*t1**2 + t2**2))
            psi_12 = -b*q*t1*t2/((t1**2 + t2**2)*sqrt(q**2*t1**2 + t2**2))
            shear = (1/2*(psi_11 - psi_22))**2 + psi_12**2
            print("Calculating shear of %f" % shear)
        except:
            pass
        return 0.7

    @property
    def json(self):
        ret = {}
        ret['lens'] = self.lens.json
        ret['source'] = self.quasar.json
        ret['ray_region'] = self.ray_region.json
        return ret

    @classmethod
    def from_json(cls,js:'Dict') -> 'Parameters':
        z_s = js['source']['redshift']
        z_l = js['source']['redshift']
        mass = Jsonable.decode_quantity(js['source']['mass'])
        te = Parameters.static_theta_E(z_s,z_l)
        rg = Quasar.static_r_g(mass,z_s)
        with u.add_enabled_units([te,rg]):
            gal = Lens.from_json(js['lens'])
            src = Quasar.from_json(js['source'])
            rays = PixelRegion.from_json(js['ray_region'])
            return cls(src,gal,rays)

    def is_similar(self,other:'Parameters'):
        myJS = self.json
        thatJS = other.json
        return myJS['lens'] == thatJS['lens'] and myJS['ray_region'] == thatJS['ray_region'] and myJS['source']['redshift'] == thatJS['source']['redshift']


class MicrolensingParameters(Parameters):

    def __init__(self,
                 quasar:Quasar,
                 lens:Lens,
                 percent_stars:float,
                 image_center:Vec2D,
                 ray_count:Vec2D,
                 quasar_position_bounding_box:Region,
                 star_generator:MassFunction = getMassFunction()):
        try:
            print("NOTE: Need to specify the factor for going from source plane to ray plane.")
            factor = 1.3
            tmp_p = Parameters(quasar,lens)
            conv = tmp_p.convergence(image_center)
            shear = tmp_p.shear(image_center)
            ax_ratio = (abs(1 - shear - conv)/abs(1 + shear - conv))
            ray_dims = Vec2D(quasar_position_bounding_box.dimensions.x.value/ax_ratio,
                             quasar_position_bounding_box.dimensions.y.value,
                             str(quasar_position_bounding_box.dimensions.unit))
            ray_region = PixelRegion(image_center,ray_dims*factor,ray_count)
            Parameters.__init__(self,quasar,lens,ray_region)
            self._star_generator = star_generator
            self._source_plane = quasar_position_bounding_box
            self._percent_stars = percent_stars/100
        except:
            raise ParametersError("Could not construct MicrolensingParameters from the supplied arguments.")

    @property
    def starry_region(self):
        radius = self.ray_region.dimensions.x*0.6
        center = zero_vector("rad")
        area = CircularRegion(center,radius)
        return area

    @property
    def percent_stars(self):
        return self._percent_stars

    @property
    def image_center(self):
        return self.ray_region.center

    @property
    def star_generator(self):
        return self._star_generator

    @property
    def source_plane(self):
        return self._source_plane

    @property
    def xi_0(self):
        tmp = (1*self.theta_E).to('rad').value
        return u.def_unit('xi',tmp*u.rad)

    @property
    def eta_0(self):
        tmp = (1*self.theta_E).to('rad').value
        return u.def_unit('eta',tmp*u.rad)

    @property
    def mass_descriptors(self):
        convergence = self.convergence(self.image_center)
        shear = self.shear(self.image_center)
        smooth = convergence*(1 - self.percent_stars)
        starry = convergence*self.percent_stars
        return smooth,starry,shear


    @property
    def stars(self):
        region = self.starry_region.to(self.xi_0)
        mass_density = self.convergence(self.image_center) * self.critical_density
        return self.star_generator.generate_stars(region,mass_density*self.percent_stars)

    @property
    def json(self):
        ret = Parameters.json.fget(self)
        print("Sloppy implementation here. Need to redo it with better json of micromagmap")
        # del(ret['ray_region'])
        ret['star_generator'] = self.star_generator.json
        ret['percent_stars'] = self.percent_stars*100
        ret['source_plane'] = self.source_plane.json
        return ret

    @classmethod
    def from_json(cls,js):
        params = Parameters.from_json(js)
        with u.add_enabled_units([params.quasar.r_g, params.theta_E]):
            sg = StationaryMassFunction.from_json(js['star_generator'])
            pcnts = js['percent_stars']
            spln = Region.from_json(js['source_plane'])
            rays = params.ray_region.resolution
            center = params.ray_region.center
            return cls(params.quasar,params.lens,pcnts,center,rays,spln,sg)

def is_similar(self,other:'Parameters'):
    myJS = self.json
    oJS = other.json
    return Parameters.is_similar(self,other) and myJS['star_generator'] == oJS['star_generator'] and myJS['percent_stars'] == oJS['percent_stars']
