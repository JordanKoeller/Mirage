import tempfile
import io

from scipy.spatial import cKDTree
from astropy import units as u
import numpy as np

from mirage.parameters import Parameters,MicrolensingParameters
from mirage.util import Vec2D
from .CalculationDelegate import CalculationDelegate

_sc = None


def _get_spark_context():
    global _sc
    if not _sc:
        from pyspark.conf import SparkConf
        from pyspark.context import SparkContext
        from mirage import GlobalPreferences
        settings = GlobalPreferences['spark_configuration']
        SparkContext.setSystemProperty("spark.executor.memory",settings['executor-memory'])
        SparkContext.setSystemProperty("spark.driver.memory",settings['driver-memory'])
        conf = SparkConf()
        conf = conf.setMaster(settings['master'])
        conf = conf.set('spark.driver.maxResultSize',settings['driver-memory'])
        conf = conf.set('spark.scheduler.mode','FAIR')
        _sc = SparkContext.getOrCreate(conf=conf)
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
        print(starCount)
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
        print("Querying")
        query_point_file = self.get_data_file(points)
        query_radius = radius.value
        jrdd = self._spark_context.emptyRDD()._jrdd
        file = tempfile.NamedTemporaryFile('w+',delete = False)
        print("PointShape is of " + str(points.shape))
        self.spark_context._jvm.main.Main.sampleLightCurves(query_point_file,file.name,points.shape[0],query_radius,jrdd)
        returned_data = self.get_returned_data(file.name,points.shape)
        return np.array(returned_data)

    def get_star_file(self,data:np.ndarray):
        # row_delimiter = "\n"
        # col_delimiter = ","
        file = tempfile.NamedTemporaryFile('w+',delete = False)
        data.tofile(file)
        print(data)
        file.close()
        # for i in range(data.shape[0]):
        #     for j in range(data.shape[1]):
        #         string = str(data[i,j]) + col_delimiter
        #         file.write(string)
        #     file.seek(file.tell()-1)
        #     file.write(row_delimiter)
        # file.close()
        return file.name

    def get_data_file(self,data:np.ndarray):
        # row_delimiter = "\n"
        # col_delimiter = ","
        file = tempfile.NamedTemporaryFile('w+',delete = False)
        sizes = np.ndarray(data.shape[0],dtype=np.int32)
        for i in range(data.shape[0]):
            print(data[i].shape[0])
            sizes[i] = data[i].shape[0]
        sizes.tofile(file)
        data.tofile(file)
        file.close()
        # for i in range(data.shape[0]):
        #     for j in range(len(data[i])):
        #         string = str(data[i][j,0]) + ":" + str(data[i][j,1])
        #         file.write(string + col_delimiter)
        #     file.seek(file.tell()-1)
        #     file.write(row_delimiter)
        # file.close()
        return file.name

    def get_returned_data(self,filename,shape):
        # import time
        # time.sleep(10000000)
        ret = np.fromfile(filename,np.int32,shape[0]*shape[1])
        return np.reshape(ret,(shape[0],shape[1]))
        # with open(filename) as data:
        #     big_string = data.read()
        #     lines = big_string.split("\n")
        #     elems = list(map(lambda line: line.split(","),lines))
        #     nums = list(map(lambda line: list(map(lambda elem: float(elem),line)),elems))
        #     ret = np.array(nums)
        #     return ret


