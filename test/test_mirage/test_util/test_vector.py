from unittest import TestCase

from astropy import units as u
from astropy.units import Quantity
from astropy.coordinates import CartesianRepresentation

from mirage.util import Vec2D, PolarVec


class TestVec2D(TestCase):

    def testVect2DInit_floatArgs_success(self):
        v = Vec2D(2.5, 3.4, "m")

        self.assertEqual(v.x, 2.5 * u.m)
        self.assertEqual(v.y, 3.4 * u.m)
        self.assertEqual(v.unit, u.m)

    def testToCartesian_success(self):
        v = Vec2D(2.5, 3.4, "m")
        c = v.to_cartesian()
        self.assertEqual(c.x, v.x)
        self.assertEqual(c.y, v.y)
        self.assertEqual(c.z, 0 * v.unit)

    def testFromCartesian_success(self):
        expected = Vec2D(2.5, 3.4, "m")
        c = expected.to_cartesian()
        actual = Vec2D.from_cartesian(c)
        self.assertEqual(actual, expected)

    def testVect2DInit_quantityArgs_success(self):
        v = Vec2D(200 * u.m, 300 * u.m, "km")

        self.assertEqual(v.x, 0.2 * u.km)
        self.assertEqual(v.y, 0.3 * u.km)
        self.assertEqual(v.unit, u.km)

    def testVec2DInit_floatAndQuantity_throws(self):
        self.assertRaises(ValueError, lambda: Vec2D(200 * u.m, 300, u.m))

    def testVec2DInit_floatsWithNoUnits_throws(self):
        self.assertRaises(ValueError, lambda: Vec2D(200, 300))

    def testVec2DInit_nonConvertableUnits_throws(self):
        self.assertRaises(ValueError, lambda: Vec2D(3 * u.m, 4 * u.kg))

    def testVec2DInit_dimensionalQuantities_throws(self):
        self.assertRaises(ValueError, lambda: Vec2D(u.Quantity([3, 4], u.m), 5 * u.m))


class TestPolarVec(TestCase):

    def testInit_success(self):
        v = PolarVec(3 * u.m, 90 * u.deg)

    def testToCartesian_success(self):
        v = PolarVec(3 * u.m, 90 * u.deg)
        cart = v.to_cartesian()
        self.assertAlmostEqual(cart.x, 0 * u.m)
        self.assertAlmostEqual(cart.y, 3 * u.m)

    def testFromCartesian_success(self):
        cart = CartesianRepresentation(1 * u.m, 0 * u.m, 0 * u.m)

        v = PolarVec.from_cartesian(cart)

        self.assertAlmostEqual(v.r, 1 * u.m)
        self.assertAlmostEqual(v.theta, 0 * u.rad)

    def testInit_nonAngleQuantity_throws(self):
        self.assertRaises(ValueError, lambda: PolarVec(3 * u.m, 90 * u.m))

    def assertAlmostEqual(self, first, second):
        if isinstance(first, Quantity) and isinstance(second, Quantity):
            self.assertEqual(first.unit, second.unit)
            first = first.value
            second = second.value
        super().assertAlmostEqual(first, second)
