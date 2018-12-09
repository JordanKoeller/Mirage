.TH mirage 7 "2018-12-12" "1.0.0" "Mirage usage instructions"
.SH NAME
Mirage - Simulation and analysis of arbitrary-radius gravitationally lensed quasars.
.SH SYNOPSIS
.B mirage
[
.I
OPTIONS
]
.PP
.B mirage
[
.I OPTIONS
]
.B --run 
.I INPUT_FILE OUTPUT_FILE

.SH DESCRIPTION

.B mirage
is a program for simulating, as well as analyzing results from such simulations of gravitationally lensed quasars of arbitrary radius.

To compute simulations, start 
.B mirage
with the 
.I --run INPUT_FILE OUTPUT_FILE
flag, where 
.I INPUT_FILE
is a parameters file specifying the system to simulate, and
.I OUTPUT_FILE
specifies where to put the results. For more info about running simulations
as well as the parameters file, see the official documentation hosted at
.I http://www.cs.trinity.edu/~jkoeller/Mirage/run_simulation.html.
Example parameters files may also be found in the 
.I test_parameters
directory.

.B mirage
includes two backends for running simulation. Simulations may be ran on the local machine with optimized code written in 
.I C/C++
with
.I openmp
for parallelization (default), or ran remotely on a 
.I spark
cluster.

In addition to tools for computing simulations, 
.B mirage
also includes tools for analyzing simulation results in the 
.I lens_analysis 
module. Running 
.B mirage
without the 
.I --run
file automatically sets up a python environment for analyzing results via
.I lens_analysis.
For more info about 
.I lens_analysis,
see its docstring accessable through the command

.in +.4i
>>> help(la)
.in

from within 
.I mirage
or online at 
.I http://www.cs.trinity.edu/~jkoeller/Mirage/lens_analysis.html.

For more information about
.I mirage, 
what it can model and how to use it effectively, see the documentation at
.I http://www.cs.trinity.edu/~jkoeller/Mirage/index.html.


.SH OPTIONS
.in -.2i
.B Environment Options
.in
.B -l, --local
.bp
.in +.4i
Emulate a cluster locally. Spark will set up a spark cluster locally, with as many partitions as there are cores on your machine. This options is useful for quick testing of updates to the spark simulation backend. Not recommended for full-scale simulations.
.in

.B -c, --cluster
.bp
.in +.4i
Connect to cluster. If no cluster parameters are specified, it will use the preferences set in the "cluster_config" file.
.in

.B -n, --no-gui
.bp
.in +.4i
Disable visualization tools. This options lets you prohibit a GUI event loop from being started. Useful for starting simulations over SSH connection.
.in

.in -.2i
.B Cluster Configuration Options
.in
.sp
.B --num-executors 
.I NUM
.bp
.in +.4i
Number of executors to request from the spark cluster. Overrides settings in "cluster_config".
.in

.B --executor-memory 
.I AMT
.bp
.in +.4i
The amount of ram to reserve on each executor. Overrides settings in "cluster_config".
.I AMT
should be an integer followed by a unit (e.g. 1000M, 2G).
.in

.B --driver-memory
.I AMT
.bp
.in +.4i
The amount of ram to reserve on the driver node. Overrides settings in "cluster_config".
.I AMT
should be an integer followed by a unit. e.g. 1000M, 2G.
.in

.B --master
.I MASTER_URL
.bp
.in +.4i
The URL of the cluster to connect to. Overrides settings in "cluster_config\"
.in

.B --extra-spark-opts
.I OPTS
.bp
.in +.4i
Extra arguments to pass to
.I pyspark.
To see available options, run the command "pyspark --help"
.in

.SH AUTHOR

Jordan Koeller, Trinity University. 
.I jkoeller@trinity.edu

David Pooley, Ph.D. Trinity University. 
.I dpooley@trinity.edu


.SH ACKNOWLEDGEMENTS
Man page made with the help of http://www.linuxhowtos.org/System/creatingman.htm

