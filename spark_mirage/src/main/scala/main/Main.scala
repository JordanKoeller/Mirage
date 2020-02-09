package main

import lensing._
import org.apache.spark.api.java.JavaRDD
import spatialrdd._
import utility.{ArrayQueryIterator, FileHandler, GridQueryGenerator}

object Main {

  private var rddGrid: RDDGridProperty = null

  /**
    * Entry point for ray-tracing a lensing system and creating the RDDGrid. Note that this method does not actually
    * compute anything. The source plane is lazily evaluated when the RDDGrid is queried.
    * @param starsfile Binary file with all star's locations and masses. Usually a tempfile.
    * @param numStars The number of files specified in the starsFile.
    * @param shear Local shear value for the starry region.
    * @param smooth Local convergence value for the starry region in continuous (dark) matter.
    * @param dx Width of a pixel in units of \xi_0
    * @param dy Height of a pixel in units of \xi_0
    * @param width Number of columns of pixels in the rays traced.
    * @param height Number of rows of pixels in the rays traced.
    * @param jrdd Reference to a JavaRDD instance.
    * @param numPartitions Number of partitions to break the RDDGrid up into.
    */
  def createRDDGrid(
      starsfile: String,
      numStars: Int,
      shear: Double,
      smooth: Double,
      dx: Double,
      dy: Double,
      width: Long,
      height: Long,
      jrdd: JavaRDD[Int],
      numPartitions: Int
  ): Unit = {
    if (rddGrid != null) rddGrid.destroy()
    val sc = jrdd.context
    sc.setLogLevel("WARN")
    val stars = FileHandler.getStars(starsfile, numStars)
    val pixels = sc.range(0, width * height, 1, numPartitions)
    val raybanks = pixels.glom().map(arr => RayBank(arr, dx, dy, width, height))
    val parameters =
      MicroParameters(stars, shear, smooth, dx, dy, width, height)
    val broadParams = sc.broadcast(parameters)
    val tracer = new RayBankTracer()
    val srcPlane = tracer(raybanks, broadParams)
    val caustics = srcPlane
    broadParams.unpersist(true)
    rddGrid = RDDGrid[RayBank, OptTree[RayBank]](
      caustics,
      nodeStructure = OptTree.apply
    )
  }

  /**
    * This method creates an equally spaced grid to query. Useful for making a magnification map.
    * @param x0 "left" x value in units of \xi_0
    * @param y0 "bottom" y value in units of \xi_0
    * @param x1 "right" x value in units of \xi_0
    * @param y1 "top" y value in units of \xi_0
    * @param xDim Number of columns in the grid.
    * @param yDim Number of rows in the grid.
    * @param radius Radius of the query circle in units of \xi_0
    * @param retFile Filename to save the magnifications to.
    * @param ctx References to a JavaRDD instance.
    */
  def queryPoints(
      x0: Double,
      y0: Double,
      x1: Double,
      y1: Double,
      xDim: Int,
      yDim: Int,
      radius: Double,
      retFile: String,
      ctx: JavaRDD[Int]
  ): Unit = {
    val sc = ctx.context
    val collector = new GridQueryGenerator(x0, y0, x1, y1, xDim, yDim)
    val retArr = rddGrid.searchBatch(collector, radius, sc)
    FileHandler.saveMagnifications(retFile, retArr)
  }

  /**
    * Request a large batch of light curves be sampled. Note that the light curves can be of different lengths.
    * @param pointsFile Filename where the query points are specified.
    * @param retFile Filename to save the magnifications to.
    * @param numLines The number of light curves specified in the pointsFile.
    * @param radius Radius of quasar to simulation in units of \xi_0
    * @param ctx Reference to a JavaRDD instance.
    */
  def sampleLightCurves(
      pointsFile: String,
      retFile: String,
      numLines: Int,
      radius: Double,
      ctx: JavaRDD[Int]
  ): Unit = {
    val sc = ctx.context
    val lightCurves = FileHandler.getQueryPoints(pointsFile, numLines)
    val collector = new ArrayQueryIterator(lightCurves)
    val retArr = rddGrid.searchBatch(collector, radius, sc)
    FileHandler.saveMagnifications(retFile, retArr)
  }

  def querySingleCurve(
      pointsFile: String,
      retFile: String,
      radius: Double,
      ctx: JavaRDD[Int]
  ): Unit = {
    val sc = ctx.context
    val lightCurves = FileHandler.getQueryPoints(pointsFile, 1).head
    val retArr = rddGrid.query_curve(lightCurves, radius, sc)
    FileHandler.saveMagnifications(retFile, Array(retArr))
  }

  def setMoment(momentIndex: Int): Unit = {
    RayCollector.setCollector(momentIndex)
  }

  def setMoment(momentIndex: Int, parity: String): Unit = {
    val par =
      if (parity == "pos") Some(1)
      else if (parity == "neg") Some(-1)
      else if (parity == "zero") Some(0)
      else None
    RayCollector.setCollector(momentIndex)
    RayCollector.setParity(par)
  }

  /**
    * This method creates an equally spaced grid to query. Useful for making a magnification map. Note that this method does not receive a radius as an argument.
    * It bins rays into the grid specified by all the parameters. This type of binning is more akin to that used in Joachim Wambsganss' microlensing code.
    * @param x0 "left" x value in units of \xi_0
    * @param y0 "bottom" y value in units of \xi_0
    * @param x1 "right" x value in units of \xi_0
    * @param y1 "top" y value in units of \xi_0
    * @param xDim Number of columns in the grid.
    * @param yDim Number of rows in the grid.
    * @param retFile Filename to save the magnifications to.
    * @param ctx References to a JavaRDD instance.
    */
  def queryGrid(
      x0: Double,
      y0: Double,
      x1: Double,
      y1: Double,
      xDim: Int,
      yDim: Int,
      retFile: String,
      ctx: JavaRDD[Int]
  ): Unit = {
    val sc = ctx.context
    val collector = new GridQueryGenerator(x0, y0, x1, y1, xDim, yDim)
    val retArr = rddGrid.searchGrid(collector, sc)
    FileHandler.saveMagnifications(retFile, retArr)
  }
//  def sampleCaustics(pointsFile:String,retFile:String,numLines:Int,radius:Double,ctx:JavaRDD[Int]):Unit = {
//    val sc = ctx.context
//    val lightCurves = FileHandler.getQueryPoints(pointsFile,numLines)
//    val retArr = rddGrid.queryCaustics(lightCurves,radius,sc)
//    val ret = retArr.map{arr =>
//      arr.map(elem => if (elem) 1 else 0)
//    }
//    FileHandler.saveMagnifications(retFile,ret)
//  }

}
