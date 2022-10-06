



.PHONY: all
all:
	make build
	make scala-module

.PHONY: scratch
scratch:
	make cython-build
	make scala-module

.PHONY: build
build:
	python mirage/setup.py build_ext --inplace --no-cython
	make clean

cython-build:
	python mirage/setup.py build_ext --inplace
	make clean

scala-module: spark_mirage/build.sbt
	cd spark_mirage; sbt -batch package

# You can set these variables from the command line.
.PHONY: docs
docs:
	sphinx-build docs/source docs/build -a




.PHONY: clean
clean:
	rm -rf build


