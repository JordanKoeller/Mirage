
class MomentMap(MagnificationMap):

  def __init__(self, simulation, data):
    self._data3D = data
    MagnificationMap.__init__(self, simulation, data[self._ind])
    self._ind = 0

  def setMoment(self, ind):
    self._index = ind
    self._data = self._data3D[ind]
