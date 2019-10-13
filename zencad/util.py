import runpy
import math
import pyservoce
import os

def execfile(path):
    # with open(path) as f:
    # 	code = compile(f.read(), path, 'exec')
    # 	exec(code, globals(), locals())
    # 	return locals()
    file_globals = runpy.run_path(path)
    return file_globals


def deg(grad):
    return float(grad) / 180.0 * math.pi


def angle_pair(arg):
    if isinstance(arg, tuple) or isinstance(arg, list):
        return arg
    return (0, arg)


def point3(*arg):
    if isinstance(arg[0], pyservoce.point3):
        return arg[0]

    return pyservoce.point3(*arg)


def vector3(*arg):
    if isinstance(arg[0], pyservoce.vector3):
        return arg[0]

    return pyservoce.vector3(*arg)


def points(tpls):
    return [point3(*t) for t in tpls]


def vectors(tpls):
    return [vector3(*t) for t in tpls]

def circle_tangent_points(center, radius, point):
    c_x = center[0]
    c_y = center[1]
    a_x = point[0] - c_x
    a_y = point[1] - c_y
    R = radius

    b1x = R*(R*a_x - a_y*math.sqrt(-R**2 + a_x**2 + a_y**2))/(a_x**2 + a_y**2)
    b1y = R*(R*a_y + a_x*math.sqrt(-R**2 + a_x**2 + a_y**2))/(a_x**2 + a_y**2)
    
    b2x = R*(R*a_x + a_y*math.sqrt(-R**2 + a_x**2 + a_y**2))/(a_x**2 + a_y**2)
    b2y = R*(R*a_y - a_x*math.sqrt(-R**2 + a_x**2 + a_y**2))/(a_x**2 + a_y**2)
    
    b1x += c_x
    b1y += c_y 
    b2x += c_x
    b2y += c_y 
    
    return [ point3(b1x,b1y), point3(b2x,b2y) ]

def examples_paths():
    import zencad
    ret = []

    root = os.path.join(zencad.moduledir, "examples")
    for path, subdirs, files in os.walk(root):
        for name in files:
            if os.path.splitext(name)[1] == ".py":
                ret.append(os.path.join(path, name))

    return ret