package main


import lensing._
import org.apache.spark.api.java.JavaRDD
import spatialrdd._
import utility.FileHandler

object Main extends App {

  private var rddGrid: RDDGridProperty = null

  def createRDDGrid(
                     starsfile:String,
                     numStars:Int,
                     shear:Double,
                     smooth:Double,
                     dx:Double,
                     dy:Double,
                     width:Long,
                     height:Long,
                     jrdd:JavaRDD[Int],
                     numPartitions:Int):Unit = {
    if (rddGrid != null) rddGrid.destroy()
    val sc = jrdd.context
    sc.setLogLevel("WARN")
    val stars = FileHandler.getStars(starsfile,numStars)
    val pixels = sc.range(0,width*height,1,numPartitions)
    val raybanks = pixels.glom().map(arr => CausticRayBank(arr,dx,dy,width,height))
    println(s"Putting into $numPartitions partitions")
    val parameters = MicroParameters(
      stars,
      shear,
      smooth,
      dx,
      dy,
      width,
      height)
    val broadParams = sc.broadcast(parameters)
    val tracer = new RayBankTracer()
    val srcPlane = tracer(raybanks,broadParams)
    val causticTracer = new CausticTracer()
    val caustics = causticTracer(srcPlane,broadParams)
//    FileHandler.saveDoubles("SavedCaustics",caustics.collect().head.compressed)
//    val collected = caustics.collect.head.printTo("TestCaustics.py")
    rddGrid = RDDGrid(caustics,nodeStructure = CausticTree.apply)
    rddGrid.cache()
    broadParams.unpersist()
  }



  def queryPoints(x0: Double, y0: Double, x1: Double, y1: Double, xDim: Int, yDim: Int, radius: Double, retFile:String, ctx: JavaRDD[Int], verbose: Boolean = false) = {
    val sc = ctx.context
    val generator = new GridGenerator(x0, y0, x1, y1, xDim, yDim)
    val retArr = rddGrid.queryPointsFromGen(generator, radius, sc, verbose = verbose)
    FileHandler.saveMagnifications(retFile,retArr)
  }

  def sampleLightCurvess(pointsFile: String, retFile:String, numLines:Int,radius: Double, ctx: JavaRDD[Int]) {
    val sc = ctx.context
    val lightCurves = FileHandler.getQueryPoints(pointsFile,numLines)
    val retArr = rddGrid.queryPoints(lightCurves, radius, sc, false)
    FileHandler.saveMagnifications(retFile,retArr)
  }

  def querySingleCurve(pointsFile: String, retFile:String, radius: Double, ctx: JavaRDD[Int]) {
    val sc = ctx.context
    val lightCurves = FileHandler.getQueryPoints(pointsFile,1).head
    val retArr = rddGrid.query_curve(lightCurves, radius, sc)
    FileHandler.saveMagnifications(retFile,Array(retArr))
  }

  def sampleLightCurves(pointsFile:String,retFile:String,numLines:Int,radius:Double,ctx:JavaRDD[Int]) = {
    val sc = ctx.context
    val lightCurves = FileHandler.getQueryPoints(pointsFile,numLines)
    val retArr = rddGrid.queryCaustics(lightCurves,radius,sc)
    val ret = retArr.map{arr =>
      arr.map(elem => if (elem) 2 else 1)
    }
    FileHandler.saveMagnifications(retFile,ret)
  }

}
