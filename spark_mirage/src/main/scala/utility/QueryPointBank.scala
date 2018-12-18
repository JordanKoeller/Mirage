package utility


class QueryPointBank(contig:Array[Double],shapes:Array[Int]) extends Serializable {
  def iterator:Iterator[QueryPointBank.QueryPoint] = new Iterator[QueryPointBank.QueryPoint] {
    private var i = 0
    private var j = 0
    private var c = 0
    override def next(): QueryPointBank.QueryPoint = {
      val x = contig(c)
      val y = contig(c+1)
      val ret = QueryPointBank.QueryPoint(i,j,x,y)
      c += 2
      j += 1
      if (j == shapes(i)) {
        i += 1
        j = 0
      }
      ret
    }
    override def hasNext():Boolean = {
      c < contig.size
    }
  }

}

object QueryPointBank {

  case class QueryPoint(i:Int,j:Int,x:Double,y:Double)

  def apply(qpts:Array[Array[(Double,Double)]]):QueryPointBank = {
    val shapes = qpts.map(_.length)
    val contiguous:Array[Double] = Array.fill(shapes.sum*2)(0.0)
    var c = 0
    for (i <- 0 until qpts.size) {
      for (j <- 0 until qpts(i).size) {
        contiguous(c) = qpts(i)(j)._1
        contiguous(c+1) = qpts(i)(j)._2
        c += 2
      }
    }
    new QueryPointBank(contig = contiguous, shapes = shapes)
  }
}
