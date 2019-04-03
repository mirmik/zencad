import unittest
import zencad

class Ops3dProbe(unittest.TestCase):
	def setUp(self):
		zencad.lazy.encache=False
		zencad.lazy.decache=False
		zencad.lazy.fastdo=True

	def test_linear_extrude(self):
		proto = zencad.ngon(r=3, n=12)
		zencad.linear_extrude(proto=proto, vec=3).unlazy()
		zencad.linear_extrude(proto=proto, vec=(3,1,3)).unlazy()
		zencad.linear_extrude(proto, 3).unlazy()
		zencad.linear_extrude(proto, (3,1,3)).unlazy()

	def test_pipe(self):
		proto= zencad.circle(20)
		path = zencad.interpolate([(0,0,0), (0,0,10), (0,10,20)])
		zencad.pipe(proto, path).unlazy()
		zencad.pipe(proto=proto, path=path).unlazy()

	def test_pipe_shell(self):
		proto= zencad.circle(20, wire=True)
		path = zencad.interpolate([(0,0,0), (0,0,10), (0,10,20)])
		zencad.pipe_shell(proto, path).unlazy()
		zencad.pipe_shell(proto=proto, path=path).unlazy()
	
	def test_sweep(self):
		proto= zencad.circle(20, wire=True)
		path = zencad.interpolate([(0,0,0), (0,0,10), (0,10,20)])
		zencad.sweep(proto, path).unlazy()
		zencad.sweep(proto=proto, path=path).unlazy()
	
	def test_loft(self):
		arr=[
			zencad.circle(20, wire=True),
			zencad.circle(20, wire=True).up(10),
			zencad.square(20, wire=True, center=True).up(20)
		]
		zencad.loft(arr).unlazy()
		zencad.loft(arr, True).unlazy()
		zencad.loft(arr=arr, smooth=True).unlazy()
	
	def test_revol(self):
		zencad.revol(zencad.ngon(r=10, n=10).rotateX(zencad.deg(90)).right(30)).unlazy()
		zencad.revol(zencad.ngon(r=10, n=10).rotateX(zencad.deg(90)).right(30), yaw=zencad.deg(120)).unlazy()
	
	def test_thinksolid(self):
		zencad.thicksolid(zencad.box(10), -1, [(5,0,5)]).unlazy()
		zencad.thicksolid(proto=zencad.box(10), refs=[(5,0,5)], t=-1).unlazy()
		zencad.thicksolid(zencad.box(10), 1, [(5,0,5)]).unlazy()
		zencad.thicksolid(proto=zencad.box(10), refs=[(5,0,5)], t=1).unlazy()
	
	def test_fillet(self):
		zencad.box(20).fillet(1)
		zencad.box(20).fillet(r=1)
		zencad.fillet(proto=zencad.box(20), r=1)
		
		zencad.box(20).fillet(1, [(5,0,0)])
		zencad.box(20).fillet(refs=[(5,0,0)], r=1)
		zencad.fillet(proto=zencad.box(20), refs=[(5,0,0)], r=1)

	def test_chamfer(self):
		zencad.box(20).chamfer(1)
		zencad.box(20).chamfer(r=1)
		zencad.chamfer(proto=zencad.box(20), r=1)
		
		zencad.box(20).chamfer(1, [(5,0,0)])
		zencad.box(20).chamfer(refs=[(5,0,0)], r=1)
		zencad.chamfer(proto=zencad.box(20), refs=[(5,0,0)], r=1)
