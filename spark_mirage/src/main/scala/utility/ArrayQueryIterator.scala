package utility

import scala.collection.mutable.ListBuffer

class ArrayQueryIterator(qpts:Array[Array[DoublePair]]) extends QueryIterator {

  var dispatchedRows:ListBuffer[Int] = ListBuffer[Int]()
  var lastSent = 0
  val resultDump = Array.fill(qpts.size)(Array[Int]())

  def nextBatch():ArrayLocalQueryIterator = {
    var counter = 0
    dispatchedRows = ListBuffer[Int]()
    while (lastSent < qpts.size && counter < QueryIterator.chunkSize) {
      counter += qpts(lastSent).size
      dispatchedRows += lastSent
      lastSent += 1
    }
    new ArrayLocalQueryIterator(qpts.slice(dispatchedRows.head,dispatchedRows.last).flatten)
  }

  def hasNext:Boolean = lastSent < qpts.size

  def takeInResult(res:Array[Int]) = {
    var counter = 0
    for (elem <- dispatchedRows) {
      resultDump(elem) = res.slice(counter,qpts(elem).size+counter)
      counter += resultDump(elem).size
    }
  }

  def collect:Array[Array[Int]] = resultDump

}

class ArrayLocalQueryIterator(values:Array[DoublePair]) extends LocalQueryIterator {
  def size:Int = values.size
  def apply(i:Int):DoublePair = values(i)
}
