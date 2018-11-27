package spatialrdd

import lensing.CausticRayBank


class CausticTree(values:CausticRayBank, branchSize: Int) extends SpatialData {

  private val xExtremes = minMax(values,(a,b) => a.sourceX(b))
  private val yExtremes = minMax(values,(a,b) => a.sourceY(b))
  private val boxes = list_constructNodes()

  private def minMax(vals: CausticRayBank,func:(CausticRayBank,Int) => Double): (Double, Double) = {
    vals.indices.foldLeft((Double.MaxValue, Double.MinValue)) { (best, ind) =>
      (math.min(best._1, func(vals,ind)), math.max(best._2, func(vals,ind)))
    }
  }

  class Node(val indI: Int, val indJ: Int, var split: Double) {
    def size: Int = indJ - indI

    override def toString() = "Node"

    def print = {
      println("Node with " + size + " elements from " + indI + " to " + indJ)
    }

    def search(x: Double, y: Double, r2: Double): Int = {
      var counter = 0
      var dx = 0.0
      var dy = 0.0
      for (i <- indI until indJ) {
        dx = values.sourceX(i) - x
        dy = values.sourceY(i) - y
        if (dx * dx + dy * dy <= r2) {
          counter += 1
        }
      }
      counter
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

    def containedBy(x: Double, y: Double, r: Double): Boolean = {
      false
    }

    def searchCaustic(x:Double, y:Double, r2:Double):Boolean = {
      //To Find a caustic, I use the fact that magnification is continuous and differentiable.
      //What this means is that if I find a point with positive magnification and another with
      //negative magnification, I must have a zero in between where a caustic is present.
      //Once two such points are found, I can short-circuit out of the loop and return.
      var dx = 0.0
      var dy = 0.0
      var posMag = false
      var negMag = false
      for (i <- indI until indJ) {
        dx = values.sourceX(i) - x
        dy = values.sourceY(i) - y
        //Find a point in the query.
        if (dx*dx + dy*dy <= r2) {
          //check if it's positive
          if (values.causticValue(i) > 0.0) {
            posMag = true
          }
          else {
            negMag = true
          }
          if (posMag && negMag) {
            return true
          }
        }
      }
      return false
    }

  }

  def apply(i: Int) = boxes(i)


  def size: Int = {
    values.size
  }

  def query_point_count(x: Double, y: Double, r: Double): Int = {
    searchNodes(x, y, r)
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

  def searchNodes(x: Double, y: Double, r: Double): Int = {
    val r2 = r * r
    var searching = 0
    var toSearch: List[Int] = 0 :: Nil
    var counter = 0
    var level = 0
    while (!toSearch.isEmpty) {
      searching = toSearch.head
      level = (math.log1p(searching) / OptTree.log2).toInt
      toSearch = toSearch.tail
      //Two cases: It overlaps the circle, or is completely enclosed by the circle
      //Case 1: completely encloses the circle
      if (boxes(searching).containedBy(x, y, r2)) counter += boxes(searching).size
      //Case 2: box overlaps the circle
      else {
        //Two cases. It is a leaf or a branch
        if (searching * 2 + 1 >= boxes.size) {
          //Case 1: It's a leaf
          boxes(searching).search(x, y, r2)
        } else {
          //Case 2: Need to go into its children. Check each individually, see if needs to be added.
          if (boxes(searching).overlapsLeft(x, y, r, level)) toSearch = (searching * 2 + 1) :: toSearch
          if (boxes(searching).overlapsRight(x, y, r, level)) toSearch = (searching * 2 + 2) :: toSearch
        }
      }
    }
    counter
  }

  def searchCaustics(x: Double, y: Double, r: Double): Boolean = {
    val r2 = r * r
    var searching = 0
    var toSearch: List[Int] = 0 :: Nil
    var counter = 0
    var level = 0
    while (!toSearch.isEmpty) {
      searching = toSearch.head
      level = (math.log1p(searching) / OptTree.log2).toInt
      toSearch = toSearch.tail
      //Two cases: It overlaps the circle, or is completely enclosed by the circle
      //Case 1: completely encloses the circle
      if (boxes(searching).containedBy(x, y, r2)) counter += boxes(searching).size
      //Case 2: box overlaps the circle
      else {
        //Two cases. It is a leaf or a branch
        if (searching * 2 + 1 >= boxes.size) {
          //Case 1: It's a leaf
          if (boxes(searching).searchCaustic(x, y, r2)) {
            return true
          }
        } else {
          //Case 2: Need to go into its children. Check each individually, see if needs to be added.
          if (boxes(searching).overlapsLeft(x, y, r, level)) toSearch = (searching * 2 + 1) :: toSearch
          if (boxes(searching).overlapsRight(x, y, r, level)) toSearch = (searching * 2 + 2) :: toSearch
        }
      }
    }
    false
  }

  def printt: Unit = {
    for (box <- boxes) box.print
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
    //    var b = 0.0
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
        //        b = other(l + 1 + start)
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

object CausticTree {

  val binSize = 64
  val log2 = math.log(2)

  def apply(values:CausticRayBank):CausticTree = {
    new CausticTree(values,binSize)
  }

//  case object Fold
//  case object Cusp

}
