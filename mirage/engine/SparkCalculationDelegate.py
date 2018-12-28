import tempfile


from astropy import units as u
import numpy as np

from mirage.parameters import MicrolensingParameters
from mirage.util import Vec2D
from .CalculationDelegate import CalculationDelegate

_sc = None

def _get_spark_context():
    global _sc
    if not _sc:
        from pyspark.conf import SparkConf
        from pyspark.context import SparkContext
        from mirage import GlobalPreferences
        _sc = SparkContext.getOrCreate()
        _sc.setLogLevel("WARN")
    return _sc

class MicroSparkDelegate(CalculationDelegate):

    def __init__(self,spark_context = None):
        self._spark_context = spark_context or _get_spark_context()

    @property
    def spark_context(self):
        return self._spark_context

    def reconfigure(self,parameters:MicrolensingParameters):
        smooth, starry, shear = parameters.mass_descriptors
        dimensions = parameters.ray_region.resolution
        dTheta = parameters.ray_region.dTheta
        width = dimensions.x.value
        height = dimensions.y.value
        jrdd = self._spark_context.emptyRDD()._jrdd

        #Make sure to put input data into units of xi_0!!
        dx = dTheta.x.to(parameters.xi_0).value
        dy = dTheta.y.to(parameters.xi_0).value
        #I also need to subtract off the center of the image from the stars.
        stars = parameters.stars
        stars[:,0] = (stars[:,0])# - parameters.image_center.x.to('rad').value)/xi_0
        stars[:,1] = (stars[:,1])# - parameters.image_center.y.to('rad').value)/xi_0
        starCount = stars.shape[0]
        #Now that inputs are properly normalized, can proceed.
        starfile = self.get_star_file(stars)

        #And now calling the jvm:
        return self.spark_context._jvm.main.Main.createRDDGrid(
            starfile,
            starCount,
            shear,
            smooth,
            dx,
            dy,
            width,
            height,
            jrdd,
            self.core_count)

    def get_connecting_rays(self,location:Vec2D, radius:u.Quantity) -> np.ndarray:
        print("GET_CONNECTING_RAYS not implimented for MicroSparkDelegate")

    def get_ray_count(self,location:Vec2D, radius:u.Quantity) -> int:
        pass

    def query_points(self,points:np.ndarray, radius:u.Quantity) -> np.ndarray:
        query_point_file = self.get_data_file(points)
        query_radius = radius.value
        jrdd = self._spark_context.emptyRDD()._jrdd
        file = tempfile.NamedTemporaryFile('w+',delete = False)
        self.spark_context._jvm.main.Main.sampleLightCurves(query_point_file,file.name,points.shape[0],query_radius,jrdd)
        returned_data = self.get_returned_data(file.name,points)
        return np.array(returned_data)

    def query_caustics(self,points:Vec2D,radius:u.Quantity) -> np.ndarray:
        query_point_file = self.get_data_file(points)
        query_radius = radius.value
        jrdd = self._spark_context.emptyRDD()._jrdd
        file = tempfile.NamedTemporaryFile("w+",delete = False)
        self.spark_context._jvm.main.Main.sampleCaustics(query_point_file,file.name,points.shape[0],query_radius,jrdd)
        returned_data = self.get_returned_data(file.name,points)
        return np.array(returned_data,dtype=np.int32)

    def query_region(self,region,radius:u.Quantity) -> np.ndarray:
        query_radius = radius.value
        jrdd = self._spark_context.emptyRDD()._jrdd
        file = tempfile.NamedTemporaryFile("w+",delete = False)
        left = region.center - region.dimensions/2.0
        right = region.center + region.dimensions/2.0
        args = (left.x.value, left.y.value,
            right.x.value,
            right.y.value,
            region.resolution.x.value,
            region.resolution.y.value,
            query_radius,
            file.name,
            jrdd)
        self.spark_context._jvm.main.Main.queryPoints(*args)
        returned_data = self.get_returned_data(file.name,region.pixels)
        return np.array(returned_data,dtype=np.int32)

    def get_star_file(self,data:np.ndarray):
        file = tempfile.NamedTemporaryFile('w+',delete = False)
        data.tofile(file)
        file.close()
        return file.name

    def get_data_file(self,data:np.ndarray):
        # print("Shape of " + str(data.shape))
        # print(data)
        file = tempfile.NamedTemporaryFile('w+',delete = False)
        sizes = np.ndarray(data.shape[0],dtype=np.int32)
#        print(data)
        for i in range(data.shape[0]):
            sizes[i] = data[i].shape[0]
        sizes.tofile(file)
        for row in data:
            row.tofile(file)
        file.close()
        return file.name

    def get_returned_data(self,filename,qpts):
        ret = np.ndarray(qpts.shape[0],dtype=object)
        file = open(filename,'rb')
        if qpts.dtype == object:
            for i in range(qpts.shape[0]):
                ret[i] = np.fromfile(file,np.int32,qpts[i].size)
            file.close()
            return ret
        else:
            shape = qpts.shape
            ret = np.fromfile(file,np.int32,shape[0]*shape[1])
            return np.reshape(ret,(shape[0],shape[1]))


