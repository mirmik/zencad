#!/usr/bin/env python3

import tempfile
import requests
import tarfile
import zipfile
import sys
import site
import shutil
import os

python_occ_precompiled_packages = {
	"linux-64" :{
		"python3.7": {
			"7.4.1": "https://anaconda.org/conda-forge/pythonocc-core/7.4.1/download/linux-64/pythonocc-core-7.4.1-py37h2700f40_0.tar.bz2"
		},
		"python3.8": {
			"7.4.1": "https://anaconda.org/conda-forge/pythonocc-core/7.4.1/download/linux-64/pythonocc-core-7.4.1-py38he1669a3_0.tar.bz2"
		},
		"python3.9": {
			"7.4.1": "https://anaconda.org/conda-forge/pythonocc-core/7.4.1/download/linux-64/pythonocc-core-7.4.1-py39h465cb30_0.tar.bz2"
		}
	},
	"win-64" : {
		"python3.7": {
			"7.4.1": "https://anaconda.org/conda-forge/pythonocc-core/7.4.1/download/win-64/pythonocc-core-7.4.1-py37hc019675_0.tar.bz2"
		},
		"python3.8": {
			"7.4.1": "https://anaconda.org/conda-forge/pythonocc-core/7.4.1/download/win-64/pythonocc-core-7.4.1-py38hb051852_0.tar.bz2"
		},
		"python3.9": {
			"7.4.1": "https://anaconda.org/conda-forge/pythonocc-core/7.4.1/download/win-64/pythonocc-core-7.4.1-py39h3d1c7c5_0.tar.bz2"
		}
	}
}

def download_repo(url, path):
	"""Just file downloading"""
	with requests.get(url, stream=True) as r:
		r.raise_for_status()
		file_size = int(r.headers['Content-length'])
		file_size_M = file_size/10**6

		print(f"Downloading: {url}")
		print(f"File size:, {file_size}, {file_size_M}MB")
		print(f"Target path: {path}")

		with open(path, 'wb') as f:
			downloaded_size = 0
			for chunk in r.iter_content(chunk_size=8192): 
				downloaded_size += len(chunk)
				downloaded_size_M = downloaded_size / 10**6
				f.write(chunk)
				sys.stdout.write(f"\rProgress: {downloaded_size}, {int(downloaded_size_M)}MB/{int(file_size_M)}MB, {int(downloaded_size/file_size*100)}%")
		print()
		print("Downloading status: Success")

def download_repo_to_temporary_directory(url) -> str:
	"""Download repo and return its temporary path"""
	path = os.path.join(tempfile.gettempdir(), os.path.basename(url))
	download_repo(url=url, path=path)
	return path

def extract_archive(path, extract_directory=None):
	print("Extract archive")

	extension = os.path.splitext(path)[1]
	if extension in (".bz2", ".gz", ".tgz"):
		print("Use tarfile extractor")
		archive = tarfile.TarFile.open(path)
	elif extension in ("zip"):
		print("Use zipfile extractor")
		archive = zipfile.ZipFile.open(path)
	else:
		raise Exception("Unresolved archive extension")
	
	if extract_directory is None:
		extract_directory = path + ".extract"

	print(f"Source: {path}")
	print(f"Target: {extract_directory}")
	archive.extractall(extract_directory)
	print("Extraction status: Success")

	return extract_directory

def user_site_packages_directory():
	return site.USER_SITE

def install_precompiled_python_occ(occversion="7.4.1"):
	if sys.platform == "linux":
		systref = "linux-64"
	elif sys.platform == "win32":
		systref = "win-64"

	ver = sys.version[:3]
	python_name = "python" + ver

	# Downloading precompiled repo
	url = python_occ_precompiled_packages[systref][python_name][occversion]
	path = download_repo_to_temporary_directory(url)
	
	#Extraction
	extract_directory = extract_archive(path)

	# Copy to site packages
	print("Copy package to site-packages")
	source_directory = os.path.join(extract_directory, 
		"lib", python_name, "site-packages", "OCC")
	target_directory = os.path.join(user_site_packages_directory(), 
		"OCC")
	print(f"Source: {source_directory}")
	print(f"Target: {source_directory}")
	shutil.copytree(source_directory, target_directory, dirs_exist_ok=True)	
	print("Copying status: Success")

	print(f"Precomiled OCC succesfually installed in {target_directory}")

def test_third_libraries():
	try:
		import OCC
		import OCC.Core
		import OCC.Core.gp
	except Exception as ex:
		if "libTK" in str(ex):
			return {
				"occt": False,
				"pythonocc": True,
			}

		return {
			"occt": None,
			"pythonocc": False,
		}

	return {
		"occt":True,
		"pythonocc":OCC.__file__,
	}

def console_third_libraries_installer_utility():
	yes = ['yes', 'y', '', "ye"]
	no = ['n', 'no']

	while True:
		third_libraries_status = test_third_libraries()
		print(third_libraries_status)

		if (
			third_libraries_status["occt"] and
			third_libraries_status["pythonocc"]
		):
			return True

		if third_libraries_status["pythonocc"] is False:
			print("Module pythonocc is not found")
			
			while True:
				inp = input("Are you want to install it from repository? [Y/n]").lower()
				if inp in yes:
					answer = True
					break
				elif inp in no:
					answer = False
					return False
				else:
					print("Unresolved answer")
	
			if answer:
				install_precompiled_python_occ()
				continue

		if third_libraries_status["occt"] is False:
			pass

		break

	return False

if __name__ == "__main__":
	sts = console_third_libraries_installer_utility()
	print(sts)