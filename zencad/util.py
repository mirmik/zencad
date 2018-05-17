import runpy

def execfile(path):
	#with open(path) as f:
	#	code = compile(f.read(), path, 'exec')
	#	exec(code, globals(), locals())
	#	return locals()
	file_globals = runpy.run_path(path)
	return file_globals