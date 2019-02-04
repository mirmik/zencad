#!/usr/bin/env python3

from wheel.bdist_wheel import bdist_wheel as bdist_wheel_
from setuptools import setup, Extension, Command
from distutils.util import get_platform

import zencad

import glob
import sys
import os

setup(
	name = 'zencad',
	packages = ['zencad'],
	version = '0.15.3',
	license='MIT',
	description = 'CAD system for righteous zen programmers ',
	author = 'mirmik',
	author_email = 'mirmikns@yandex.ru',
	url = 'https://mirmik.github.io/zencad/',
	long_description=open("README.md", "r").read(),
	long_description_content_type='text/markdown',
	keywords = ['testing', 'cad'],
	classifiers = [],

	package_data={
		'zencad': [ 'industrial-robot.svg', "examples/*", "examples/**/*"],
	},

	#data_files = [
	#	("zencad/examples", [file for file in glob.glob("examples/*.py")]),
	#	*[("zencad/examples/"+d, [file for file in glob.glob("examples/"+d+"/*")]) for d in os.listdir("examples") if os.path.isdir(os.path.join("examples", d)) and d != "__pycache__"]
	#],

	include_package_data=True,
	install_requires=[
		'evalcache==1.9.1',
		'pyservoce==1.9.2',
		'numpy',
		'pillow',
		'inotify',
		'PyQt5',
		'zencad-cli',
	],
)
