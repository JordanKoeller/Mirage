package spatialrdd


import lensing.RayCollector
import utility.Result


trait SpatialData extends Serializable {
  


	def size:Int
	def query_point_count(x:Double, y:Double, r:Double):Result
	def intersects(x:Double,y:Double,r:Double):Boolean
	def searchNodes(x: Double, y: Double, r: Double, collector:RayCollector): Result
	def searchNodes(x1:Double,x2:Double,y1:Double,y2:Double,collector:RayCollector): Result

	}


