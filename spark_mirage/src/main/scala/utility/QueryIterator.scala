package utility

trait QueryIterator {
  def nextBatch():LocalQueryIterator
  def hasNext:Boolean
  def takeInResult(res:Array[Int])
  def collect:Array[Array[Int]]
}

trait LocalQueryIterator extends Serializable {
  def size:Int
  def apply(i:Int):DoublePair

}

object QueryIterator {
  private[utility] val chunkSize = 100000
}
