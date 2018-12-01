


from distutils.core import setup, Extension

from Cython.Build import cythonize
import numpy


if __name__ =="__main__":
    ray_tracer = Extension("engine.ray_tracer", sources = ["engine/ray_tracer.pyx"], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11","-Ofast"], libraries = ["m"])
    peak_finding = Extension("calculator.peak_finding", sources = ["calculator/peak_finding.pyx"], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11","-Ofast"], libraries = ["m"])
    rand_functs = Extension("calculator.optimized_funcs", sources = ["calculator/optimized_funcs.pyx"], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11","-Ofast"], libraries = ["m"])
    renderer = Extension("views.Renderer", sources = ["views/Renderer.pyx"], language = "c++",    extra_compile_args=["-std=c++11","-fopenmp"], extra_link_args=["-std=c++11","-Ofast"], libraries = ["m"])
    setup(
        ext_modules = cythonize([
            ray_tracer,
            peak_finding,
            rand_functs,
            renderer
            ]),
        include_dirs = [numpy.get_include(),"engine","calculator","views"],
    )
