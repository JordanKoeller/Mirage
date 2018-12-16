package spatialrdd

import lensing.RayBank
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import spatialrdd.partitioners.SpatialPartitioning
import utility.DoublePair
import utility.Index
import utility.pixelConstructor
import utility.pixelLongConstructor
import spatialrdd.partitioners.BalancedColumnPartitioner

import scala.reflect.ClassTag

class RDDGrid(rdd: RDD[CausticTree]) extends RDDGridProperty {

  sealed case class RetValue(x: Int, y: Int, value: Int)

  def queryPointsFromGen(gen: GridGenerator, radius: Double, sc: SparkContext, verbose: Boolean = false): Array[Array[Int]] = {
    val bgen = sc.broadcast(gen)
    val r = sc.broadcast(radius)
    val queries = rdd.flatMap { grid =>
      gen.flatMap { qPt =>
        if (grid.intersects(qPt.x, qPt.y, r.value)) {
          val num = grid.query_point_count(qPt.x, qPt.y, r.value)
          if (num != 0) pixelLongConstructor(qPt.px, qPt.py, num) :: Nil else Nil
        } else Nil
      }
    }

    val collected = queries.collect()
    val ret = Array.fill(gen.xDim, gen.yDim)(0)
    collected.foreach { el =>
      val elem = pixelConstructor(el)
      ret(elem.x)(elem.y) += elem.value
    }
    ret
  }
  def queryPoints(pts: Array[Array[DoublePair]], radius: Double, sc: SparkContext, verbose: Boolean = false): Array[Array[Index]] = {
    val r = sc.broadcast(radius)
    val queryPts = sc.broadcast(pts)
    val queries = rdd.flatMap { grid =>
      var rett: List[RetValue] = Nil
      for (i <- 0 until queryPts.value.length) {
        for (j <- 0 until queryPts.value(i).length) {
          if (grid.intersects(queryPts.value(i)(j)._1, queryPts.value(i)(j)._2, r.value)) {
            val num = grid.query_point_count(queryPts.value(i)(j)._1, queryPts.value(i)(j)._2, r.value)
            if (num != 0) rett ::= RetValue(i, j, num)
          }
        }
      }
      rett
    }
    val collected = queries.collect()
    val ret = Array.fill(pts.length)(Array[Int]())
    for (i <- 0 until pts.length) ret(i) = Array.fill(pts(i).length)(0)
    collected.foreach { elem =>
      ret(elem.x)(elem.y) += elem.value
    }
    ret
  }

  def queryCaustics(pts: Array[Array[DoublePair]], radius: Double, sc: SparkContext, verbose: Boolean = false): Array[Array[Boolean]] = {
    val r = sc.broadcast(radius)
    val queryPts = sc.broadcast(pts)
    val queries = rdd.flatMap { grid =>
      var rett: List[RetValue] = Nil
      for (i <- 0 until queryPts.value.length) {
        for (j <- 0 until queryPts.value(i).length) {
          if (grid.intersects(queryPts.value(i)(j)._1, queryPts.value(i)(j)._2, r.value)) {
            val num = grid.searchCaustics(queryPts.value(i)(j)._1, queryPts.value(i)(j)._2, r.value)
            if (num) rett ::= RetValue(i, j, 1)
          }
        }
      }
      rett
    }
    val collected = queries.collect()
    val ret = Array.fill(pts.length)(Array[Boolean]())
    for (i <- 0 until pts.length) ret(i) = Array.fill(pts(i).length)(false)
    collected.foreach { elem =>
      if (elem.value == 1) {
        ret(elem.x)(elem.y) = true
      }
    }
    ret
  }

  def query_curve(pts: Array[DoublePair], radius: Double, sc: SparkContext): Array[Int] = {
    val r = sc.broadcast(radius)
    val queryPts = sc.broadcast(pts)
    val queries = rdd.flatMap { grid =>
      var rett: List[Long] = Nil
      for (i <- 0 until queryPts.value.length) {
        if (grid.intersects(queryPts.value(i)._1, queryPts.value(i)._2, r.value)) {
          val num = grid.query_point_count(queryPts.value(i)._1, queryPts.value(i)._2, r.value)
          rett ::= pixelLongConstructor(i, 0, num)
        }
      }
      rett
    }
    val ret = Array.fill(pts.length)(0)
    queries.collect().foreach { elem =>
      val e = pixelConstructor(elem)
      ret(e.x) = e.value
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
//  def apply(data: RDD[Array[Ray]], partitioner: SpatialPartitioning = new BalancedColumnPartitioner, nodeStructure: Array[Ray] => SpatialData = kDTree.apply): RDDGrid = {
//    val rddProfiled = partitioner.profileData(data)
//    val rddTraced = rddProfiled.partitionBy(partitioner)
//    val glommed: RDD[Array[Ray]] = rddTraced.map(_._2).glom().map(RayBankVal.apply)
//
//    val ret = glommed.map(arr => nodeStructure(arr)).cache()
//    new RDDGrid(ret)
//  }
  def apply[A <: RayBank: ClassTag](data: RDD[A], partitioner: SpatialPartitioning = new BalancedColumnPartitioner, nodeStructure: A => CausticTree): RDDGrid = {
    val ret = data.map(arr => nodeStructure(arr)).cache
    new RDDGrid(ret)
  }
//  def fromFile(file: String, numPartitions: Int, sc: SparkContext): RDDGrid = {
//    val rdd = sc.objectFile[SpatialData](file, numPartitions)
//    new RDDGrid(rdd)
//  }

}
