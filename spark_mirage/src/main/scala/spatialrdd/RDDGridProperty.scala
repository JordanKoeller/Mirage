package spatialrdd

import org.apache.spark.SparkContext

import utility.DoublePair
import utility.Index
trait RDDGridProperty extends Serializable {
  def queryPoints(pts: Array[Array[DoublePair]], radius: Double, sc: SparkContext, verbose: Boolean = false): Array[Array[Index]]

  def count: Long
  def queryPointsFromGen(gen: GridGenerator, radius: Double, sc: SparkContext, verbose: Boolean = false): Array[Array[Int]]
  
  def query_curve(pts:Array[DoublePair], radius:Double, sc:SparkContext):Array[Int]

  def destroy():Unit
  
  def printSuccess:Unit
  
  def saveToFile(fname:String):Unit
}
