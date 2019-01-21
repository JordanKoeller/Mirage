package utility

case class QueryInfo(px: Int, py: Int, x: Double, y: Double)

class GridQueryGenerator(x0: Double, y0: Double, x1: Double, y1: Double, val xDim: Int, val yDim: Int) extends QueryIterator {
  private val xStep = (x1 - x0) / (xDim.toDouble)
  private val yStep = (y1 - y0) / (yDim.toDouble)
  override val resultDump = Array.fill(yDim,xDim)(0)

  private val rowPerBatch = QueryIterator.chunkSize / xDim
  private var startRow = 0
  private var endRow = 0

  override def nextBatch(): LocalQueryIterator = {
    startRow = endRow
    endRow = math.min(startRow+rowPerBatch,yDim)
    val ret = new GridLocalIterator(xStep,yStep,x0,y0, xDim, startRow, endRow)
    ret
  }

  override def hasNext: Boolean = currRow < yDim

  override def takeInResult(res: Array[Index]): Unit = {
    var counter = 0
    for (i <- startRow until endRow) {
      resultDump(i) = res.slice(counter,xDim+counter)
      counter += xDim
    }
  }

}


class GridLocalIterator(xStep:Double ,yStep:Double, x0:Double, y0:Double, w:Int, hs:Int, hf:Int) extends LocalQueryIterator {
  private val gen = (x: Double, y: Double) => (x0 + xStep * x, y0 + yStep * y)

  def size:Int = (hf - hs)*w

  def apply(i:Int):DoublePair =  {
    val x = i % w
    val y = i / w + hs
    gen(x.toDouble,y.toDouble)
  }

}
