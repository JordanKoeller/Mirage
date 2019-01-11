package utility

trait QueryIterator {
  def nextBatch():LocalQueryIterator
  def hasNext:Boolean
  def takeInResult(res:Array[Int])
  protected val resultDump:Array[Array[Int]]
  def collect:Array[Array[Int]] = resultDump


}

trait LocalQueryIterator extends Serializable {
  def size:Int
  def apply(i:Int):DoublePair

}

object QueryIterator {
  private[utility] val chunkSize = 100000
}
