package elliptical

import org.apache.spark.rdd.RDD
import org.apache.spark.broadcast.Broadcast

class RayTracer() extends Serializable {
  
  def atanh(x:Double):Double = {
    0.5*math.log((1.0+x)/(1.0-x))
  }

  def apply(pixels: RDD[Long], p: Broadcast[RayParameters]): RDD[(Double, Double)] = {
    val pi2 = math.Pi / 2.0
    //    val ret = pixels.glom().map { pixelIter =>
    pixels.mapPartitions(pixelIter => {
      pixelIter.map { long =>
        val x = long % p.value.width.toLong
        val y = long / p.value.width.toLong
        var retX = 0.0
        var retY = 0.0
        val incidentAngleX = (x.toDouble - p.value.width / 2.0) * p.value.dThetaX
        val incidentAngleY = (p.value.height / 2.0 - y.toDouble) * p.value.dThetaY

        // Point sources
        for (star <- p.value.stars) {
          val deltaRX = incidentAngleX - star.x
          val deltaRY = incidentAngleY - star.y
          val r = deltaRX * deltaRX + deltaRY * deltaRY
          if (r != 0.0) {
            retX += deltaRX * star.mass * p.value.pointConstant / r
            retY += deltaRY * star.mass * p.value.pointConstant / r
          }
        }

        //SIS constant. For elliptical models
        val deltaRX = incidentAngleX - p.value.centerX
        val deltaRY = incidentAngleY - p.value.centerY
        val r = math.sqrt(deltaRX * deltaRX + deltaRY * deltaRY)
        if (r != 0.0) {
        	val q1 = math.sqrt(1.0-p.value.ellipMag*p.value.ellipMag)
          val q = p.value.ellipMag
          val eex = deltaRX*math.sin(p.value.ellipAngle)+deltaRY*math.cos(p.value.ellipAngle)
          val eey = -deltaRX*math.cos(p.value.ellipAngle)+deltaRY*math.sin(p.value.ellipAngle)
          val ex = p.value.sisConstant*q*math.atan(q1*eex/math.sqrt(q*q*eex*eex+eey*eey))/q1
          val ey = p.value.sisConstant*q*atanh(q1*eey/math.sqrt(q*q*eex*eex+eey*eey))/q1
          retX += ex*math.sin(p.value.ellipAngle) - ey*math.cos(p.value.ellipAngle)
          retY += ex*math.cos(p.value.ellipAngle) + ey*math.sin(p.value.ellipAngle)
        }

        //Shear
        val phi = 2 * (pi2 - p.value.shearAngle) - math.atan2(deltaRY, deltaRX)
        retX += p.value.shearMag * r * math.cos(phi)
        retY += p.value.shearMag * r * math.sin(phi)
        (deltaRX - retX, deltaRY - retY)
      }
    }, true)
  }
}