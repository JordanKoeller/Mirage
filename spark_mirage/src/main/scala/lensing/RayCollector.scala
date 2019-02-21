package lensing

trait RayCollector extends Serializable {
  def apply(rayBank: RayBank, index:Int):Double
}



class CountCollector extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = 1.0
}

class Moment1XCollector extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = rayBank.sourceX(index) - rayBank.x(index)
}

class Moment1YCollector extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = rayBank.sourceY(index) - rayBank.y(index)
}

class Moment2XCollector extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = {
    val dx = rayBank.sourceX(index) - rayBank.x(index)
    dx*dx
  }
}

class Moment2XYCollector extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = {
    (rayBank.sourceX(index) - rayBank.x(index))*(rayBank.sourceY(index) - rayBank.y(index))
  }
}

class Moment2YCollector extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = {
    val dy = rayBank.sourceY(index) - rayBank.y(index)
    dy*dy
  }
}


object RayCollector {

  private var index:Int = 0

  def setCollector(ind:Int):Unit = {
    index = ind
  }

  implicit def collector:RayCollector = {
    println("Implicitly constructor collector with index " + index)
    index match {
      case 0 => new CountCollector
      case 1 => new Moment1XCollector
      case 2 => new Moment1YCollector
      case 3 => new Moment2XCollector
      case 4 => new Moment2XYCollector
      case 5 => new Moment2YCollector
      case _ => {
        println("No valid collector. Supplying the default.")
        new CountCollector
      }
    }
  }
}
