package spatialrdd

import org.apache.spark.SparkContext
import utility.{DoublePair, Index, QueryIterator, Result}

trait RDDGridProperty extends Serializable {
  def queryPoints(pts: Array[Array[DoublePair]], radius: Double, sc: SparkContext, verbose: Boolean = false): Array[Array[Result]]
//  def queryCaustics(pts: Array[Array[DoublePair]], radius: Double, sc: SparkContext, verbose: Boolean = false): Array[Array[Boolean]]

  def count: Long
  def queryPointsFromGen(gen: GridGenerator, radius: Double, sc: SparkContext, verbose: Boolean = false): Array[Array[Result]]
  
  def query_curve(pts:Array[DoublePair], radius:Double, sc:SparkContext):Array[Result]

  def destroy():Unit

  def cache():Unit
  
  def printSuccess:Unit
  
  def saveToFile(fname:String):Unit

  def searchBatch(iter:QueryIterator,radius:Double,sc:SparkContext):Array[Array[Result]]

  }
