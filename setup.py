# from setuptools import setup, find_packages, Extension

# # for cpp extensions, just a template.
# # TODO: Fill out properly later
# cpp_extension = Extension(
#     name="pythonproject._core", 
#     sources=["src/cpp/main.cpp"],
#     include_dirs=["src/cpp"],
#     language="c++",
# )

# # Setup python package directory
# setup(
#     ext_modules=[cpp_extension],
#     package_dir={"": "src/pysync"},
#     packages=find_packages(where="src/pysync"),
# )


# Python only version, use above for cpp later on
from setuptools import setup, find_packages

setup(
    package_dir={"": "src"},
    packages=find_packages(where="src"),
)