package utility

import java.io.{BufferedInputStream, BufferedOutputStream, FileInputStream, FileOutputStream}
import java.nio.ByteOrder.nativeOrder
import lensing.Star

object FileHandler {

  def saveStars(filename: String, data: Array[Star]): Unit = {
    val file = new BufferedOutputStream(new FileOutputStream(filename))
    val bytes = data.flatMap{s =>
      val bb = java.nio.ByteBuffer.allocate(8*3)
      bb.order(nativeOrder())
      bb.putDouble(s.x)
      bb.putDouble(s.y)
      bb.putDouble(s.mass)
      bb.array()
    }
    file.write(bytes)
    file.flush()
    file.close()
  }

  def getStars(filename: String,count:Int):Array[Star] = {
    val file = new BufferedInputStream(new FileInputStream(filename))
    val buff:Array[Byte] = Array.fill(count*24)(0)
    val numRead = file.read(buff)
    val bb = java.nio.ByteBuffer.wrap(buff)
    bb.order(nativeOrder())
    Array.fill(count)(Star(bb.getDouble,bb.getDouble,bb.getDouble))
  }

  def saveMagnifications(filename: String, data: Array[Array[Int]]): Unit = {
    val file = new BufferedOutputStream(new FileOutputStream(filename))
    val bytes:Array[Byte] = data.flatMap{arr =>
      val bb = java.nio.ByteBuffer.allocate(arr.length*4)
      bb.order(nativeOrder())
      arr.foreach(e => bb.putInt(e))
      bb.array()
    }
    file.write(bytes)
    file.flush()
    file.close()
  }

  def saveDoubles(filename:String,data:Array[Array[Double]]): Unit = {

    val file = new BufferedOutputStream(new FileOutputStream(filename))
    val bytes:Array[Byte] = data.flatMap{arr =>
      val bb = java.nio.ByteBuffer.allocate(arr.length*8)
      bb.order(nativeOrder())
      arr.foreach(e => bb.putDouble(e))
      bb.array()
    }
    file.write(bytes)
    file.flush()
    file.close()
  }



  def getQueryPoints(filename:String,numRows:Int):Array[Array[(Double,Double)]] = {
    val file = new BufferedInputStream(new FileInputStream(filename))
    val sizes = Array.fill(numRows*4)(0.toByte)
    file.read(sizes)
    val sizeIter = java.nio.ByteBuffer.wrap(sizes)
    sizeIter.order(nativeOrder())
    val ret:Array[Array[(Double,Double)]] = Array.fill(numRows)(null)
    for (i <- 0 until numRows) {
      val length = sizeIter.getInt()
      val bb = Array.fill(length*16)(0.toByte)
      file.read(bb)
      val buff = java.nio.ByteBuffer.wrap(bb)
    buff.order(nativeOrder())
      val tmp = Array.fill(length)((buff.getDouble,buff.getDouble))
      ret(i) = tmp
    }
    file.close()
    ret
  }


}