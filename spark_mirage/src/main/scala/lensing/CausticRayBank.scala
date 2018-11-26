package lensing

import java.io.{BufferedWriter, FileWriter}

class CausticRayBank(lensPosition:Array[Double],sourcePosition:Array[Double],causticCharacter:Array[Double]) extends RayBank(lensPosition,sourcePosition) {
  def causticValue(ind:Int):Double = causticCharacter(ind)
  def setCausticValue(ind:Int,value:Double):Unit = causticCharacter(ind) = value
  def compressed:Array[Array[Double]] = {
    indices.map(ind => Array(sourceX(ind),sourceY(ind),causticValue(ind)))
  }
  def printTo(file:String):Unit = {
    val fw = new java.io.File(file)
    val bw = new BufferedWriter(new FileWriter(fw))
    val mapped = indices.take(100000).map(ind => "[" + sourceX(ind) + "," + sourceY(ind) + "," + causticValue(ind) + "]")
    bw.write("arr = [" + mapped.mkString(",") + "]")
    bw.close()
  }
  //For caustics, do I need to locate the critical curves to high resolution, then interpolate?
  //Would that be the most efficient way to find them?

}

object CausticRayBank {
  def apply(input: Array[Long], dx: Double, dy: Double, w: Long, h: Long): CausticRayBank = {    println("Allocating RayBank(s)")
    val number = input.size
    val lensPos = Array.fill(number*2)(0.0)
    val srcPos = Array.fill(number*2)(0.0)
    val caustics = Array.fill(number)(0.0)
    for (ind <- input.indices) {
      val long = input(ind)
      lensPos(ind*2) = ((long % w) - w/2).toDouble*dx
      lensPos(ind*2+1) = (h/2 - (long/w)).toDouble*dy
    }
    new CausticRayBank(lensPos,srcPos,caustics)
  }
}
