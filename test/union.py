
import zencad

zencad.display(zencad.union(
	[
		zencad.box(3), 
		zencad.box(4).right(2),
		zencad.box(6).right(5)
	]))
zencad.show()