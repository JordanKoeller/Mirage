from unittest import TestCase

from mirage.util import PixelRegion, Vec2D, zero_vector

class TestPixelRegion(TestCase):

    def testSubdivideGivesExpectedEvenTilesOnEvenInput(self):
        pr = PixelRegion(zero_vector("uas"), Vec2D(10.0, 10.0, 'uas'), Vec2D(10, 10))
        subdivides = [tile for tile in pr.subdivide(2)]
        self.assertEqual(len(subdivides), 25)
        self.assertPixelsEqual(subdivides, pr)

    def testSubdivideGivesExpectedEvenTilesOnUnevenInput(self):
        pr = PixelRegion(zero_vector("uas"), Vec2D(10.0, 10.0, 'uas'), Vec2D(13, 13))
        subdivides = [tile for tile in pr.subdivide(5)]
        self.assertEqual(len(subdivides), 9)
        self.assertPixelsEqual(subdivides, pr)

    def assertPixelsEqual(self, tiles: PixelRegion, total: PixelRegion):
        expectedPts = []
        foundPts = []
        expectedPixels = total.pixels
        i, j, _ = expectedPixels.shape
        for ii in range(i):
            for jj in range(j):
                expectedPts.append((expectedPixels[ii,jj,0].value, expectedPixels[ii,jj,1].value))
        for tile in tiles:
            tilePixels = tile.pixels
            i, j, _ = tilePixels.shape
            for ii in range(i):
                for jj in range(j):
                    foundPts.append((tilePixels[ii,jj,0].value, tilePixels[ii,jj,1].value))
        self.assertEqual(len(foundPts), len(expectedPts), "Pixel arrays of unequal length")
        for foundPt in foundPts:
            found = False
            for expectedPt in expectedPts:
                if self.approxEq(foundPt[0], expectedPt[0]) and self.approxEq(foundPt[1], expectedPt[1]):
                    found = True
            if not found:
                print(f"Found no match between \n{expectedPts[:3]}... and \n{foundPts[:3]}...")
            self.assertTrue(found)

    def approxEq(self, a, b, tol=1e-8):
        return abs(a - b) < tol

