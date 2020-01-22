#!/usr/bin/env python3

from wheel.bdist_wheel import bdist_wheel as bdist_wheel_
from setuptools import setup, Extension, Command
from distutils.util import get_platform

import glob
import sys
import os

directory = os.path.dirname(os.path.realpath(__file__))

requires = [
        "evalcache",
        "pyservoce>=1.15.2",
        "numpy",
        "pillow",
        "pyopengl",
        "PyQt5",
        "psutil"
    ] 

if sys.platform != "win32":
    requires.append("setproctitle")

setup(
    name="zencad",
    packages=["zencad"],
    version="0.25.0",
    license="MIT",
    description="CAD system for righteous zen programmers ",
    author="mirmik",
    author_email="mirmikns@yandex.ru",
    url="https://github.com/mirmik/zencad",
    long_description=open(os.path.join(directory, "README.md"), "r").read(),
    long_description_content_type="text/markdown",
    keywords=["testing", "cad"],
    classifiers=[],
    package_data={
        "zencad": [
            "industrial-robot.svg",
            "zencad_logo.png",
            "bird.jpg",
            "techpriest.jpg",
            "geom/*",
            "libs/*",
            "gui/*",
            "examples/*",
            "examples/**/*",
            "examples/**/**/*",
        ]
    },
    include_package_data=True,
    install_requires=requires,
    entry_points={"console_scripts": ["zencad=zencad.__main__:main"]},
)
