package spatialrdd

import lensing.{CountCollector, RayBank, RayCollector}
import utility.Result
import utility.ResultZero

class OptTree[A <: RayBank](values:A, branchSize: Int) extends SpatialData {

  private val xExtremes = minMax(values,(a,b) => a.sourceX(b))
  private val yExtremes = minMax(values,(a,b) => a.sourceY(b))
  private val boxes = list_constructNodes()

  private def minMax(vals: A,func:(A,Int) => Double): (Double, Double) = {
    vals.indices.foldLeft((Double.MaxValue, Double.MinValue)) { (best, ind) =>
      (math.min(best._1, func(vals,ind)), math.max(best._2, func(vals,ind)))
    }
  }

  class Node(val indI: Int, val indJ: Int, var split: Double) extends Serializable {
    def size: Int = indJ - indI

    override def toString() = "Node"

    def search(x: Double, y: Double, r2: Double, collector:RayCollector): Result = {
      var aggregator = ResultZero
      var dx = 0.0
      var dy = 0.0
      for (i <- indI until indJ) {
        if (collector.properParity(values, i)) {
          dx = values.sourceX(i) - x
          dy = values.sourceY(i) - y
          if (dx * dx + dy * dy <= r2) {
            aggregator += collector(values, i)
          }
        }
      }
      aggregator
    }

    def search(x1: Double, x2: Double, y1:Double, y2:Double, collector:RayCollector): Result = {
      var aggregator = ResultZero
      for (i <- indI until indJ) {
        if (collector.properParity(values,i) && values.sourceX(i) > x1 && values.sourceX(i) < x2 && values.sourceY(i) < y2 && values.sourceY(i) > y1) {
          aggregator += collector(values,i)
        }
      }
      aggregator
    }

    def overlapsRight(x1: Double, x2: Double, y1:Double, y2:Double, level: Int): Boolean = {
      if (level % 2 == 0) {
        split < x2
      } else {
        split < y2
      }
    }

    def overlapsLeft(x1: Double, x2: Double, y1:Double, y2:Double, level: Int): Boolean = {
      if (level % 2 == 0) {
        split > x1
      } else {
        split > y2
      }
    }

    def overlapsRight(x: Double, y: Double, r: Double, level: Int): Boolean = {
      if (level % 2 == 0) {
        split < r + x
      } else {
        split < r + y
      }
    }

    def overlapsLeft(x: Double, y: Double, r: Double, level: Int): Boolean = {
      if (level % 2 == 0) {
        split > x - r
      } else {
        split > y - r
      }
    }

    def containedBy(x:Double, y:Double ,r:Double, level:Int, index:Int):Boolean = {
      false
    }
  }

  def apply(i: Int) = boxes(i)


  def size: Int = {
    values.size
  }

  def query_point_count(x: Double, y: Double, r: Double): Result = {
    val coll = new CountCollector(None)
    searchNodes(x, y, r,coll)
  }



  def intersects(x: Double, y: Double, r: Double): Boolean = {
    val width = xExtremes._2 - xExtremes._1
    val height = yExtremes._2 - yExtremes._1
    val rx = xExtremes._1 + width / 2.0
    val ry = yExtremes._1 + height / 2.0
    circleRectOverlap(x, y, r, rx, ry, width, height)
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

  def brute_search(x: Double, y: Double, r: Double): Int = {
    (for (ind <- values.indices) yield {
      val dx = x - values.sourceX(ind)
      val dy = y - values.sourceY(ind)
      dx * dx + dy * dy <= r * r
    }).count(e => e)
  }

  def searchNodes(x: Double, y: Double, r: Double, collector:RayCollector): Result = {
    val r2 = r * r
    var searching = 0
    var toSearch: List[Int] = 0 :: Nil
    var counter = 0.0
    var level = 0
    while (!toSearch.isEmpty) {
      searching = toSearch.head
      level = (math.log1p(searching) / OptTree.log2).toInt
      toSearch = toSearch.tail
      //Two cases: It overlaps the circle, or is completely enclosed by the circle
      //Case 1: completely encloses the circle
      if (false) counter += boxes(searching).size //This is the contained_by statement. ****************************************
      //Case 2: box overlaps the circle
      else {
        //Two cases. It is a leaf or a branch
        if (searching * 2 + 1 >= boxes.size) {
          //Case 1: It's a leaf
          counter += boxes(searching).search(x, y, r2, collector)
        } else {
          //Case 2: Need to go into its children. Check each individually, see if needs to be added.
          if (boxes(searching).overlapsLeft(x, y, r, level)) toSearch = (searching * 2 + 1) :: toSearch
          if (boxes(searching).overlapsRight(x, y, r, level)) toSearch = (searching * 2 + 2) :: toSearch
        }
      }
    }
    counter
  }

  def searchNodes(x1:Double,x2:Double,y1:Double,y2:Double,collector:RayCollector): Result = {
    var searching = 0
    var toSearch: List[Int] = 0 :: Nil
    var counter = 0.0
    var level = 0
    while (!toSearch.isEmpty) {
      searching = toSearch.head
      level = (math.log1p(searching) / OptTree.log2).toInt
      toSearch = toSearch.tail
      //Two cases: It overlaps the circle, or is completely enclosed by the circle
      //Case 1: completely encloses the circle
      if (false) counter += boxes(searching).size //This is the contained_by statement. ****************************************
      //Case 2: box overlaps the circle
      else {
        //Two cases. It is a leaf or a branch
        if (searching * 2 + 1 >= boxes.size) {
          //Case 1: It's a leaf
          counter += boxes(searching).search(x1, x2, y1, y2, collector)
        } else {
          //Case 2: Need to go into its children. Check each individually, see if needs to be added.
          if (boxes(searching).overlapsLeft(x1, x2, y1, y2, level)) toSearch = (searching * 2 + 1) :: toSearch
          if (boxes(searching).overlapsRight(x1, x2, y1, y2, level)) toSearch = (searching * 2 + 2) :: toSearch
        }
      }
    }
    counter
  }



  private def list_constructNodes(): Array[Node] = {
    val tmpBoxes: collection.mutable.ArrayBuffer[Node] = collection.mutable.ArrayBuffer[Node](new Node(0,size, 0.0))
    var level = 0
    var flag = true
    var index = 0
    while (flag) {
      if (tmpBoxes(index).size <= branchSize) flag = false
      else {
          for (i <- 0 until math.pow(2, level).toInt) {
            val n = tmpBoxes(index).size
            val k = n / 2
            if (level % 2 == 0) {
              //Horizontal split
              tmpBoxes(index).split = selectX(k, n, tmpBoxes(index).indI)
            } else {
              //Vertical split
              tmpBoxes(index).split = selectY(k, n, tmpBoxes(index).indI)
            }
            tmpBoxes.append(new Node(tmpBoxes(index).indI, tmpBoxes(index).indI + k, 0.0))
            tmpBoxes.append(new Node(tmpBoxes(index).indI + k, tmpBoxes(index).indJ, 0.0))
            index += 1
          }
        level += 1
      }
    }
    tmpBoxes.toArray
  }


  private def selectX(k: Int, n: Int, start: Int): Double = {
    if (n < 2) return 0
    var a = (0.0,0.0,0.0,0.0)
    var l = 0
    var ir = n - 1
    var j = 0
    var mid = 0
    var i = 0
    while (true) {
      if (ir <= l) {
        if (ir == l + 1 && values.sourceX(ir+start) < values.sourceX((l+start))) values.swap(l + start, ir + start)
        return values.sourceX((k + start))
      } else {
        mid = (l + ir) >> 1
        values.swap(mid + start, l + 1 + start)
        if (values.sourceX((l + start)) > values.sourceX((ir + start))) values.swap(l + start, ir + start)
        if (values.sourceX((l + 1 + start)) > values.sourceX((ir + start))) values.swap(l + 1 + start, ir + start)
        if (values.sourceX((l + start)) > values.sourceX((l + 1 + start))) values.swap(l + start, l + 1 + start)
        i = l + 1
        j = ir
        a = values.getTuple(l+1+start)
        var flag = true
        while (flag) {
          do { i += 1 } while (values.sourceX((i + start)) < a._3)
          do { j -= 1 } while (values.sourceX((j + start)) > a._3)
          if (j < i) flag = false
          else values.swap(i + start, j + start)
        }
        values.setTuple(l+1+start,values.getTuple(j+start))
        values.setTuple(j+start,a)
        if (j >= k) ir = j - 1
        if (j <= k) l = i
      }
    }
    -1
  }

  private def selectY(k: Int, n: Int, start: Int): Double = {
    if (n < 2) return 0
    var a = (0.0,0.0,0.0,0.0)
    var l = 0
    var ir = n - 1
    var j = 0
    var mid = 0
    var i = 0
    while (true) {
      if (ir <= l) {
        if (ir == l + 1 && values.sourceY((ir+start)) < values.sourceY((l+start))) values.swap(l + start, ir + start)
        return values.sourceY((k + start))
      } else {
        mid = (l + ir) >> 1
        values.swap(mid + start, l + 1 + start)
        if (values.sourceY((l + start)) > values.sourceY((ir + start))) values.swap(l + start, ir + start)
        if (values.sourceY((l + 1 + start)) > values.sourceY((ir + start))) values.swap(l + 1 + start, ir + start)
        if (values.sourceY((l + start)) > values.sourceY((l + 1 + start))) values.swap(l + start, l + 1 + start)
        i = l + 1
        j = ir
        a = values.getTuple(l+1+start)
        var flag = true
        while (flag) {
          do { i += 1 } while (values.sourceY((i + start)) < a._4)
          do { j -= 1 } while (values.sourceY((j + start)) > a._4)
          if (j < i) flag = false
          else values.swap(i + start, j + start)
        }
        values.setTuple(l+1+start,values.getTuple(j+start))
        values.setTuple(j+start,a)
        if (j >= k) ir = j - 1
        if (j <= k) l = i
      }
    }
    -1
  }
}

object OptTree {

  val binSize = 32
  val log2 = math.log(2)

  def apply[A <: RayBank](values:A):OptTree[A] = {
    new OptTree(values,binSize)
  }


}
