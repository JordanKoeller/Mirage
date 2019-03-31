package lensing

trait RayCollector extends Serializable {
  def apply(rayBank: RayBank, index:Int):Double
  val paritySelection:Option[Int]
  def properParity(rayBank: RayBank, index:Int):Boolean = {
    if (paritySelection.isEmpty) true
    else paritySelection.get == rayBank.parity(index)
  }
}



class CountCollector(override val paritySelection: Option[Int]) extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = 1.0
}

class Moment1XCollector(override val paritySelection: Option[Int]) extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = rayBank.x(index) - rayBank.sourceX(index)
}

class Moment1YCollector(override val paritySelection: Option[Int]) extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = rayBank.y(index) - rayBank.sourceY(index)
}

class Moment2XCollector(override val paritySelection: Option[Int]) extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = {
    val dx = rayBank.x(index)-rayBank.sourceX(index)
    dx*dx
  }
}

class Moment2XYCollector(override val paritySelection: Option[Int]) extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = {
    (rayBank.x(index)-rayBank.sourceX(index))*(rayBank.y(index)-rayBank.sourceY(index))
  }
}

class Moment2YCollector(override val paritySelection: Option[Int]) extends RayCollector {
  override def apply(rayBank: RayBank, index: Int): Double = {
    val dy = rayBank.y(index)-rayBank.sourceY(index)
    dy*dy
  }
}


object RayCollector {

  private var index:Int = 0
  private var paritySelection:Option[Int] = None

  def setCollector(ind:Int):Unit = {
    index = ind
  }

  def setParity(value:Option[Int]):Unit = {
    paritySelection = value
  }
  implicit def collector:RayCollector = {
    println("Implicitly constructor collector with index " + index)
    index match {
      case 0 => new CountCollector(paritySelection)
      case 1 => new Moment1XCollector(paritySelection)
      case 2 => new Moment1YCollector(paritySelection)
      case 3 => new Moment2XCollector(paritySelection)
      case 4 => new Moment2XYCollector(paritySelection)
      case 5 => new Moment2YCollector(paritySelection)
      case _ => {
        println("No valid collector. Supplying the default.")
        new CountCollector(paritySelection)
      }
    }
  }
}
