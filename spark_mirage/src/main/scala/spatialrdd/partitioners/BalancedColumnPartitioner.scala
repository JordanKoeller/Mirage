package spatialrdd.partitioners

import lensing.RayBank.Ray
import org.apache.spark.rdd.RDD
import org.apache.spark.RangePartitioner
class BalancedColumnPartitioner extends SpatialPartitioning {
  private var _numPartitions = 1
  private var _ranger: RangePartitioner[Double, Array[Byte]] = _

  def getPartition(key: Any): Int = {
    //Has the _mixer array to jumble the keys a bit. Gives a more even distribution of work across the cluster, while the RangePartitioner gives an equal distribution of data.
    _ranger.getPartition(key)
  }

  def getPartitions(key: (Double, Double), r: Double): Set[Int] = {
    (for (i <- _ranger.getPartition(key._1 - r) to _ranger.getPartition(key._2 + r)) yield i).toSet

  }

  def numPartitions: Int = {
    _numPartitions
  }

  override def profileData(data: RDD[Array[Ray]]): RDD[(Double,Array[Byte])] = {
    val serialRays = data.flatMap(arr => arr.map(r => (r.sourceX, r.packed)))
    _numPartitions = data.getNumPartitions
    _ranger = new RangePartitioner(_numPartitions, serialRays)
    serialRays
  }
}
