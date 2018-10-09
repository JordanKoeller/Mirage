package utility

import java.io.{BufferedInputStream, BufferedOutputStream, FileInputStream, FileOutputStream}

import lensing.Star

object FileHandler {

  def saveStars(filename: String, data: Array[Star]): Unit = {
    val file = new BufferedOutputStream(new FileOutputStream(filename))
    val bytes = data.flatMap{s =>
      val bb = java.nio.ByteBuffer.allocate(8*3)
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
    val ret:Array[Star] = Array.fill(count)(null)
    val buff:Array[Byte] = Array.fill(count*24)(0)
    val numRead = file.read(buff)
    assert(numRead == count)
    val bb = java.nio.ByteBuffer.wrap(buff)
    ret.map{dummy =>
      Star(bb.getDouble(),bb.getDouble(),bb.getDouble())
    }
    file.close()
    ret
  }

  def saveMagnifications(filename: String, data: Array[Array[Int]]): Unit = {
    val file = new BufferedOutputStream(new FileOutputStream(filename))
    val bytes:Array[Byte] = data.flatMap{arr =>
      val bb = java.nio.ByteBuffer.allocate(arr.length*4)
      arr.foreach(e => bb.putInt(e))
      bb.array()
    }
    file.write(bytes)
    file.flush()
    file.close()
  }



  def getQueryPoints(filename:String,numRows:Int):Array[Array[(Double,Double)]] = {
    val file = new BufferedInputStream(new FileInputStream(filename))
    val ret = Array[Array[(Double,Double)]]()
    for (i <- 0 until numRows) {
      val num = Array.fill(4)(0.toByte)
      file.read(num)
      val length = java.nio.ByteBuffer.wrap(num).getInt
      val bb = Array.fill(length*16)(0.toByte)
      file.read(bb)
      val buff = java.nio.ByteBuffer.wrap(bb)
      val tmp = Array.fill(length)((buff.getDouble,buff.getDouble))
      ret(i) = tmp
    }
    file.close()
    ret
  }


}