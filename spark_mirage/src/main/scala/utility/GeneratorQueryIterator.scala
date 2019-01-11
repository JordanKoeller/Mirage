package utility

case class QueryInfo(px: Int, py: Int, x: Double, y: Double)

class GridQueryGenerator(x0: Double, y0: Double, x1: Double, y1: Double, val xDim: Int, val yDim: Int) extends QueryIterator {
  private val xStep = (x1 - x0) / (xDim.toDouble)
  private val yStep = (y1 - y0) / (yDim.toDouble)
  private val generator = (x: Double, y: Double) => (x0 + xStep * x, y0 + yStep * y)
  override val resultDump = Array.fill(yDim,xDim)(0)

  private val numRow = QueryIterator.chunkSize / xDim
  private var currRow = 0

  override def nextBatch(): LocalQueryIterator = {
    val ret = new GridLocalIterator(generator, xDim, currRow, math.min(currRow + numRow, yDim))
    currRow += numRow
    ret
  }

  override def hasNext: Boolean = currRow < yDim

  override def takeInResult(res: Array[Index]): Unit = {
    var counter = 0
    for (i <- currRow - numRow until currRow) {
      resultDump(i) = res.slice(counter,xDim+counter)
      counter += xDim
    }
  }

}


class GridLocalIterator(gen:(Double,Double) => DoublePair, w:Int, hs:Int, hf:Int) extends LocalQueryIterator {

  def size:Int = (hf - hs)*w

  def apply(i:Int):DoublePair =  {
    val x = i % w
    val y = i / w + hs
    gen(x.toDouble,y.toDouble)
  }

}
