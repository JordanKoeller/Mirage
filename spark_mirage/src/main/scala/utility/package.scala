

package object utility {
    type Index = Int
    
    type DoublePair = (Double,Double)
    
    
    
    class IndexPair(val v:Long=0l) extends AnyVal with Serializable {
      def _2:Int = {
        ((v << 32) >> 32).toInt
      }
      
      
      
      def _1:Int ={
         (v >> 32).toInt
      }

      def x:Int = _1
      def y:Int = _2
      
     override def toString():String = {
        "(" + this._1+","+this._2+")"
      }
    }
    def mkPair(x:Index, y:Index):IndexPair = {
    		new IndexPair((x.toLong << 32) + y.toLong)
    }
    
//    def mkPair(x:Int, y:Int):IndexPair = {
//    		new IndexPair((x << 16) + y)
//    }
    
    
    class PixelValue(val _hidden:Long) extends AnyVal {
      
      def x:Int = {
        (_hidden >> 48).toInt 
      }
      
      def y:Int = {
        (_hidden << 16 >> 48).toInt
      }
      
      def value:Int = {
        (_hidden << 32 >> 32).toInt
      }
      private def pos:Int = {
        (_hidden >> 32).toInt
      }
    }
    
    def pixelConstructor(x:Int,y:Int,value:Int):PixelValue = {
      pixelConstructor(pixelLongConstructor(x,y,value))
    }
    
    def pixelConstructor(l:Long):PixelValue = {
      new PixelValue(l)
    }
    
    def pixelLongConstructor(x:Int,y:Int,value:Int):Long = {
      val pos = (x << 16) + y
      (pos.toLong << 32) + value.toLong
    }
}
