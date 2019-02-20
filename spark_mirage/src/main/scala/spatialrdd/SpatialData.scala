package spatialrdd


import utility.Result


trait SpatialData extends Serializable {
  


	def size:Int
	def query_point_count(x:Double, y:Double, r:Double):Result
	def intersects(x:Double,y:Double,r:Double):Boolean
}


