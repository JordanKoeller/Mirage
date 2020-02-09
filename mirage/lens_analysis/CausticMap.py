from mirage.util import PixelRegion, Vec2D, zero_vector

from . import MagnificationMap


class CausticMap(MagnificationMap):

  def __init__(self, simulation, data):
    sp = simulation.parameters.source_plane
    theta_E = simulation.parameters.theta_E
    r = simulation['causticmap'].resolution
    self._source_plane = PixelRegion(zero_vector(theta_E), sp.dimensions.to(theta_E), r)
    self._data = data

  @property
  def data(self):
    return self._data

  def is_caustic(self, point: Vec2D) -> bool:
    pix = self.region.loc_to_pixel(point)
    return self.data[pix.x, pix.y] == 1

  def caustics_along(self, curve):
    qpts = curve.query_points
    ret = []
    for r in range(len(curve)):
      if self.is_caustic(Vec2D(qpts[r, 0], qpts[r, 1], qpts.unit)):
        ret.append(r)
    return np.array(ret)
