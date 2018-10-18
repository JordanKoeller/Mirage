#!/usr/bin/env bash

export LA_HOME=$(cat ~/.lensrc)
export PYSPARK_DRIVER_PYTHON=ipython
export PYTHONPATH="$LA_HOME"
#Pull out the configuration variables
MASTER=$(python -c 'from mirage import GlobalPreferences; print(GlobalPreferences["spark_configuration"]["master"])')
DRIVER_MEMORY=$(python -c 'from mirage import GlobalPreferences; print(GlobalPreferences["spark_configuration"]["driver-memory"])')
EXECUTOR_MEMORY=$(python -c 'from mirage import GlobalPreferences; print(GlobalPreferences["spark_configuration"]["executor-memory"])')
EXTRA_ARGS=$(python -c 'from mirage import GlobalPreferences; print(GlobalPreferences["spark_configuration"]["command-line-args"])')
JAR_LOC="$LA_HOME/spark_mirage/target/scala-2.11/spark_mirage-assembly-beta.jar"

export PYTHONSTARTUP="$LA_HOME/scripts/shell.py"

echo about to pyspark
#The command itself
pyspark --master $MASTER --executor-memory $EXECUTOR_MEMORY --driver-memory $DRIVER_MEMORY --jars $JAR_LOC
