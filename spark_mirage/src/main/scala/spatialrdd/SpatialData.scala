package spatialrdd
import utility.Index
import utility.IndexPair
import utility.DoublePair
trait SpatialData extends Serializable {
  


	def size:Int
	def query_point_count(x:Double, y:Double, r:Double):Int
	def intersects(x:Double,y:Double,r:Double):Boolean
}


