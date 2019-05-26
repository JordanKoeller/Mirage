


from distutils.core import setup, Extension

import numpy
import sys
import os


if __name__ =="__main__":
    EXT = None
    if "--no-cython" in sys.argv:
        EXT = ".cpp"
        sys.argv.remove('--no-cython')
    else:
        EXT = ".pyx"
    ray_tracer = Extension("mirage.engine.ray_tracer", sources = ["mirage"+os.sep+"engine"+os.sep+"ray_tracer" + EXT], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11","-Ofast"])
    micro_ray_tracer = Extension("mirage.engine.micro_ray_tracer", sources = ["mirage"+os.sep+"engine"+os.sep+"micro_ray_tracer" + EXT], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11"])
    peak_finding = Extension("mirage.calculator.peak_finding", sources = ["mirage"+os.sep+"calculator"+os.sep+"peak_finding" + EXT], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11"])
    rand_functs = Extension("mirage.calculator.optimized_funcs", sources = ["mirage"+os.sep+"calculator"+os.sep+"optimized_funcs" + EXT], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11"])
    renderer = Extension("mirage.views.Renderer", sources = ["mirage"+os.sep+"views"+os.sep+"Renderer" + EXT], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11"])

    modules = [ray_tracer, peak_finding, rand_functs, renderer, micro_ray_tracer]

    if EXT == ".pyx":
        from Cython.Build import cythonize
        modules = cythonize(modules)
    setup(
        ext_modules = modules,
        include_dirs = [numpy.get_include(),"mirage"+os.sep+"engine","mirage"+os.sep+"calculator","mirage"+os.sep+"views"],
    )
