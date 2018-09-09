package spatialrdd
import scala.collection.mutable
import utility.DoublePair
import utility.Index
import math.sqrt

//class MemGrid(grid: Array[Array[mutable.ArrayBuffer[Double]]], _hashX: Double => Int, _hashY: Double => Int, sz: Int, val partitionIndex: Int) extends SpatialData {
class MemGrid(grid: mutable.Map[Index, mutable.Map[Index, mutable.ArrayBuffer[Double]]], hashXPair: (HashFunc, Dehasher), hashYPair: (HashFunc, Dehasher), sz: Int, extremes: (Double, Double, Double, Double)) extends SpatialData {

  private def _hashX = hashXPair._1

  private def _hashY = hashYPair._1

  private def _dehashX = hashXPair._2

  private def _dehashY = hashYPair._2

  private def _hashFunction(xx: Double, yy: Double): (Int, Int) = {
    val x = _hashX(xx)
    val y = _hashY(yy)
    (x, y)
  }

  private def _query_bucket(i: Int, j: Int, x: Double, y: Double, r2: Double): Int = {
    if (grid.contains(i) && grid(i).contains(j)) {
      val queryType = query_type(i, j, r2, x, y)
      if (queryType == -1) 0
      else if (queryType == 1) grid(i)(j).size / 2
      else if (queryType == 0 && grid(i)(j).size > 0) {
        var counter = 0
        var ind = 0
        var dx = 0.0
        var dy = 0.0
        while (ind < grid(i)(j).size) {
          dx = grid(i)(j)(ind) - x
          dy = grid(i)(j)(ind + 1) - y
          if (r2 >= dx * dx + dy * dy) counter += 1
          ind += 2
        }
        counter

      } else 0

    } else 0
  }

  private def query_type(i: Int, j: Int, r2: Double, x: Double, y: Double): Int = {
    //First figure out the quadrant
    //Then know how to shift i and j to find which corners I need to check.
    var ret = 0
    ret += pointInCircle(x, y, r2, _dehashX(i), _dehashY(j))
    ret += pointInCircle(x, y, r2, _dehashX(i + 1), _dehashY(j))
    ret += pointInCircle(x, y, r2, _dehashX(i), _dehashY(j + 1))
    ret += pointInCircle(x, y, r2, _dehashX(i + 1), _dehashY(j + 1))
    if (ret == 4) 1 else 0
    //1 means all enclosed
    //-1 means completely excluded
    //0 means partially enclosed
  }
  def intersects(x: Double, y: Double, r: Double): Boolean = {
    //Checks if the point you want to query overlaps at all with the MemGrid instance
    val w = extremes._2 - extremes._1
    val h = extremes._4 - extremes._3
    val rx = extremes._1 + w / 2
    val ry = extremes._3 + h / 2
    circleRectOverlap(x, y, r, rx, ry, w, h)
  }

  private def circleRectOverlap(cx: Double, cy: Double, r: Double, rx: Double, ry: Double, w: Double, h: Double): Boolean = {
    val cdx = math.abs(cx - rx)
    val cdy = math.abs(cy - ry)
    if (cdx > (w / 2.0 + r)) false
    else if (cdy > (h / 2.0 + r)) false
    else if (cdx <= w / 2.0) true
    else if (cdy <= h / 2.0) true
    else {
      val dx = cdx - w / 2.0
      val dy = cdy - h / 2.0
      dx * dx + dy * dy <= r * r
    }

  }

  private def pointInCircle(cx: Double, cy: Double, r2: Double, x: Double, y: Double): Int = {
    val dx = x - cx
    val dy = y - cy
    if (r2 >= dx * dx + dy * dy) 1 else 0
  }

  override def query_point_count(x: Double, y: Double, r: Double): Int = {
    val center = _hashFunction(x, y)
    val intRX = _hashX(x + r) + 2 - center._1
    var intRY = _hashY(y + r) + 2 - center._2
    val r2 = r * r
    var counter = 0
    var i = 1
    var j = 1
    counter += _query_bucket(center._1, center._2, x, y, r2) //Query center

    while (i <= intRX) { //Query x - axis
      counter += _query_bucket(center._1 - i, center._2, x, y, r2)
      counter += _query_bucket(center._1 + i, center._2, x, y, r2)
      //      }
      i += 1
    }
    i = 1
    while (j <= intRY) {
      counter += _query_bucket(center._1, center._2 + j, x, y, r2)
      counter += _query_bucket(center._1, center._2 - j, x, y, r2)
      //      }
      j += 1
    }
    j = 1
    while (i <= intRX) {
      val xSpread = _dehashX(i) - x
      intRY = _hashY(y + sqrt(r2 - xSpread * xSpread)) + 2
      while (j <= intRY) {
        counter += _query_bucket(center._1 + i, center._2 + j, x, y, r2)
        counter += _query_bucket(center._1 - i, center._2 + j, x, y, r2)
        counter += _query_bucket(center._1 + i, center._2 - j, x, y, r2)
        counter += _query_bucket(center._1 - i, center._2 - j, x, y, r2)
        //        }
        j += 1
      }
      j = 1
      i += 1
    }
    counter
  }


  override def size: Int = sz

}

object MemGrid {

  val bucketFactor = 1
  def apply(data: IndexedSeq[DoublePair]): MemGrid = {
    val xHashPair = hashDehashPair(data, (l: DoublePair) => l._1, math.sqrt(data.size).toInt * bucketFactor)
    val yHashPair = hashDehashPair(data, (l: DoublePair) => l._2, math.sqrt(data.size).toInt * bucketFactor)
    val grid: mutable.Map[Index, mutable.Map[Index, mutable.ArrayBuffer[Double]]] = mutable.Map()
    var rover = 0
    var xMin = Double.MaxValue
    var xMax = -Double.MaxValue
    var yMin = Double.MaxValue
    var yMax = -Double.MaxValue
    while (rover < data.size) {
      val elem = data(rover)
      val x = xHashPair._1(elem._1)
      val y = yHashPair._1(elem._2)
      if (!grid.contains(x)) grid(x) = mutable.Map()
      if (!grid(x).contains(y)) grid(x)(y) = mutable.ArrayBuffer()
      grid(x)(y) += elem._1
      grid(x)(y) += elem._2
      rover += 1
      if (elem._1 < xMin) xMin = elem._1
      if (elem._2 < yMin) yMin = elem._2
      if (elem._2 > yMax) yMax = elem._2
      if (elem._1 > xMax) xMax = elem._1
    }
    new MemGrid(grid, xHashPair, yHashPair, data.size, (xMin, xMax, yMin, yMax))
  }
}
