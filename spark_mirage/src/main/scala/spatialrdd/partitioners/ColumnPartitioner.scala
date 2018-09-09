//package spatialrdd.partitioners
//
//import org.apache.spark.rdd.RDD
//import spatialrdd.XYDoublePair
//import spatialrdd.equalHashing
//import spatialrdd.MinMax
//
//class ColumnPartitioner extends SpatialPartitioning {
//  private var _hashFunc: Double => Int = _
//  private var _numPartitions = 1
//  def getPartition(key: Any): Int = {
//    val ret = key match {
//      case dub: Double => _hashFunc(dub)
//      case xyp: XYDoublePair => _hashFunc(xyp.x)
//    }
//    ret
//  }
//
//  def getPartitions(key: XYDoublePair, r: Double): Set[Int] = {
//    (for (i <- getPartition(key.x - r) to getPartition(key.x+r)) yield i).toSet
//
//  }
//
//  def numPartitions: Int = {
//    _numPartitions
//  }
//
//  override def profileData(data: RDD[XYDoublePair]): RDD[(Double, Double)] = {
//    _numPartitions = data.getNumPartitions * 3
//    val hashFunc = equalHashing(data, (l: XYDoublePair) => l.x, numPartitions)
//    _hashFunc = (l:Double) => math.min(numPartitions-1,hashFunc(l))
//    data.mapPartitions(elemIter => elemIter.map(elem => (elem.x, elem.y)),true)
//  }
//}
