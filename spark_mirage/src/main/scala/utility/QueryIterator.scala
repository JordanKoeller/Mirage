package utility

trait QueryIterator extends Serializable {
  def nextBatch():LocalQueryIterator
  def hasNext:Boolean
  def takeInResult(res:Array[Result])
  protected val resultDump:Array[Array[Result]]
  def collect:Array[Array[Result]] = resultDump


}

trait LocalQueryIterator extends Serializable {
  def size:Int
  def apply(i:Int):DoublePair

}

object QueryIterator {
  private[utility] val chunkSize = 1000000
}
