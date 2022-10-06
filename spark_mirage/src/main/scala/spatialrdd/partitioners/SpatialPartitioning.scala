package spatialrdd.partitioners

import lensing.RayBank
import org.apache.spark.Partitioner
import org.apache.spark.rdd.RDD

import scala.reflect.ClassTag



trait SpatialPartitioning extends Partitioner {

//  def profileData[A <: RayBank: ClassTag](data: RDD[A]):RDD[(Double,Array[Byte])]

  def getPartitions(key: (Double,Double), r: Double): Set[Int]

}
