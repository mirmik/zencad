import OCC.Core.BRepPrimAPI

def make_test_box():
	return OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeBox(10., 20., 30.).Shape()

