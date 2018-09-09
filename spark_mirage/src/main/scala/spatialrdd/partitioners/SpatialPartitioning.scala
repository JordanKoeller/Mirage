package spatialrdd.partitioners

import org.apache.spark.Partitioner
import org.apache.spark.rdd.RDD
import scala.reflect.ClassTag


trait SpatialPartitioning extends Partitioner {

  def profileData(data: RDD[(Double,Double)]):RDD[(Double,Double)]

  def getPartitions(key: (Double,Double), r: Double): Set[Int]

}
