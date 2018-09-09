val spark = "org.apache.spark" % "spark-core_2.11" % "2.2.0" % "provided"
val sparkSQL = "org.apache.spark" % "spark-sql_2.11" % "2.2.0" % "provided"
lazy val root = (project in file("."))
  .settings(
    name         := "lensing_simulator_spark_kernel",
    organization := "edu.trinity",
    scalaVersion := "2.11.8",
    version      := "0.1.0-SNAPSHOT",
    libraryDependencies += spark,
    scalacOptions := Seq("-optimise")
  )
