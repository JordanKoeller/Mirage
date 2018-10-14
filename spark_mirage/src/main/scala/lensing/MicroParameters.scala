package lensing

case class Star(x:Double,y:Double,mass:Double)

case class MicroParameters(stars:Array[Star],
    shear:Double,
    smooth:Double,
    dx:Double,
    dy:Double,
    width:Long,
    height:Long)