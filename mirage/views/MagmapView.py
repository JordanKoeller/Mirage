import numpy as np
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from mirage.util import Vec2D
from mirage.parameters import Simulation
from mirage.lens_analysis.MagnificationMap import MagnificationMap

class MagnificationMapView:
	def __init__(self,name=None):
		# self.rect = rect
		self.figure, self.axes = MagnificationMapView.get_view(True,name)
		self.connect()
		self._cmap = plt.get_cmap('RdBu_r')
		# self.figure = fig
		# self.axes= ax
		self.press = None
		self.line = Line2D([0,0],[0,0],color='r',antialiased=True)#,animated=True)
		self.axes.add_line(self.line)

	def connect(self):
		'connect to all the events we need'
		print("Connected")
		self.cidpress = self.figure.canvas.mpl_connect(
			'button_press_event', self.on_press)
		self.cidrelease = self.figure.canvas.mpl_connect(
			'button_release_event', self.on_release)
		self.cidmotion = self.figure.canvas.mpl_connect(
			'motion_notify_event', self.on_motion)

	def on_press(self, event):
		'on button press we will see if the mouse is over us and store some data'
		if event.inaxes != self.axes: return

		canvas = self.figure.canvas
		self.line.set_xdata([0,0])
		self.line.set_ydata([0,0])
		self.line.set_animated(True)
		canvas.draw()
		self.background = canvas.copy_from_bbox(self.axes.bbox)
		self.press = event.xdata, event.ydata
		self.axes.draw_artist(self.line)
		canvas.blit(self.axes.bbox)

	def on_motion(self, event):
		'on motion we will move the rect if the mouse is over us'
		if self.press is None: return
		if event.inaxes != self.axes: return
		xpress, ypress = self.press
		self.line.set_xdata([xpress,event.xdata])
		self.line.set_ydata([ypress,event.ydata])
		self.figure.canvas.restore_region(self.background)
		self.axes.draw_artist(self.line)
		self.figure.canvas.blit(self.axes.bbox)

	def on_release(self, event):
		'on release we reset the press data'
		start = self.press
		end = event.xdata, event.ydata
		print("From " + str(start) +" to " + str(end))
		self.press = None
		sv = Vec2D(start[0],start[0],self.map_unit)
		ev = Vec2D(end[0],end[0],self.map_unit)
		if self._magmap:
			plt.figure()
			plt.plot(self._magmap.slice_line(sv,ev))
		# self.figure.canvas.draw()

	def disconnect(self):
		'disconnect all the stored connection ids'
		self.figure.canvas.mpl_disconnect(self.cidpress)
		self.figure.canvas.mpl_disconnect(self.cidrelease)
		self.figure.canvas.mpl_disconnect(self.cidmotion)

	@staticmethod
	def get_view(with_figure=False,name=None):
		fig, axes = plt.subplots(num=name)
		axes.set_axis_off()
		fig.subplots_adjust(top=1,bottom=0,left=0,right=1)
		if not with_figure:
			return axes
		else:
			return (fig, axes)

	@property
	def magmap(self):
		return self._magmap
	

	@property
	def map_unit(self):
		return self.magmap.region.dimensions.unit

	def display(self,magmap:MagnificationMap):
		extent = magmap.region.dimensions/2
		x = extent.x.value
		y = extent.y.value
		self.axes.imshow(magmap.data,cmap=self._cmap,extent=[-x,x,-y,y])
		self._magmap = magmap
