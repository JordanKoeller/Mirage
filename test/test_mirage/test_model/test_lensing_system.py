from unittest import TestCase
from ruamel.yaml import YAML
import json

from astropy import units as u
from astropy.cosmology import WMAP9

from mirage.model import Quasar, LensingSystem
from mirage.model.impl import SingularIsothermalSphereLens
from mirage.util import PolarVec, Dictify


class TestLensingSystem(TestCase):

  def testToDict_canDictify(self):
    sis = SingularIsothermalSphereLens(
        quasar=Quasar(0.7, mass=u.Quantity(1e9, "solMass")),
        redshift=1.2,
        velocity_dispersion=u.Quantity(300, "km/s"),
        star_fraction=0.8,
        shear=PolarVec(u.Quantity(0.1, "rad"), u.Quantity(0.2, "rad")),
        ellipticity=PolarVec(u.Quantity(0.1, "rad"), u.Quantity(0.3, "rad")),
        cosmology=WMAP9,
    )

    expected = {
        "Quasar": {"Redshift": 0.7, "Mass": "1000000000 solMass"},
        "Redshift": 1.2,
        "VelocityDispersion": "300 km / s",
        "StarFraction": 0.8,
        "Shear": {"R": "0.1 rad", "Theta": "0.2 rad"},
        "Ellipticity": {"R": "0.1 rad", "Theta": "0.3 rad"},
        "Cosmology": "WMAP9",
    }

    dict_sis = Dictify.to_dict(sis)

    self.assertDictEqual(dict_sis, expected)

  def testFromDict_canParseLens(self):
    sis_dict = {
        "Quasar": {"Redshift": 0.7, "Mass": [1e9, "solMass"]},
        "Redshift": 1.2,
        "VelocityDispersion": [300, "km / s"],
        "StarFraction": 0.8,
        "Shear": {"R": [0.1, "rad"], "Theta": [0.2, "rad"]},
        "Ellipticity": {"R": [0.1, "rad"], "Theta": [0.3, "rad"]},
        "Cosmology": "WMAP9",
    }

    actual_sis = Dictify.from_dict(SingularIsothermalSphereLens, sis_dict)
    expected_sis = SingularIsothermalSphereLens(
        quasar=Quasar(0.7, mass=u.Quantity(1e9, "solMass")),
        redshift=1.2,
        velocity_dispersion=u.Quantity(300, "km/s"),
        star_fraction=0.8,
        shear=PolarVec(u.Quantity(0.1, "rad"), u.Quantity(0.2, "rad")),
        ellipticity=PolarVec(u.Quantity(0.1, "rad"), u.Quantity(0.3, "rad")),
        cosmology=WMAP9,
    )

    self.assertEqual(actual_sis, expected_sis)
