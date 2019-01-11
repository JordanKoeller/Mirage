package spatialrdd

import lensing.RayBank
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import org.apache.spark.storage.StorageLevel
import spatialrdd.partitioners.SpatialPartitioning
import utility._
import spatialrdd.partitioners.BalancedColumnPartitioner

import scala.reflect.ClassTag

class RDDGrid[A <: RayBank : ClassTag, SD <: SpatialData : ClassTag](rdd: RDD[SD]) extends RDDGridProperty {

  def queryPointsFromGen(gen: GridGenerator, radius: Double, sc: SparkContext, verbose: Boolean = false): Array[Array[Int]] = {
    val bgen = sc.broadcast(gen)
    val r = sc.broadcast(radius)
    val queries = rdd.flatMap { grid =>
      var rett: List[(Long, Int)] = Nil
      val iter = bgen.value.iterator
      while (iter.hasNext) {
        val qPt = iter.next
        if (grid.intersects(qPt.x, qPt.y, r.value)) {
          val num = grid.query_point_count(qPt.x, qPt.y, r.value)
          if (num != 0) rett ::= (mkPair(qPt.px, qPt.py).v, num)
        }
      }
      rett
    }
    bgen.unpersist()
    val ret = Array.fill(gen.xDim, gen.yDim)(0)
    this.collect(queries,ret)
    ret
  }

  def queryPoints(pts: Array[Array[DoublePair]], radius: Double, sc: SparkContext, verbose: Boolean = false): Array[Array[Index]] = {
    val r = sc.broadcast(radius)
    val queryBank = QueryPointBank(pts)
    val queryPts = sc.broadcast(queryBank)
    val queries = rdd.flatMap { grid =>
      var rett: List[(Long,Int)] = Nil
      val iter = queryPts.value.iterator
      while (iter.hasNext) {
        val pt = iter.next()
        if (grid.intersects(pt.x,pt.y,radius)) {
          val num = grid.query_point_count(pt.x,pt.y,r.value)
          if (num != 0) rett ::= (mkPair(pt.i,pt.j).v,num)
        }
      }
      rett
    }
    queryPts.unpersist(true)
    val ret = Array.fill(pts.length)(Array[Int]())
    for (i <- 0 until pts.length) ret(i) = Array.fill(pts(i).length)(0)
    this.collect(queries,ret)
    ret
  }


  def searchBatch(iter:QueryIterator,radius:Double,sc:SparkContext):Array[Array[Int]] = {
    while (iter.hasNext) {
      println("Next Batch")
      val localIter = iter.nextBatch()
      val broadcasted = sc.broadcast(localIter)
      val queries = rdd.flatMap {
        grid =>
          var rett: List[(Int,Int)] = Nil
          for (i <- 0 until broadcasted.value.size) {
            val qloc = broadcasted.value(i)
            val num = grid.query_point_count(qloc._1,qloc._2,radius)
            if (num != 0) rett ::= (i,num)
          }
          rett
      }
      val reduced = queries.reduceByKey((acc,n) => acc + n).collect
      val batchResult = reduced.sortBy(_._1).map(_._2)
      iter.takeInResult(batchResult)
    }
    iter.collect
  }

  private def collect(data:RDD[(Long,Int)], accumulator:Array[Array[Int]]):Unit = {
    val reduced = data.reduceByKey((acc,cnt) => acc + cnt).map{elem => new IndexPair(elem._1) -> elem._2}
    val collected = reduced.collect
    collected.foreach{elem => accumulator(elem._1.x)(elem._1.y) += elem._2}
  }

//  def queryCaustics(pts: Array[Array[DoublePair]], radius: Double, sc: SparkContext, verbose: Boolean = false): Array[Array[Boolean]] = {
//    val r = sc.broadcast(radius)
//    val queryPts = sc.broadcast(pts)
//    val queries = rdd.flatMap { grid =>
//      var rett: List[RetValue] = Nil
//      for (i <- 0 until queryPts.value.length) {
//        for (j <- 0 until queryPts.value(i).length) {
//          if (grid.intersects(queryPts.value(i)(j)._1, queryPts.value(i)(j)._2, r.value)) {
//            val num = grid.searchCaustics(queryPts.value(i)(j)._1, queryPts.value(i)(j)._2, r.value)
//            if (num) rett ::= RetValue(i, j, 1)
//          }
//        }
//      }
//      rett
//    }
//    val collected = queries.collect()
//    val ret = Array.fill(pts.length)(Array[Boolean]())
//    for (i <- 0 until pts.length) ret(i) = Array.fill(pts(i).length)(false)
//    collected.foreach { elem =>
//      if (elem.value == 1) {
//        ret(elem.x)(elem.y) = true
//      }
//    }
//    ret
//  }

  def query_curve(pts: Array[DoublePair], radius: Double, sc: SparkContext): Array[Int] = {
    val r = sc.broadcast(radius)
    val queryPts = sc.broadcast(pts)
    val queries = rdd.flatMap { grid =>
      var rett: List[(Int,Int)] = Nil
      for (i <- 0 until queryPts.value.length) {
        if (grid.intersects(queryPts.value(i)._1, queryPts.value(i)._2, r.value)) {
          val num = grid.query_point_count(queryPts.value(i)._1, queryPts.value(i)._2, r.value)
          if (num != 0) rett ::= (i,num)
        }
      }
      rett
    }
    queryPts.unpersist()
    val ret = Array.fill(pts.length)(0)
    val reduced = queries.reduceByKey((acc,n) => acc + n)
    val collected = reduced.collect
    collected.foreach { elem =>
      val k = elem._1
      val v = elem._2
      ret(k) = v
    }
    ret
  }

  def count: Long = rdd.count()

  def destroy(): Unit = {
    rdd.unpersist(blocking = true)
  }

  def printSuccess: Unit = {
    return
  }

  def saveToFile(fname: String): Unit = {
    rdd.saveAsObjectFile(fname)
  }

  override def cache(): Unit = {
    rdd.persist()
  }

}

object RDDGrid {

  val numBatches = 100

  def apply[A <: RayBank: ClassTag, SD <: SpatialData : ClassTag](data: RDD[A], partitioner: SpatialPartitioning = new BalancedColumnPartitioner, nodeStructure: A => SD): RDDGrid[A,SD] = {
    val ret = data.map(arr => nodeStructure(arr)).persist(StorageLevel.MEMORY_ONLY).setName("RDDGrid")
    new RDDGrid(ret)
  }

}
