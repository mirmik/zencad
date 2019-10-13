#!/usr/bin/env python3

import zencad
import sys
import os

examples = zencad.util.examples_paths()
#print(examples)

for epath in examples:
	cmd = sys.executable + " -m zencad --disable-show " + epath
	print(cmd)
	os.system(cmd)

	pass