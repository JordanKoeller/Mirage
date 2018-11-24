package main

import java.io._

import org.apache.spark.api.java.JavaRDD

import spatialrdd.GridGenerator
import spatialrdd.RDDGrid
import spatialrdd.RDDGridProperty
import spatialrdd.partitioners.BalancedColumnPartitioner
import lensing.MicroRayTracer
import lensing.Star
import lensing.MicroParameters
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
    val tracer = new MicroRayTracer()
    val pixels = sc.range(0,width*height,1,numPartitions)
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
    val srcPlane = tracer(pixels,broadParams)
    val partitioner = new BalancedColumnPartitioner()
    rddGrid = RDDGrid(srcPlane,partitioner)
    broadParams.unpersist()
  }



  def queryPoints(x0: Double, y0: Double, x1: Double, y1: Double, xDim: Int, yDim: Int, radius: Double, retFile:String, ctx: JavaRDD[Int], verbose: Boolean = false) = {
    val sc = ctx.context
    val generator = new GridGenerator(x0, y0, x1, y1, xDim, yDim)
    val retArr = rddGrid.queryPointsFromGen(generator, radius, sc, verbose = verbose)
    FileHandler.saveMagnifications(retFile,retArr)
  }

  def sampleLightCurves(pointsFile: String, retFile:String, numLines:Int,radius: Double, ctx: JavaRDD[Int]) {
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

}
