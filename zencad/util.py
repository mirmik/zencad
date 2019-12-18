import runpy
import math
import pyservoce
import os
import evalcache
import sys

PROCNAME = str(os.getpid())

def print_to_stderr(*args):
    sys.stderr.write("STDERR {}: ".format(PROCNAME))
    sys.stderr.write(str(args))
    sys.stderr.write("\r\n")
    sys.stderr.flush()

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
    args = [ evalcache.unlazy_if_need(a) for a in arg ]

    if isinstance(args[0], pyservoce.point3):
        return args[0]

    return pyservoce.point3(*args)


def vector3(*arg):
    args = [ evalcache.unlazy_if_need(a) for a in arg ]

    if isinstance(args[0], pyservoce.vector3):
        return args[0]

    return pyservoce.vector3(*args)


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

def examples_paths(root = None):
    import zencad
    ret = []

    if root is None:
        root = os.path.join(zencad.moduledir, "examples")
    else:
        root = os.path.abspath(root)

    for path, subdirs, files in os.walk(root):
        subdirs[:] = [d for d in subdirs if not d.startswith('__pycache__')]
        for name in files:
            if os.path.splitext(name)[1] == ".py":
                ret.append(os.path.join(path, name))

    return ret

def examples_dict(root = None):
    import zencad
    if root is None:
        root = os.path.join(zencad.moduledir, "examples")

    dct = {}
    dct["__files__"] = set()

    for d in os.listdir(root):
        dpath = os.path.join(root, d)

        if d == "__pycache__" or d == "fonts":
            continue

        if os.path.isdir(dpath):
            dct[d] = examples_dict(dpath)
        else:
            dct["__files__"].add(d)

    return dct

def set_process_name(name):
    if sys.platform != "win32":
        import setproctitle
        setproctitle.setproctitle(name)  