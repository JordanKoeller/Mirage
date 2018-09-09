package spatialrdd

import org.apache.spark.SparkContext
import org.apache.spark.SparkConf
import org.apache.spark.rdd.RDD
import spatialrdd.partitioners.SpatialPartitioning
import spatialrdd.partitioners.BalancedColumnPartitioner
// import spatialrdd.SpatialData
import org.apache.spark.storage.StorageLevel

import org.apache.spark.RangePartitioner
import utility.PixelAccumulator
import utility.IndexPair
import utility.DoublePair
import utility.mkPair
import utility.Index
import utility.PixelValue
import utility.pixelConstructor
import utility.pixelLongConstructor
import spatialrdd.partitioners.BalancedColumnPartitioner
import java.io.PrintWriter
import java.io.File

class RDDGrid(rdd: RDD[SpatialData]) extends RDDGridProperty {

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

}

object RDDGrid {
  def apply(data: RDD[(Double, Double)], partitioner: SpatialPartitioning = new BalancedColumnPartitioner, nodeStructure: IndexedSeq[(Double, Double)] => SpatialData = kDTree.apply): RDDGrid = {
    val rddProfiled = partitioner.profileData(data)
    val rddTraced = rddProfiled.partitionBy(partitioner)
    val glommed = rddTraced.glom()

    val ret = glommed.map(arr => nodeStructure(arr)).cache()
    new RDDGrid(ret)
  }
  def fromFile(file: String, numPartitions: Int, sc: SparkContext): RDDGrid = {
    val rdd = sc.objectFile[SpatialData](file, numPartitions)
    println("Created an RDD with " + rdd.count() + " elements")
    new RDDGrid(rdd)
  }
  //  private def writeFile(data: Array[Array[Double]],filename:String): Unit = {
  //    val dString = data.map(_.mkString(",")).mkString(":")
  //  }

}
