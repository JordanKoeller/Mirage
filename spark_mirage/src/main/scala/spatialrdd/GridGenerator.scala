package spatialrdd

case class QueryInfo(px: Int, py: Int, x: Double, y: Double)
case class BucketInfo(px:Int, py:Int, x1: Double, x2:Double, y1:Double, y2:Double)

class GridGenerator(x0: Double, y0: Double, x1: Double, y1: Double,val xDim: Int,val yDim: Int) extends Serializable {
  private val xStep = (x1 - x0) / (xDim.toDouble)
  private val yStep = (y1 - y0) / (yDim.toDouble)
  private val generator = (x: Double, y: Double) => (x0 + xStep * x, y0 + yStep * y)

  def iterator:Iterator[QueryInfo] = new Iterator[QueryInfo] {
    private var currX: Int = 0
    private var currY: Int = 0

    def hasNext: Boolean = {
      currX < xDim && currY < yDim
    }


    def next: QueryInfo = {
      val bucket = generator(currX.toDouble, currY.toDouble)
      val ret = QueryInfo(currX, currY, bucket._1, bucket._2)
      if (currX + 1 == xDim) {
        currX = 0
        currY += 1
      }
      else currX += 1
      ret
    }
  }

  def gridIterator:Iterator[BucketInfo] = new Iterator[BucketInfo] {
    private var currX: Int = 0
    private var currY: Int = 0

    def hasNext: Boolean = {
      currX < xDim && currY < yDim
    }


    def next: BucketInfo = {
      val bucket = generator(currX.toDouble, currY.toDouble)
      val ret = BucketInfo(currX, currY, bucket._1, bucket._1 + xStep, bucket._2, bucket._2+yStep)
      if (currX + 1 == xDim) {
        currX = 0
        currY += 1
      }
      else currX += 1
      ret
    }
  }
}