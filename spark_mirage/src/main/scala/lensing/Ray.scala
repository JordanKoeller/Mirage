package lensing

object RayBankVal {

  //private var rays:Array[Double] = Array()
  var lensPosition:Array[Double] = Array()
  var sourcePosition:Array[Double] = Array()
  //Position of the ray after mapping to the source plane

  def size:Int = lensPosition.size/2

  def allocate(input:Array[Long],dx:Double,dy:Double,w:Long,h:Long):Array[Ray] = {
    val number = input.size
    val ret = input.indices.toArray.map(l => new Ray(l))
    println("Allocating")
    lensPosition = Array.fill(number*2)(0.0)
    sourcePosition = Array.fill(number*2)(0.0)
    for (ind <- input.indices) {
      val ray = ret(ind)
      val long = input(ind)
      ray.x = ((long % w) - w/2).toDouble*dx
      ray.y = (h/2 - (long/w)).toDouble*dy
    }
    ret
  }

  def apply(rays:Array[Array[Byte]]):Array[Ray] = {
    lensPosition = Array.fill(rays.size*2)(0.0)
    sourcePosition = Array.fill(rays.size*2)(0.0)
    val retInds = rays.indices.toArray
    for (ind <- retInds) {
      val bb = java.nio.ByteBuffer.wrap(rays(ind)).asDoubleBuffer()
      lensPosition(ind*2) == bb.get(0)
      lensPosition(ind*2+1) == bb.get(1)
      sourcePosition(ind*2) == bb.get(2)
      sourcePosition(ind*2+1) == bb.get(3)
    }
    retInds.map(e => new Ray(e))
  }

  class Ray(val index:Int) extends AnyVal {
    def x:Double = lensPosition(index*2)
    def y:Double = lensPosition(index*2+1)
    def sourceX:Double = sourcePosition(index*2)
    def sourceY:Double = sourcePosition(index*2+1)
    def x_=(value:Double):Unit = lensPosition(index*2) = value
    def y_=(value:Double):Unit = lensPosition(index*2+1) = value
    def sourceX_=(value:Double):Unit = sourcePosition(index*2) = value
    def sourceY_=(value:Double):Unit = sourcePosition(index*2+1) = value
    def asLong:Int = index
    def packed:Array[Byte] = {
      val bb = java.nio.ByteBuffer.allocate(8*4)
      bb.putDouble(x)
      bb.putDouble(y)
      bb.putDouble(sourceX)
      bb.putDouble(sourceY)
      bb.array()
    }
  }


}