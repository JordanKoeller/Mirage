from setuptools import find_packages, Extension, setup
import logging
from os import path

from Cython.Build import cythonize
import numpy

logger = logging.getLogger(__name__)


def get_ext_modules() -> list[Extension]:
    import numpy

    extensions = [
        # Extension(
        #     "mirage.calc.tracers.micro_tracer_helper",
        #     sources=[
        #         path.join(
        #             "mirage", "calc", "tracers", "micro_tracer_helper.pyx"
        #         )
        #     ],
        #     # define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        #     include_dirs=[numpy.get_include()],
        #     extra_compile_args=["-O3", "-fopenmp"],
        #     extra_link_args=["-O3", "-fopenmp"],
        # ),
        # Extension(
        #     "mirage.calc.tracers.tracers",
        #     sources=[
        #         path.join(
        #             "mirage", "calc", "tracers", "tracers.pyx"
        #         )
        #     ],
        #     include_dirs=[numpy.get_include(), path.join("mirage", "calc", "tracers")],
        #     extra_compile_args=["-O3", "--std=c++23"],
        #     extra_link_args=["-O3", "--std=c++23"],
        # ),
        Extension(
            "mirage.calc.tracers.micro_tracer_helper",
            sources=[
                path.join(
                    "mirage", "calc", "tracers", "micro_tracer_helper.pyx"
                )
            ],
            include_dirs=[numpy.get_include(), path.join("mirage", "calc", "tracers")],
            extra_compile_args=["-O3", "--std=c++20"],
            extra_link_args=["-O3", "--std=c++20"],
        ),
        Extension(
            "mirage.calc.fast_tree",
            sources=[
                path.join(
                    "mirage", "calc", "fast_tree.pyx"
                )
            ],
            include_dirs=[numpy.get_include(), path.join("mirage", "calc")],
            extra_compile_args=["--std=c++23"],
            extra_link_args=["--std=c++23"],
        ),
        Extension(
            "mirage.calc.reducer_funcs",
            sources=[path.join("mirage", "calc", "reducer_funcs.pyx")],
            # define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
            include_dirs=[numpy.get_include()],
            extra_compile_args=["-fopenmp"],
            extra_link_args=["-fopenmp"],
        ),
    ]
    return cythonize(
        extensions,
        include_path=[numpy.get_include()],
        exclude_failures=True,
    )


setup(
    name="mirage",
    version="2.0",
    packages=find_packages(),
    ext_modules=get_ext_modules(),
)
