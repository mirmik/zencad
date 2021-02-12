import zencad
import evalcache
import zencad.lazifier

@zencad.lazifier.lazy.file_creator(pathfield="filepath")
def write_as_obj_wavefront(filepath, vertices, polygons):
	vertices = evalcache.unlazy_if_need(vertices)
	polygons = evalcache.unlazy_if_need(polygons)

	with open(filepath, 'w') as f:    
		f.write("# OBJ file\n")
		
		for v in vertices:
			f.write("v %.4f %.4f %.4f\n" % (v[0], v[1], v[2]))

		for p in polygons:
			f.write("f")
			for i in p:
				f.write(" %d" % (i + 1))
			f.write("\n")