from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.backends.backend_qt5agg import FigureCanvas, \
    NavigationToolbar2QT as NavigationToolbar

from matplotlib import pyplot as plt
from matplotlib.figure import Figure

class ImageCurveView:
    def __init__(self):
        self._cmap = plt.get_cmap('RdBu_r')
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
        window.addToolBar(NavigationToolbar(fc,window))
        return window, fc, fig

    @staticmethod
    def get_view(with_figure=False,name=None,with_canvas=False):
        # fig = 
        # fig = Figure()
        window, fc, fig = ImageCurveView.figure_with_context()
        gs = GridSpec(2,1,figure=fig,height_ratios = [1,5])
        # gsLower = GridSpecFromSubplotSpec(2,1,subplot_spec = gs[1,0],hspace=0.0,height_ratios=[11,1])
        # axes = fig.subplots(2,1)#,gridspec_kw={'height_ratios':[1,5]})
        window.show()
        import numpy as np
        # fig, axes = plt.subplots(2,1,num=name,gridspec_kw = {'height_ratios':[1, 5]})
        curve_ax = fig.add_subplot(gs[0,0])
        # colorbar = fig.add_subplot(gsLower[1,0])
        img_ax = fig.add_subplot(gs[1,0])
        img_ax.set_axis_off()
        # colorbar.get_yaxis().set_visible(False)
        img_ax.set_frame_on(True)
        # ex = np.linspace(0,1,1000)
        # ret = np.ndarray((10,len(ex)))
        # for i in range(10):
        #     ret[i,:] = ex
        # colorbar.imshow(ret)
        fig.set_tight_layout(True)
        # fig.subplots_adjust(top=0.988,bottom=0.006,left=0.039,right=0.983,hspace=0.1)
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

