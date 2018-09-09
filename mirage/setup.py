


from distutils.core import setup, Extension

from Cython.Build import cythonize
import numpy


if __name__ =="__main__":
	ray_tracer = Extension("engine/ray_tracer", sources = ["engine/ray_tracer.pyx"], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11","-Ofast"], libraries = ["m"])
	setup(
		ext_modules = cythonize([ray_tracer]),
		include_dirs = [numpy.get_include(),"engine"],
	)
