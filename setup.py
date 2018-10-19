#!/usr/bin/env python3

from wheel.bdist_wheel import bdist_wheel as bdist_wheel_
from setuptools import setup, Extension, Command
from distutils.util import get_platform

import sys

try:
	import PyQt5
except:
	print("PyQt5 needed.")
	print("try:")
	print("apt-get install python3-pyqt5")
	sys.exit()

setup(
	name = 'zencad',
	packages = ['zencad'],
	version = '0.6.3',
	license='MIT',
	description = 'CAD system for righteous zen programmers ',
	author = 'Sorokin Nikolay',
	author_email = 'mirmikns@yandex.ru',
	url = 'https://mirmik.github.io/zencad/',
	keywords = ['testing', 'cad'],
	classifiers = [],

    install_requires=[
        'evalcache',
        'pyservoce',
    ],
)
