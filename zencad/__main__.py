#!/usr/bin/python3
#coding:utf-8

from zencad import *

logo = textshape("HelloWorld", 
	moduledir + "/examples/fonts/mandarinc.ttf", 20)
display(logo, Color(1,1,1,0))

show(showconsole=True, showeditor=True)