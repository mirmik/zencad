#!/usr/bin/env python3

import zencad

model = zencad.execfile("box.py")["model"]

#scn = zencad.scene()
#scn.add(model)
#
#cam = zencad.camera(0,0,0,0,0,0)
#
#view = zencad.view(scn, cam)
#view.render()
#
#view.screenshot("path.png")

zencad.display(model)
zencad.show()