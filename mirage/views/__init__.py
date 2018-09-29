# import matplotlib.style as mplstyle
# mplstyle.use(['dark_background','fast'])

from .MagmapView import MagnificationMapView


def run_example_rect():
	import numpy as np
	import matplotlib.pyplot as plt
	from matplotlib.lines import Line2D

	class DraggableRectangle:
		def __init__(self,fig,ax):
			# self.rect = rect
			self.figure = fig
			self.axes= ax
			self.press = None
			self.line = Line2D([0,0],[0,0],color='k',antialiased=True)#,animated=True)
			self.axes.add_line(self.line)

		def connect(self):
			'connect to all the events we need'
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
			dx = event.xdata - xpress
			dy = event.ydata - ypress
			self.line.set_xdata([xpress,event.xdata])
			self.line.set_ydata([ypress,event.ydata])
			self.figure.canvas.restore_region(self.background)
			self.axes.draw_artist(self.line)
			self.figure.canvas.blit(self.axes.bbox)

		def on_release(self, event):
			'on release we reset the press data'
			self.press = None
			self.figure.canvas.draw()

		def disconnect(self):
			'disconnect all the stored connection ids'
			self.figure.canvas.mpl_disconnect(self.cidpress)
			self.figure.canvas.mpl_disconnect(self.cidrelease)
			self.figure.canvas.mpl_disconnect(self.cidmotion)

	fig = plt.figure()
	ax = fig.add_subplot(111)
	dr = DraggableRectangle(fig,ax)
	dr.connect()
	plt.show()
	return dr
	# rects = ax.bar(range(10), 20*np.random.rand(10))
	# drs = []
	# for rect in rects:
	# 	dr = DraggableRectangle(rect)
	# 	dr.connect()
	# 	drs.append(dr)


def line_example():
	from matplotlib import pyplot as plt

	class LineBuilder:
		def __init__(self, line):
			self.line = line
			self.xs = list(line.get_xdata())
			self.ys = list(line.get_ydata())
			self.cid = line.figure.canvas.mpl_connect('button_press_event', self)

		def __call__(self, event):
			print('click', event)
			if event.inaxes!=self.line.axes: return
			self.xs.append(event.xdata)
			self.ys.append(event.ydata)
			self.line.set_data(self.xs, self.ys)
			self.line.figure.canvas.draw()

	fig = plt.figure()
	ax = fig.add_subplot(111)
	ax.set_title('click to build line segments')
	line, = ax.plot([0], [0])  # empty line
	linebuilder = LineBuilder(line)

	plt.show()

# def click_drag_line():
# from __future__ import print_function
# """
# Do a mouseclick somewhere, move the mouse to some destination, release
# the button.  This class gives click- and release-events and also draws
# a line or a box from the click-point to the actual mouseposition
# (within the same axes) until the button is released.  Within the
# method 'self.ignore()' it is checked whether the button from eventpress
# and eventrelease are the same.

# """
# from matplotlib.widgets import RectangleSelector
# import numpy as np
# import matplotlib.pyplot as plt


# def line_select_callback(eclick, erelease):
# 	'eclick and erelease are the press and release events'
# 	x1, y1 = eclick.xdata, eclick.ydata
# 	x2, y2 = erelease.xdata, erelease.ydata
# 	print("(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (x1, y1, x2, y2))
# 	print(" The button you used were: %s %s" % (eclick.button, erelease.button))


# def toggle_selector(event):
# 	print(' Key pressed.')
# 	if event.key in ['Q', 'q'] and toggle_selector.RS.active:
# 		print(' RectangleSelector deactivated.')
# 		toggle_selector.RS.set_active(False)
# 	if event.key in ['A', 'a'] and not toggle_selector.RS.active:
# 		print(' RectangleSelector activated.')
# 		toggle_selector.RS.set_active(True)


# fig, current_ax = plt.subplots()                 # make a new plotting range
# N = 100000                                       # If N is large one can see
# x = np.linspace(0.0, 10.0, N)                    # improvement by use blitting!

# plt.plot(x, +np.sin(.2*np.pi*x), lw=3.5, c='b', alpha=.7)  # plot something
# plt.plot(x, +np.cos(.2*np.pi*x), lw=3.5, c='r', alpha=.5)
# plt.plot(x, -np.sin(.2*np.pi*x), lw=3.5, c='g', alpha=.3)

# print("\n      click  -->  release")

# # drawtype is 'box' or 'line' or 'none'
# toggle_selector.RS = RectangleSelector(current_ax, line_select_callback,
# 									   drawtype='box', useblit=True,
# 									   button=[1, 3],  # don't use middle button
# 									   minspanx=5, minspany=5,
# 									   spancoords='pixels',
# 									   interactive=True)
# plt.connect('key_press_event', toggle_selector)
# plt.show()