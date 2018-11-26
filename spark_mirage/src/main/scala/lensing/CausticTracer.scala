package lensing

import org.apache.spark.broadcast.Broadcast
import org.apache.spark.rdd.RDD

class CausticTracer extends Serializable {

  /*
  gam = macro_shear + 0j
    x1 = locations[j,0]
  x2 = locations[j,1]
  gamBar = macro_shear + 0j
    gamBarPrime = 0 + 0j
    gamPrime = 0 + 0j
    gamPrimeUBar = 0 + 0j
    gamPrimeBarUBar = 0 + 0j
  for i in range(0,num_stars):
    x1i = stars[i,0]
    x2i = stars[i,1]
    u = (x1-x1i) + (x2 - x2i)*I
    ubar = (x1-x1i) - (x2 - x2i)*I
    mi = stars[i,2]
    r = u*ubar
    gam += mi*u*u/r/r
  */

  def apply(pixels:RDD[CausticRayBank],p:Broadcast[MicroParameters]):RDD[CausticRayBank] = {
    pixels.map{bank =>
      for (ind <- bank.indices) {
        var x1 = 0.0
        var x2 = 0.0
        var gam1 = p.value.shear
        var gam2 = 0.0
        var r2 = 0.0
        for (star <- p.value.stars) {
          x1 = bank.x(ind) - star.x
          x2 = bank.y(ind) - star.y
          r2 = x1*x1+ x2*x2
          gam1 -= star.mass*(x1*x1 - x2*x2)/r2/r2
          gam2 -= 2.0*star.mass*x1*x2/r2/r2
        }
        bank.setCausticValue(ind,((1.0-p.value.smooth)*(1.0-p.value.smooth)-(gam1*gam1+gam2*gam2)))

      }
      bank
    }
  }
}
