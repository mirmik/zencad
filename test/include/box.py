#!/usr/bin/env python3

import zencad

model = zencad.box(30,20,10)

if __name__ == "__main__":
	zencad.display(model)
	zencad.show()