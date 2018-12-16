


from distutils.core import setup, Extension

import numpy
import sys


if __name__ =="__main__":
    EXT = None
    if "--no-cython" in sys.argv:
        EXT = ".cpp"
        sys.argv.remove('--no-cython')
    else:
        EXT = ".pyx"
    ray_tracer = Extension("mirage.engine.ray_tracer", sources = ["mirage/engine/ray_tracer" + EXT], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11","-Ofast"], libraries = ["m"])
    micro_ray_tracer = Extension("mirage.engine.micro_ray_tracer", sources = ["mirage/engine/micro_ray_tracer" + EXT], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11"], libraries = ["m"])
    peak_finding = Extension("mirage.calculator.peak_finding", sources = ["mirage/calculator/peak_finding" + EXT], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11"], libraries = ["m"])
    rand_functs = Extension("mirage.calculator.optimized_funcs", sources = ["mirage/calculator/optimized_funcs" + EXT], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11"], libraries = ["m"])
    renderer = Extension("mirage.views.Renderer", sources = ["mirage/views/Renderer" + EXT], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11"], libraries = ["m"])

    modules = [ray_tracer, peak_finding, rand_functs, renderer, micro_ray_tracer]

    if EXT == ".pyx":
        from Cython.Build import cythonize
        modules = cythonize(modules)
    setup(
        ext_modules = modules,
        include_dirs = [numpy.get_include(),"mirage/engine","mirage/calculator","mirage/views"],
    )
