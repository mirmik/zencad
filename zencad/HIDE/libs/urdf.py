#!/usr/bin/env python3
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom import minidom

import os
import math

class urdf_writer:
	def __init__(self, name):
		self.obj = Element("robot", name=name)

	def add_link(self, name):
		SubElement(self.obj, "link", name=name)

	def add_joint(self, name, parent, child, type="continuous", axis=None, origin=None):
		joint = SubElement(self.obj, "joint", name=name, type=type)
		SubElement(joint, "parent", link=parent)
		SubElement(joint, "child", link=child)
		if origin:
			SubElement(joint, "origin", xyz=f"{origin[0][0]} {origin[0][1]} {origin[0][2]}", rpy=f"{origin[1][0]} {origin[1][1]} {origin[1][2]}")
		if axis:
			SubElement(joint, "axis", xyz=f"{axis[0]} {axis[1]} {axis[2]}")



	def save(self, path):
		with open(path, "w") as f:
			rough_string = tostring(self.obj, 'utf-8')
			reparsed = minidom.parseString(rough_string)
			f.write(reparsed.toprettyxml(indent="	"))

if __name__ == "__main__":
	writer = urdf_writer("test_robot")
	writer.add_link("link1")
	writer.add_link("link2")
	writer.add_link("link3")
	writer.add_link("link4")

	writer.add_joint("joint1", parent="link1", child="link2", axis=(-0.9,0.15,0), origin=((5,3,0),(0,0,0)))
	writer.add_joint("joint2", parent="link1", child="link3", axis=(-math.pi/4,math.pi/4,0), origin=((-2,5,0),(0,0,math.pi/2)))
	writer.add_joint("joint3", parent="link3", child="link4", axis=(math.pi/4,-math.pi/4,0), origin=((5,0,0),(0,0,-math.pi/2)))

	writer.save(os.path.expanduser("~/test/test.urdf"))