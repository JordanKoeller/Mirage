package spatialrdd.partitioners

import lensing.RayBankVal.Ray
import org.apache.spark.Partitioner
import org.apache.spark.rdd.RDD

import scala.reflect.ClassTag


trait SpatialPartitioning extends Partitioner {

  def profileData(data: RDD[Array[Ray]]):RDD[(Double,Array[Byte])]

  def getPartitions(key: (Double,Double), r: Double): Set[Int]

}
