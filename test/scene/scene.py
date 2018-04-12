#!/usr/bin/env python3

import zencad

model = zencad.box(3,5,6)

scn = zencad.scene()
cam = zencad.camera()

view = zencad.view(scn, cam)


scn.add(model)



view.screen()