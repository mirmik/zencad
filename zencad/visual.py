import zencad
import zencad.shower
import numpy as np
from pyservoce import Scene, Viewer

from PIL import Image

from evalcache.lazyfile import LazyFile

lazyfile = LazyFile()

@lazyfile("path")
def screen(model, path):
	scn = Scene()
	scn.add(model)
	viewer = Viewer(scn)
	view = viewer.create_view()
	view.set_virtual_window(800, 600)
	view.fit_all()

	raw = view.rawarray()
	npixels = np.reshape(np.asarray(raw), (600,800,3))
	nnnpixels = np.flip(npixels, 0).reshape((800 * 600 * 3))

	rawiter = iter(nnnpixels)
	pixels = list(zip(rawiter, rawiter, rawiter))
		
	image = Image.new("RGB", (800, 600))
	image.putdata(pixels)

	image.save(path)
