


from distutils.core import setup, Extension

import numpy
import sys
import os

def pathify(*parts):
    return os.sep.join(parts)

class ModuleBuilder:

    def __init__(self):
        self.modules = []
        self.built_modules = []

    def with_extension(self, path, sources):
        if isinstance(sources, str):
            sources = [sources]
        self.modules.append(
            Extension(path,
                      sources=sources,
                      language="c++",
                      extra_compile_args=['-fopenmp', '-std=c++11'],
                      extra_link_args=['-Ofast', '-std=c++11'],
            )
        )

    def _get_dirs(self):
        all_paths = []
        for extension in self.modules:
            all_paths.extend(extension.sources)
        distinct_dirs = set([
            path[:path.rindex(os.sep)]
            for path in all_paths
        ])
        return list(distinct_dirs)

    def cythonize(self):
        from Cython.Build import cythonize
        import Cython.Compiler.Options
        Cython.Compiler.Options.annotate = True
        self.built_modules = cythonize(self.modules, annotate=True)

    def setup(self):
        setup(
            ext_modules=self.built_modules,
            include_dirs=[
                numpy.get_include(), *self._get_dirs()
            ]
        )


if __name__ =="__main__":
    EXT = None
    if "--no-cython" in sys.argv:
        EXT = ".cpp"
        sys.argv.remove('--no-cython')
    else:
        EXT = ".pyx"

    builder = ModuleBuilder()
    
    builder.with_extension("mirage.engine.ray_tracer", pathify("mirage","engine","ray_tracer" + EXT))
    builder.with_extension("mirage.reducers.reducer", pathify("mirage", "reducers", "reducer" + EXT))
    builder.with_extension("mirage.reducers.magmap_reducer", pathify("mirage", "reducers", "magmap_reducer" + EXT))
    builder.with_extension("mirage.engine.micro_ray_tracer", pathify("mirage","engine","micro_ray_tracer" + EXT))
    builder.with_extension("mirage.calculator.peak_finding", pathify("mirage","calculator","peak_finding" + EXT))
    builder.with_extension("mirage.calculator.optimized_funcs", pathify("mirage","calculator","optimized_funcs" + EXT))
    # renderer = fastExt("mirage.views.Renderer", ["mirage"+os.sep+"views"+os.sep+"Renderer" + EXT])

    if EXT == ".pyx":
        builder.cythonize()
    builder.setup()
