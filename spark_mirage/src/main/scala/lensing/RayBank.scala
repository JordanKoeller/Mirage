package lensing

import java.util

import utility.Result

class RayBank(private var lensPosition:Array[Double],private var sourcePosition:Array[Double]) extends Serializable {
  private val parities = new util.BitSet(lensPosition.size)

  def setParity(ind:Int,value:Int): Unit = {
    val lookup = ind*2
    if (value == 1) {
      parities.set(lookup,lookup+2,true)
    }
    else if (value == -1) {
      parities.set(lookup,lookup+2,false)
    }
    else {
      parities.set(lookup,true)
      parities.set(lookup+1,false)
    }
  }

  def parity(ind:Int):Int = {
    val lookup = ind*2
    if (parities.get(lookup) && parities.get(lookup+1)) 1
    else if (!parities.get(lookup) && !parities.get(lookup+1)) -1
    else 0
  }

  def size:Int = lensPosition.length/2

  def x(ind:Int):Double = lensPosition(ind*2)
  def y(ind:Int):Double = lensPosition(ind*2+1)
  def sourceX(ind:Int):Double = sourcePosition(ind*2)
  def sourceY(ind:Int):Double = sourcePosition(ind*2+1)

  def setX(ind:Int,value:Double):Unit = lensPosition(ind*2) = value
  def setY(ind:Int,value:Double):Unit = lensPosition(ind*2+1) = value
  def setSourceX(ind:Int,value:Double):Unit = sourcePosition(ind*2) = value
  def setSourceY(ind:Int,value:Double):Unit = sourcePosition(ind*2+1) = value

  def indices:Array[Int] = Array.range(0,size)
  def getTuple(i:Int):(Double,Double,Double,Double,Int) = {
    (x(i),y(i),sourceX(i),sourceY(i),parity(i))
  }
  def setTuple(i:Int,data:(Double,Double,Double,Double,Int)) = {
    setX(i,data._1)
    setY(i,data._2)
    setSourceX(i,data._3)
    setSourceY(i,data._4)
    setParity(i,data._5)
  }

  def destroy(ind:Int):Unit = {
    lensPosition(ind*2) = Double.MinValue
    lensPosition(ind*2+1) = Double.MinValue
    sourcePosition(ind*2) = Double.MinValue
    sourcePosition(ind*2+1) = Double.MinValue
  }

  def trim():Unit = {
    lensPosition = lensPosition.filterNot(_ == Double.NaN)
    sourcePosition = sourcePosition.filterNot(_ == Double.NaN)
  }

  def aggregate(ind:Int):Result = {
    val dx = sourceX(ind) - x(ind)
    val dy = sourceY(ind) - y(ind)
    val lookup = 1
    val arr = Array(1.0,dx,dy,dx*dx,dx*dy,dy*dy)
    arr(lookup)
//    1.0 // zeroth order
//    dx    //1st order 1
//    dy    //1st order 2
//    dx*dx //2nd order 1
//    dx*dy //2nd order 2
    // dy*dy //2nd order 3
  }

  def swap(i:Int,j:Int):Unit = {
    val tmp = getTuple(i)
    setX(i,x(j))
    setY(i,y(j))
    setSourceX(i,sourceX(j))
    setSourceY(i,sourceY(j))
    setParity(i,parity(j))
    setTuple(j,tmp)
  }
  override def toString():String = {
    (for (i <- 0 until size) yield "[%.2f, %.2f]".format(x(i),y(i))).mkString(",")
  }
}


object RayBank {
  def apply(input:Array[Long],dx:Double,dy:Double,w:Long,h:Long): RayBank = {
    val number = input.size
    val lensPos = Array.fill(number*2)(0.0)
    val srcPos = Array.fill(number*2)(0.0)
    for (ind <- input.indices) {
      val long = input(ind)
      lensPos(ind*2+1) = ((long / w) - h/2).toDouble*dy
      lensPos(ind*2) = ((long % w) - w/2).toDouble*dx
    }
    new RayBank(lensPos,srcPos)
  }
}
