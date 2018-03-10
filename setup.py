#!/usr/bin/env python3

from setuptools import setup
from setuptools.command.install import install
import os

setup(
	name = 'dzencad',
	packages = ['dzencad'],
	version = '0.1.4',
	license='MIT',
	description = 'CAD system for righteous dzen programmers ',
	author = 'Sorokin Nikolay',
	author_email = 'mirmikns@yandex.ru',
	url = 'https://github.com/mirmik/dzencad',
	keywords = ['testing', 'cad'],
	classifiers = [],

	scripts = [],
	
	package_data={
		'dzencad': [
    		'dzenlib.so',
    		'widget.so',
    		'libboost_python-py35.so.1.58.0',
    	],
    },
)
