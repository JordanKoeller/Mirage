from matplotlib import pyplot as plt

class ImageCurveView:
    def __init__(self):
        self._cmap = plt.get_cmap('RdBu_r')

    @staticmethod
    def get_view(with_figure=False,name=None):
        fig = plt.figure(name)
        axes = fig.subplots(2,1,gridspec_kw={'height_ratios':[1,5]})
        fig.show()
        # fig, axes = plt.subplots(2,1,num=name,gridspec_kw = {'height_ratios':[1, 5]})
        curve_ax, img_ax = axes
        img_ax.set_axis_off()
        img_ax.set_frame_on(True)
        fig.subplots_adjust(top=0.988,bottom=0.006,left=0.039,right=0.983,hspace=0.075)
        if not with_figure:
            return img_ax,curve_ax
        else:
            return fig, img_ax, curve_ax

