package spatialrdd

class kDTree(xx: Array[Double], yy: Array[Double], branchSize: Int, parallelDepth: Int = -1) extends SpatialData {

  private val xExtremes = minMax(xx)
  private val yExtremes = minMax(yy)
  private val boxes = list_constructNodes()
  println("Have " + boxes.length + " boxes")

  private def minMax(vals: Array[Double]): (Double, Double) = {
    vals.foldLeft((Double.MaxValue, Double.MinValue)) { (best, elem) =>
      (math.min(best._1, elem), math.max(best._2, elem))
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
        dx = xx(i) - x
        dy = yy(i) - y
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
  }

  def apply(i: Int) = boxes(i)

  //  private val nodeDescs: Array[Double] = Array.fill(xx.length * 4)(0.0) //Array where groups of 4 are bottom left, top right of nodes

  def size: Int = {
    xx.size
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
    (for (ind <- xx.indices) yield {
      val dx = x - xx(ind)
      val dy = y - yy(ind)
      dx * dx + dy * dy <= r * r
    }).filter(_ == true).size
  }

  def searchNodes(x: Double, y: Double, r: Double): Int = {
    val r2 = r * r
    var searching = 0
    var toSearch: List[Int] = 0 :: Nil
    var counter = 0
    var level = 0
    while (!toSearch.isEmpty) {
      searching = toSearch.head
      level = (math.log1p(searching) / kDTree.log2).toInt
      toSearch = toSearch.tail
      //Two cases: It overlaps the circle, or is completely enclosed by the circle
      //Case 1: completely encloses the circle
      if (boxes(searching).containedBy(x, y, r2)) counter += boxes(searching).size
      //Case 2: box overlaps the circle
      else {
        //Two cases. It is a leaf or a branch
        if (searching * 2 + 1 >= boxes.size) {
          //Case 1: It's a leaf
          counter += boxes(searching).search(x, y, r2)
        } else {
          //Case 2: Need to go into its children. Check each individually, see if needs to be added.
          if (boxes(searching).overlapsLeft(x, y, r, level)) toSearch = (searching * 2 + 1) :: toSearch
          if (boxes(searching).overlapsRight(x, y, r, level)) toSearch = (searching * 2 + 2) :: toSearch
        }
      }
    }
    counter
  }

  def printt: Unit = {
    for (box <- boxes) box.print
  }

  private def list_constructNodes(): Array[Node] = {
    val tmpBoxes: collection.mutable.ArrayBuffer[Node] = collection.mutable.ArrayBuffer[Node](new Node(0, xx.size, 0.0))
    var parent = 0
    var left = 0
    var level = 0
    var flag = true
    var index = 0
    while (flag) {
      if (tmpBoxes(index).size <= branchSize) flag = false
      else {
        if (level >= parallelDepth) {
          for (i <- 0 until math.pow(2, level).toInt) {
            val n = tmpBoxes(index).size
            val k = (n) / 2
            if (level % 2 == 0) {
              //Horizontal split
              tmpBoxes(index).split = selectPairs(k, n, xx, yy, tmpBoxes(index).indI)
            } else {
              //Vertical split
              tmpBoxes(index).split = selectPairs(k, n, yy, xx, tmpBoxes(index).indI)
            }
            tmpBoxes.append(new Node(tmpBoxes(index).indI, tmpBoxes(index).indI + k, 0.0))
            tmpBoxes.append(new Node(tmpBoxes(index).indI + k, tmpBoxes(index).indJ, 0.0))
            index += 1
          }
        } else {
          println("Parallel iteration")
          val pariter = (0 until math.pow(2, level).toInt).par
          val temps = pariter.flatMap { i =>
            val inddex = index + i
            val n = tmpBoxes(inddex).size
            val k = (n) / 2
            if (level % 2 == 0) {
              //Horizontal split
              tmpBoxes(inddex).split = selectPairs(k, n, xx, yy, tmpBoxes(inddex).indI)
            } else {
              //Vertical split
              tmpBoxes(inddex).split = selectPairs(k, n, yy, xx, tmpBoxes(inddex).indI)
            }
            Seq(
              new Node(tmpBoxes(inddex).indI, tmpBoxes(inddex).indI + k, 0.0),
              new Node(tmpBoxes(inddex).indI + k, tmpBoxes(inddex).indJ, 0.0))
          }
          tmpBoxes.append(temps.toArray: _*)
          index += pariter.size
        }

        level += 1
      }

    }
    tmpBoxes.toArray

  }

  private def selectPairs(k: Int, n: Int, arr: Array[Double], other: Array[Double], start: Int): Double = {
    if (n < 2) return 0
    var a = 0.0
    var b = 0.0
    var l = 0
    var ir = n - 1
    var j = 0
    var mid = 0
    var i = 0
    while (true) {
      if (ir <= l) {
        if (ir == l + 1 && arr(ir + start) < arr(l + start)) swap2(l + start, ir + start, arr, other)
        return arr(k + start)
      } else {
        mid = (l + ir) >> 1
        swap2(mid + start, l + 1 + start, arr, other)
        if (arr(l + start) > arr(ir + start)) swap2(l + start, ir + start, arr, other)
        if (arr(l + 1 + start) > arr(ir + start)) swap2(l + 1 + start, ir + start, arr, other)
        if (arr(l + start) > arr(l + 1 + start)) swap2(l + start, l + 1 + start, arr, other)
        i = l + 1
        j = ir
        a = arr(l + 1 + start)
        b = other(l + 1 + start)
        var flag = true
        while (flag) {
          do { i += 1 } while (arr(i + start) < a)
          do { j -= 1 } while (arr(j + start) > a)
          if (j < i) flag = false
          else swap2(i + start, j + start, arr, other)
        }
        arr(l + 1 + start) = arr(j + start)
        other(l + 1 + start) = other(j + start)
        arr(j + start) = a
        other(j + start) = b
        if (j >= k) ir = j - 1
        if (j <= k) l = i
      }
    }
    -1
  }

  private def swap2(i: Int, j: Int, a1: Array[Double], a2: Array[Double]): Unit = {
    val tmp = a1(i)
    val tmp2 = a2(i)
    a1(i) = a1(j)
    a2(i) = a2(j)
    a1(j) = tmp
    a2(j) = tmp2
  }

}

object kDTree {

  val binSize = 64
  val parallelDepth = -1
  val log2 = math.log(2)

  def apply(values: IndexedSeq[(Double, Double)]): kDTree = {
    val xcoords = values.map(_._1).toArray
    val ycoords = values.map(_._2).toArray
    println("Constructing the tree now")
    new kDTree(xcoords, ycoords, binSize, parallelDepth)
  }

//  def checkKids(prnt: Int, level: Int, tree: kDTree): Boolean = {
//    val split = tree(prnt).split
//    val kid1 = tree(prnt * 2 + 1)
//    val kid2 = tree(prnt * 2 + 2)
//    var c = tree.xx
//    if (level % 2 != 0) c = tree.yy
//    for (i <- kid1.indI until kid1.indJ) if (c(i) > split) {
//      println("Error " + i)
//      return false
//    }
//    for (i <- kid2.indI until kid2.indJ) if (c(i) < split) {
//      println("Error " + i)
//      return false
//    }
//    println("Worked")
//    return true
//  }

}