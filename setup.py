#!/usr/bin/env python

# Usage:
#  $ pip install .

from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize

import os
import numpy
import petsc4py

# PETSc version check - 3.18 or higher
from petsc4py import PETSc

petscVer = PETSc.Sys().getVersion()
print(f"Petsc version: {petscVer[0]}.{petscVer[1]}.{petscVer[2]} ", flush=True)

if petscVer[0] != 3 or petscVer[1] < 18:
    msg = (
        f"Minimum compatible version of petsc is 3.18.0, detected version "
        f"{petscVer[0]}.{petscVer[1]}.{petscVer[2]}"
    )
    raise RuntimeError(msg)

def configure():

    INCLUDE_DIRS = []
    LIBRARY_DIRS = []
    LIBRARIES = []

    # PETSc
    import os

    print(f"PETSC_INFO - {petsc4py.get_config()}")
    PETSC_DIR = petsc4py.get_config()["PETSC_DIR"]
    PETSC_ARCH = petsc4py.get_config()["PETSC_ARCH"]

    print(f"PETSC_DIR: {PETSC_DIR}")
    print(f"PETSC_ARCH: {PETSC_ARCH}")

    # It is preferable to use the petsc4py paths to the
    # petsc libraries for consistency but the pip installation
    # of PETSc sometimes points to the temporary setup up path

    if not os.path.exists(PETSC_DIR):
        if os.environ.get("CONDA_PREFIX") and not os.environ.get("PETSC_DIR"):
            PETSC_DIR = os.path.join(os.environ["CONDA_PREFIX"],"lib","python3.1", "site-packages", "petsc") # symlink to latest python
            PETSC_ARCH = os.environ.get("PETSC_ARCH", "")
        else:
            PETSC_DIR = os.environ["PETSC_DIR"]
            PETSC_ARCH = os.environ.get("PETSC_ARCH", "")

    print(f"PETSC_DIR: {PETSC_DIR}")
    print(f"PETSC_ARCH: {PETSC_ARCH}")


    from os.path import join, isdir

    if PETSC_ARCH and isdir(join(PETSC_DIR, PETSC_ARCH)):
        INCLUDE_DIRS += [
            join(PETSC_DIR, PETSC_ARCH, "include"),
            join(PETSC_DIR, "include"),
        ]
        LIBRARY_DIRS += [join(PETSC_DIR, PETSC_ARCH, "lib")]
        petscvars = join(PETSC_DIR,PETSC_ARCH,"lib","petsc","conf","petscvariables")
    else:
        if PETSC_ARCH:
            pass  # XXX should warn ...
        INCLUDE_DIRS += [join(PETSC_DIR, "include")]
        LIBRARY_DIRS += [join(PETSC_DIR, "lib")]
        petscvars = join(PETSC_DIR,"lib","petsc","conf","petscvariables")

    LIBRARIES += ["petsc"]

    # set CC compiler to be PETSc's compiler.
    # This ought include mpi's details, ie mpicc --showme,
    # needed to compile UW cython extensions
    compiler = ""
    with open(petscvars,"r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("CC ="):
                compiler = line.split("=",1)[1].strip()
    #print(f"***\n The c compiler is: {compiler}\n*****")
    os.environ["CC"] = compiler

    # PETSc for Python
    INCLUDE_DIRS += [petsc4py.get_include()]

    # NumPy
    INCLUDE_DIRS += [numpy.get_include()]

    return dict(
        include_dirs=INCLUDE_DIRS
        + [os.curdir]
        + [os.path.join(os.curdir, "underworld3")]
        + [os.path.join(os.curdir, "underworld3", "petsc")],
        libraries=LIBRARIES,
        library_dirs=LIBRARY_DIRS,
        runtime_library_dirs=LIBRARY_DIRS,
    )


conf = configure()

extra_compile_args = ["-O3", "-g"]
# extra_compile_args = ['-O0', '-g']
extensions = [
    Extension(
        "underworld3.cython.petsc_discretisation",
        sources=[
            "src/underworld3/cython/petsc_discretisation.pyx",
        ],
        extra_compile_args=extra_compile_args,
        **conf,
    ),
    Extension(
        "underworld3.cython.petsc_maths",
        sources=[
            "src/underworld3/cython/petsc_maths.pyx",
        ],
        extra_compile_args=extra_compile_args,
        **conf,
    ),
    Extension(
        "underworld3.kdtree",
        sources=[
            "src/underworld3/kdtree.pyx",
        ],
        extra_compile_args=extra_compile_args + ["-std=c++11"],
        language="c++",
        **conf,
    ),
    Extension(
        "underworld3.cython.petsc_types",
        sources=[
            "src/underworld3/cython/petsc_types.pyx",
        ],
        extra_compile_args=extra_compile_args,
        **conf,
    ),
    Extension(
        "underworld3.cython.generic_solvers",
        sources=[
            "src/underworld3/cython/petsc_generic_snes_solvers.pyx",
        ],
        extra_compile_args=extra_compile_args,
        **conf,
    ),
    Extension(
        "underworld3.function._function",
        sources=[
            "src/underworld3/function/_function.pyx",
            "src/underworld3/function/petsc_tools.c",
        ],
        extra_compile_args=extra_compile_args,
        **conf,
    ),
    Extension(
        "underworld3.function.analytic",
        sources=[
            "src/underworld3/function/analytic.pyx",
            "src/underworld3/function/AnalyticSolNL.c",
        ],
        extra_compile_args=extra_compile_args,
        **conf,
    ),
]

setup(
    name="underworld3",
    packages=find_packages(),
    package_data={"underworld3": ["*.pxd", "*.h", "function/*.h", "cython/*.pxd"]},
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": "3"},  # or "2" or "3str"
        build_dir="build",
        annotate=True,
        # gdb_debug=True,
        include_path=[petsc4py.get_include()],
    ),
)
