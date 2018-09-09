package utility

import org.apache.spark.util.AccumulatorV2
import utility._

class PixelAccumulator(w: Int, h: Int) extends AccumulatorV2[Long, Array[Array[Index]]] {
  private val arr: Array[Array[Index]] = Array.fill(w, h)(0)
  private var iszer: Boolean = true
  def add(v: Long): Unit = {
    val tmp = pixelConstructor(v)
    synchronized {
      arr(tmp.x)(tmp.y) += tmp.value
      iszer = false
    }
  }

  def isZero: Boolean = iszer

  def copy(): PixelAccumulator = {
    val cp = new PixelAccumulator(w,h)
    for (i <- 0 until w) {
      for (j <- 0 until h) {
        val tmp = pixelLongConstructor(i, j, arr(i)(j))
        cp.add(tmp)
      }
    }
    cp
  }

  def merge(other: AccumulatorV2[Long, Array[Array[Index]]]): Unit = {
    for (i <- 0 until w) {
      for (j <- 0 until h) {
        val tmp = pixelLongConstructor(i, j, other.value(i)(j))
        add(tmp)
      }
    }
  }

  def reset(): Unit = {
    synchronized {
      for (i <- 0 until w) {
        for (j <- 0 until h) {
          val tmp = pixelLongConstructor(i, j, -arr(i)(j))
          add(tmp)
        }
      }
      iszer = true
    }
  }

  def value: Array[Array[Index]] = arr

}
