#!/usr/bin/env python3

from wheel.bdist_wheel import bdist_wheel as bdist_wheel_
from setuptools import setup, Extension, Command
from distutils.util import get_platform

import glob
import sys
import os

directory = os.path.dirname(os.path.realpath(__file__))


setup(
    name="zencad",
    packages=["zencad"],
    version="1.0.10",
    license="MIT",
    description="CAD system for righteous zen programmers ",
    author="mirmik",
    author_email="mirmikns@yandex.ru",
    url="https://github.com/mirmik/zencad",
    long_description=open(os.path.join(
        directory, "README.md"), "r", encoding="utf8").read(),
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
            "geom2/*",
            "convert/*",
            "libs/*",
            "gui/*",
            "interactive/*",
            "convert/*",
            "internal_models/*",
            "examples/*",
            "examples/**/*",
            "examples/**/**/*",
        ]
    },
    include_package_data=True,
    install_requires=[
        "psutil",
        "numpy",
        "pillow",
        "evalcache>=1.14.0",
        'zenframe',
    ],
    extras_require={
        'gui': [
            'PyQt5'
        ]
    },
    entry_points={"console_scripts": [
        "zencad=zencad.__main__:main"
    ]},
)
