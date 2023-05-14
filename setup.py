from setuptools import find_packages, setup
from typing import List, Optional
from distutils.core import setup, Extension
import logging
from os import path

logger = logging.getLogger(__name__)

def get_ext_modules() -> Optional[List[Extension]]:
  try:
    from Cython.Build import cythonize
  except ImportError:
    logger.warn("Could not import cython. Using pre-compiled extension modules")
    logger.warn(
      "In order to compile extension modules please run 'pip install .[dev]'"
      " and run setup.py again.")
    return None
  import numpy
  extensions = [
    Extension("mirage.calc.tracers.micro_tracer_helper",
              sources=[path.join("mirage", "calc", "tracers", "micro_tracer_helper.pyx")],
              # define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
              include_dirs=[numpy.get_include()],
              extra_compile_args=["-fopenmp"]),
    Extension("mirage.calc.reducer_funcs",
              sources=[path.join("mirage", "calc", "reducer_funcs.pyx")],
              # define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
              include_dirs=[numpy.get_include()],
              extra_compile_args=["-fopenmp"]),
  ]
  return cythonize(extensions, include_path=[numpy.get_include()],)

setup(
  name="mirage",
  version="2.0",
  packages=find_packages(),
  install_requires=[
    "numpy==1.23.5",
    "astropy==5.1",
    "matplotlib==3.7.1",
    "scipy==1.10.0",
    "yaml==0.2.5",
  ],
  extras_require={
    "interractive": [
      "ipython==8.10.0",
    ],
    "dev": [
      "cython==0.29.33",
    ]
  },
  ext_modules=get_ext_modules(),
)