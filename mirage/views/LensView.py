
class LensView:
    def __init__(self,name=None):
        self.figure, self.axes = LensView.get_view(True,name)

    @staticmethod
    def get_view(with_figure=False,name=None):
        from matplotlib import pyplot as plt
        fig = plt.figure()
        axes = fig.subplots(1,1)
        fig.show()

