from zencad.zenlib import vector3 as vector
from zencad.zenlib import direction3 as direction
from zencad.zenlib import point3 as point

def points(tpls):
	return [ point(*t) for t in tpls ]