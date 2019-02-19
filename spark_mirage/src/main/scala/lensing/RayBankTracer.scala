package lensing


import org.apache.spark.broadcast.Broadcast
import org.apache.spark.rdd.RDD

import scala.reflect.ClassTag


class RayBankTracer() extends Serializable {

  def lensPlane(pixels:RDD[Long], p:Broadcast[MicroParameters]):RDD[(Double,Double)] = {
    pixels.map { long =>
      val x1 = ((long % p.value.width) - p.value.width / 2).toDouble * p.value.dx
      val x2 = (p.value.height / 2 - (long / p.value.width)).toDouble * p.value.dy
      (x1, x2)
    }
  }
  def apply(pixels:RDD[RayBank], p:Broadcast[MicroParameters]):RDD[RayBank] = {
    val gminus = 1.0 - p.value.shear
    val gplus = 1.0 + p.value.shear
    pixels.map{ bank =>
      for (ind <- bank.indices) {
        val x1 = bank.x(ind)
        val x2 = bank.y(ind)
        var retX = gminus * x1 - p.value.smooth * x1
        var retY = x2 * gplus - p.value.smooth * x2
        var iter = 0
        var psi11 = gminus - p.value.smooth
        var psi12 = 0.0
        var psi21 = 0.0
        var psi22 = gplus - p.value.smooth
        var dx1 = 0.0
        var dx2 = 0.0
        var r = 0.0
        while (iter < p.value.stars.length) {
          dx1 = x1 - p.value.stars(iter).x
          dx2 = x2 - p.value.stars(iter).y
          r = dx1 * dx1 + dx2 * dx2
          retX -= p.value.stars(iter).mass * dx1 / r
          retY -= p.value.stars(iter).mass * dx2 / r

          val dx1s = dx1*dx1
          val dx2s = dx2*dx2
          val r2 = r*r

          psi11 -= p.value.stars(iter).mass*(dx2s-dx1s)/r2
          psi21 += 2.0*p.value.stars(iter).mass*dx1*dx2/r2
          psi12 += 2.0*p.value.stars(iter).mass*dx1*dx2/r2
          psi22 -= p.value.stars(iter).mass*(dx1s-dx2s)/r2

          iter += 1
        }
        val mag = math.random-0.5//psi11*psi22-psi12*psi21
        if (RayBankTracer.parity == 0 || (RayBankTracer.parity == -1 && mag < 0.0 ) || (RayBankTracer.parity == 1 && mag > 0.0)) {
          bank.setSourceX(ind,retX)
          bank.setSourceY(ind,retY)
        }
        else {
          bank.setSourceX(ind,Double.NaN)
          bank.setSourceY(ind,Double.NaN)
          bank.setX(ind,Double.NaN)
          bank.setY(ind,Double.NaN)
        }
      }
      new RayBank(bank.lensPosition.filterNot(_ == Double.NaN),bank.sourcePosition.filterNot(_ == Double.NaN))
    }
  }
}

object RayBankTracer {
  val parity = 1

}
