from math import pi, sqrt, sin, cos, atan, atan2

from astropy import units as u
from astropy import constants as const

from mirage.util import Jsonable, Vec2D, PixelRegion, Region, zero_vector, CircularRegion
from mirage.calculator import StationaryMassFunction, getMassFunction, MassFunction

from .Cosmic import Cosmic
from .CalculationDependency import CalculationDependency
from .Quasar import Quasar
from .MassModel import Lens
from . import ParametersError
from mirage import GlobalPreferences


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
        return Parameters.static_einstein_radius(self.lens.velocity_dispersion,self.quasar.redshift,self.lens.redshift)


    @property
    def einstein_radius_unit(self):
        return u.def_unit('einstein_rad', self.einstein_radius.value*u.rad)

    @property
    def theta_E(self):
        return Parameters.static_theta_E(self.quasar.redshift,self.lens.redshift)

    @property
    def raw_brightness(self) -> float:
        return 1

    def magnification(self,loc:Vec2D) -> float:
        kap = self.convergence(loc)
        gam = self.shear(loc)
        mag = 1/((1-kap)**2 - gam**2)
        return abs(mag)


    def convergence(self,loc:Vec2D) -> float:
        # print("NOTE: Have not implimented convergence yet!")
        #Assumes SIE mass model with external shear.
        #STILL NOT GOOD _ NOT ACCOUNTING FOR EXTERNAL SHEAR
        b = self.einstein_radius.to('rad').value
        x = loc.x.to('rad').value
        y = loc.y.to('rad').value
        E = self.lens.ellipticity.direction.to('rad').value
        t1 = x*sin(E) + y*cos(E)
        t2 = y*sin(E) - x*cos(E)
        p = self.lens.shear.direction.to('rad').value
        g = self.lens.shear.magnitude.value
        q = 1 - self.lens.ellipticity.magnitude.value
        ret_val = b/(2*sqrt(q**2*t1**2 + t2**2)) + 3*g*cos(E - p + atan(t2/t1))/4
        return 0.7
        return ret_val

    def shear(self,loc:Vec2D) -> float:
        # print("NOTE: Have not implimented Shear yet!")
        #Expressions calculated using Sympy, from \Psi = \theta \dot \alpha
        #STILL NOT GOOD _ NOT ACCOUNTING FOR EXTERNAL SHEAR
        b = self.einstein_radius.to('rad').value
        x = loc.x.to('rad').value
        y = loc.y.to('rad').value
        E = self.lens.ellipticity.direction.to('rad').value
        t1 = x*sin(E) + y*cos(E)
        t2 = y*sin(E) - x*cos(E)
        p = self.lens.shear.direction.to('rad').value
        g = self.lens.shear.magnitude.value
        q = 1 - self.lens.ellipticity.magnitude.value
        ret_val = sqrt(t1**2*(2*b*t2*(t1**2 + t2**2)*sqrt(q**2*t1**2 + t2**2) + g*sqrt((t1**2 + t2**2)/t1**2)*(t1**2*(q**2*t1**3*sin(E - p) - q**2*t2**3*cos(E - p) + t1*t2**2*sin(E - p)) - t2**5*cos(E - p)))**2/(4*(t1**2 + t2**2)**2*(q**2*t1**4 + q**2*t1**2*t2**2 + t1**2*t2**2 + t2**4)**2) + (-b*t1**2*sqrt(q**2*t1**2 + t2**2)/2 + b*t2**2*sqrt(q**2*t1**2 + t2**2)/2 + g*q**2*t1**4*cos(E - p + atan(t2/t1))/4 + g*q**2*t1**3*t2*sin(E - p + atan(t2/t1)) - g*q**2*t1**2*t2**2*cos(E - p + atan(t2/t1))/4 + g*t1**2*t2**2*cos(E - p + atan(t2/t1))/4 + g*t1*t2**3*sin(E - p + atan(t2/t1)) - g*t2**4*cos(E - p + atan(t2/t1))/4)**2/(q**2*t1**4 + q**2*t1**2*t2**2 + t1**2*t2**2 + t2**4)**2)
        return 0.7
        return ret_val

    @property
    def json(self):
        ret = {}
        ret['lens'] = self.lens.json
        ret['source'] = self.quasar.json
        ret['ray_region'] = self.ray_region.to(self.theta_E).json
        return ret

    @classmethod
    def from_json(cls,js:'Dict') -> 'Parameters':
        z_s = js['source']['redshift']
        z_l = js['lens']['redshift']
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


    @staticmethod
    def special_units(z_s,z_l,quasar_mass):
        r_g = Quasar.static_r_g(quasar_mass,z_s)
        theta_E = Parameters.static_theta_E(z_s,z_l)
        xi = u.def_unit('xi',(1*theta_E).to('rad'))
        return [r_g, theta_E, xi]

    @staticmethod
    def static_einstein_radius(vDispersion, z_s, z_l):
        dLS = Cosmic.cosmology.angular_diameter_distance_z1z2(z_l,z_s)
        dS = Cosmic.cosmology.angular_diameter_distance(z_s)
        ret = (4 * pi * vDispersion.to('m/s')**2*dLS)/(dS*const.c**2)
        ret = ret.to('')
        return u.Quantity(ret.value,'rad')

    def to_microlensing_parameters(self, pcnt_stars:float,
        image_center:Vec2D,
        minor_axis:u.Quantity,
        star_generator:MassFunction) -> 'MicrolensingParameters':
        bounding_box = Region(zero_vector('uas'),Vec2D(minor_axis.value,minor_axis.value,minor_axis.unit))
        return MicrolensingParameters(self.quasar, self.lens,
            pcnt_stars,
            image_center,
            self.ray_region.resolution,
            bounding_box,
            star_generator)

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
            # eprint("NOTE: Need to specify the factor for going from source plane to ray plane.")
            factor = GlobalPreferences['microlensing_window_buffer']
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
    def get_macro_parameters(self):
        print("Temporary implimentation for macro_parameters")
        ray_region = self.ray_region
        return Parameters(self.quasar,self.lens,ray_region)

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
    def ray_region(self):
        return self._ray_region.to(self.theta_E)

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
    def raw_brightness(self) -> float:
        disk_area = self.quasar.radius**2*pi
        dtheta = self.ray_region.dTheta
        pix_sz = dtheta.x*dtheta.y
        ratio = (disk_area/pix_sz).to('').value
        return ratio * self.magnification(self.image_center)

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
        try:
            ret = {}
            ret['lens'] = self.lens.json
            ret['source'] = self.quasar.json
            ret['star_generator'] = self.star_generator.json
            ret['percent_stars'] = self.percent_stars*100
            ret['source_plane'] = self.source_plane.to(self.theta_E).json
            ret['image_center'] = self.ray_region.center.json
            ret['ray_count'] = self.ray_region.resolution.json
            return ret
        except KeyError as e:
            ret = Parameters.json.fget(self)
            # print("Sloppy implementation here. Need to redo it with better json of micromagmap")
            # del(ret['ray_region'])
            ret['star_generator'] = self.star_generator.json
            ret['percent_stars'] = self.percent_stars*100
            ret['source_plane'] = self.source_plane.to(self.theta_E).json
            return ret


    @classmethod
    def from_json(cls,js):
        try:
            z_s = js['source']['redshift']
            z_l = js['lens']['redshift']
            mass = Jsonable.decode_quantity(js['source']['mass'])
            special_units = Parameters.special_units(z_s,z_l,mass)
            with u.add_enabled_units(special_units):
                gal = Lens.from_json(js['lens'])
                src = Quasar.from_json(js['source'])
                rays = Vec2D.from_json(js['ray_count'])
                sg = MassFunction.from_json(js['star_generator'])
                pcnts = js['percent_stars']
                spln = Region.from_json(js['source_plane'])
                center = Vec2D.from_json(js['image_center'])
                return cls(src,gal,pcnts,center,rays,spln,sg)
        except KeyError as e:
            print(e)
            params = Parameters.from_json(js)
            with u.add_enabled_units([params.quasar.r_g, params.theta_E]):
                sg = MassFunction.from_json(js['star_generator'])
                pcnts = js['percent_stars']
                spln = Region.from_json(js['source_plane'])
                rays = params.ray_region.resolution
                center = params.ray_region.center
                return cls(params.quasar,params.lens,pcnts,center,rays,spln,sg)

    def is_similar(self,other:'Parameters'):
        myJS = self.json
        oJS = other.json
        return myJS['lens'] == oJS['lens'] and \
        myJS['source']['redshift'] == oJS['source']['redshift'] and \
        myJS['star_generator'] == oJS['star_generator'] and \
        myJS['percent_stars'] == oJS['percent_stars'] and \
        myJS['source_plane'] == oJS['source_plane'] and \
        myJS['image_center'] == oJS['image_center'] and \
        myJS['ray_count'] == oJS['ray_count']