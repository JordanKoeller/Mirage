package lensing


import org.apache.spark.broadcast.Broadcast
import org.apache.spark.rdd.RDD


class MicroRayTracer() extends Serializable {

  def lensPlane(pixels:RDD[Long], p:Broadcast[MicroParameters]):RDD[(Double,Double)] = {
    pixels.map { long =>
      val x1 = ((long % p.value.width) - p.value.width / 2).toDouble * p.value.dx
      val x2 = (p.value.height / 2 - (long / p.value.width)).toDouble * p.value.dy
      (x1, x2)
    }
  }
  def apply(pixels:RDD[Long], p:Broadcast[MicroParameters]):RDD[Array[RayBankVal.Ray]] = {
    val gminus = 1.0 - p.value.shear
    val gplus = 1.0 + p.value.shear
    val glommed = pixels.glom()
    val rays = glommed.map { rays =>
      RayBankVal.allocate(rays, p.value.dx, p.value.dy, p.value.width, p.value.height)
    }
    rays.map { arr =>
      arr.foreach { ray =>
        val x1 = ray.x
        val x2 = ray.y
        //      (x1,x2)
        var retX = gminus * x1 - p.value.smooth * x1
        var retY = x2 * gplus - p.value.smooth * x2
        var iter = 0
        var dx1 = 0.0
        var dx2 = 0.0
        var r = 0.0
        while (iter < p.value.stars.size) {
          dx1 = x1 - p.value.stars(iter).x
          dx2 = x2 - p.value.stars(iter).y
          r = dx1 * dx1 + dx2 * dx2
          retX -= p.value.stars(iter).mass * dx1 / r
          retY -= p.value.stars(iter).mass * dx2 / r
          iter += 1
        }
        ray.sourceX = retX
        ray.sourceY = retY
        // println(ray.sourceX + "," + ray.sourceY)
      }
      arr
    }
  }
}