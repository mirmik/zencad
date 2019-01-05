#!/usr/bin/env python3

from wheel.bdist_wheel import bdist_wheel as bdist_wheel_
from setuptools import setup, Extension, Command
from distutils.util import get_platform

import zencad

import glob
import sys

#try:
#	import PyQt5
#except Exception(e):
#	print(e)
#	print("PyQt5 needed.")
#	print("try:")
#	print("apt-get install python3-pyqt5")
#	sys.exit()

setup(
	name = 'zencad',
	packages = ['zencad'],
	version = zencad.__version__,
	license='MIT',
	description = 'CAD system for righteous zen programmers ',
	author = 'Sorokin Nikolay',
	author_email = 'mirmikns@yandex.ru',
	url = 'https://mirmik.github.io/zencad/',
	long_description=open("README.md", "r").read(),
	long_description_content_type='text/markdown',
	keywords = ['testing', 'cad'],
	classifiers = [],
	scripts = ["routine/zencad"],

	package_data={'zencad': [
		'industrial-robot.svg',
	]},

	data_files = [
		("zencad/examples", [file for file in glob.glob("examples/*.py")]),
		("zencad/examples/openscad_like", [file for file in glob.glob("examples/openscad_like/*.py")]),
		("zencad/examples/storage", [file for file in glob.glob("examples/storage/*.py")]),
	],

	include_package_data=True,
	install_requires=[
		'evalcache==1.7.0',
		'pyservoce==1.7.0',
		'numpy',
		'pillow',
		'inotify',
		'PyQt5',
	],
)
