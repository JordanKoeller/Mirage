from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.backends.backend_qt5agg import FigureCanvas, \
    NavigationToolbar2QT as NavigationToolbar

from matplotlib import pyplot as plt
from matplotlib.figure import Figure

class ImageCurveView:
    def __init__(self):
        self._cmap = plt.get_cmap('RdBu')
        self._with_colorbar = False

    @staticmethod
    def figure_with_context():
        from PyQt5 import QtWidgets
        window = QtWidgets.QMainWindow()
        widg = QtWidgets.QWidget()
        window.setCentralWidget(widg)
        layout = QtWidgets.QVBoxLayout(widg)
        fig = Figure()
        fc = FigureCanvas(fig)
        layout.addWidget(fc)
        navBar = NavigationToolbar(fc,window)
        window.addToolBar(navBar)
        return window, fc, fig

    @staticmethod
    def get_view(with_figure=False,name=None,with_canvas=False):
        # fig = 
        # fig = Figure()
        window, fc, fig = ImageCurveView.figure_with_context()
        gs = GridSpec(2,1,figure=fig,height_ratios = [1,5])
        window.show()
        curve_ax = fig.add_subplot(gs[0,0])
        img_ax = fig.add_subplot(gs[1,0])
        img_ax.set_axis_off()
        img_ax.set_frame_on(True)
        fig.set_tight_layout(True)
        if not with_figure:
            if with_canvas:
                return img_ax,curve_ax, fc
            else:
                return img_ax,curve_ax
        else:
            if with_canvas:
                return fig, img_ax, curve_ax, fc
            else:
                return fig, img_ax, curve_ax

