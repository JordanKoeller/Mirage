package spatialrdd.partitioners

import org.apache.spark.rdd.RDD
import org.apache.spark.RangePartitioner
import spatialrdd.equalHashing
import spatialrdd.MinMax

import utility.DoublePair
class BalancedColumnPartitioner extends SpatialPartitioning {
  private var _numPartitions = 1
  private var _ranger: RangePartitioner[Double, Double] = _
  //  private var _mixer:Array[Int] = _

  def getPartition(key: Any): Int = {
    //Has the _mixer array to jumble the keys a bit. Gives a more even distribution of work across the cluster, while the RangePartitioner gives an equal distribution of data.
    _ranger.getPartition(key)
  }

  def getPartitions(key: (Double, Double), r: Double): Set[Int] = {
    (for (i <- _ranger.getPartition(key._1 - r) to _ranger.getPartition(key._2 + r)) yield i).toSet
    //    val range = _ranger.getPartition(key._1 - r) to _ranger.getPartition(key._2+r)
    //    range.toSet

  }

  def numPartitions: Int = {
    _numPartitions
  }

  override def profileData(data: RDD[DoublePair]): RDD[DoublePair] = {
    _numPartitions = data.getNumPartitions
    _ranger = new RangePartitioner(_numPartitions, data)
    data
  }
}
