

import os
import sys
from distutils.core import Extension, setup

import numpy

compile_args = ['-fopenmp', '-std=c++11', '-Ofast', '-fPIC']
link_args = ['-Ofast', '-fopenmp']
if __name__ == "__main__":
  EXT = None
  if "--no-cython" in sys.argv:
    EXT = ".cpp"
    sys.argv.remove('--no-cython')
  else:
    EXT = ".pyx"
  ray_tracer = Extension("mirage.engine.ray_tracer", sources=["mirage" + os.sep + "engine" + os.sep + "ray_tracer" + EXT],
                         language="c++", extra_compile_args=compile_args, extra_link_args=link_args)
  dask_tracer = Extension("mirage.engine.dask_tracer", sources=["mirage" + os.sep + "engine" + os.sep + "dask_tracer" + EXT],
                         language="c++", extra_compile_args=compile_args, extra_link_args=link_args)
  micro_ray_tracer = Extension("mirage.engine.micro_ray_tracer", sources=[
                               "mirage" + os.sep + "engine" + os.sep + "micro_ray_tracer" + EXT], language="c++", extra_compile_args=compile_args, extra_link_args=link_args)
  peak_finding = Extension("mirage.calculator.peak_finding", sources=[
                           "mirage" + os.sep + "calculator" + os.sep + "peak_finding" + EXT], language="c++", extra_compile_args=compile_args, extra_link_args=link_args)
  rand_functs = Extension("mirage.calculator.optimized_funcs", sources=[
                          "mirage" + os.sep + "calculator" + os.sep + "optimized_funcs" + EXT], language="c++", extra_compile_args=compile_args, extra_link_args=link_args)
  renderer = Extension("mirage.views.Renderer", sources=["mirage" + os.sep + "views" + os.sep + "Renderer" + EXT],
                       language="c++", extra_compile_args=compile_args, extra_link_args=link_args)

  modules = [dask_tracer, micro_ray_tracer]

  if EXT == ".pyx":
    from Cython.Build import cythonize
    modules = cythonize(modules)
  setup(
      ext_modules=modules,
      include_dirs=[numpy.get_include(), "mirage" + os.sep + "engine", "mirage" +
                    os.sep + "calculator", "mirage" + os.sep + "views"],
  )
