#!/usr/bin/env python3

import traceback
import random
import string
import tempfile
import requests
import tarfile
import zipfile
import sys
import site
import shutil
import os
import re

#from zencad.version import __occt_version__, __pythonocc_version__

python_occ_precompiled_packages = None
occt_precompiled_libraries = None


class PythonOCCLibraryPath:
    def __init__(self, path):
        lst = path.split('/')
        self.version = lst[3]
        self.system = lst[5]
        pyvers_pre = re.findall("(py36|py37|py38|py39|py310|py311|py312|py313|py314)", lst[6])[0]
        self.pyvers = pyvers_pre.replace("py3", "python3.")
        self.link = path

    def __str__(self):
        return ("(version: " + self.version + ", system:" + self.system + 
            ", pyvers:" + self.pyvers + " " + str(hash(self)))

    def __hash__(self):
        return hash(self.version) + hash(self.system) + hash(self.pyvers)

    def __lt__(self, oth):
        if self.version < oth.version: return True
        if self.system < oth.system: return True
        if self.pyvers < oth.pyvers: return True
        return False

class OCCTLibraryPath:
    def __init__(self, path):
        lst = path.split('/')
        self.version = lst[3]
        self.system = lst[5]
        self.link = path

    def __str__(self):
        return ("(version: " + self.version + ", system:" + self.system + 
            " " + str(hash(self)))

    def __hash__(self):
        return hash(self.version) + hash(self.system)

    def __lt__(self, oth):
        if self.version < oth.version: return True
        if self.system < oth.system: return True
        return False

def get_python_version():
    return f"{sys.version_info[0]}.{sys.version_info[1]}"
    

def get_conda_pythonocc_list():
    dictionary = {}
    for url in [
        "https://anaconda.org/conda-forge/pythonocc-core/files?page=1",
        "https://anaconda.org/conda-forge/pythonocc-core/files?page=2",
        "https://anaconda.org/conda-forge/pythonocc-core/files?page=3",
        "https://anaconda.org/conda-forge/pythonocc-core/files?page=4"
    ]:
        html = requests.get(url).text
        matches = re.compile("/conda-forge/pythonocc-core/[a-z|A-Z|/|_|.|0-9|-]*\.bz2").findall(html)    
        libs = [ PythonOCCLibraryPath(m) for m in matches ]

        filtered_hash = []
        filtered_libs = []
        for l in libs:
            if hash(l) not in filtered_hash:
                filtered_libs.append(l)
                filtered_hash.append(hash(l))

        hashes = [hash(l) for l in filtered_libs] 
        hashes_set = set(hashes)

        for x in libs:
            if x.system not in dictionary:
                dictionary[x.system] = {}
            if x.pyvers not in dictionary[x.system]:
                dictionary[x.system][x.pyvers] = {}
            dictionary[x.system][x.pyvers][x.version] = "http://anaconda.org" + x.link

    return dictionary

def get_conda_occt_list():
    dictionary = {}
    #url = "https://anaconda.org/conda-forge/occt/files"
    for url in [
        "https://anaconda.org/conda-forge/occt/files?page=1",
        "https://anaconda.org/conda-forge/occt/files?page=2",
        "https://anaconda.org/conda-forge/occt/files?page=3",
        "https://anaconda.org/conda-forge/occt/files?page=4",
        "https://anaconda.org/conda-forge/occt/files?page=5",
        "https://anaconda.org/conda-forge/occt/files?page=6"
    ]:
        html = requests.get(url).text
        matches = re.compile("/conda-forge/occt/[a-z|A-Z|/|_|.|0-9|-]*\.bz2").findall(html)    
        libs = [ OCCTLibraryPath(m) for m in matches ]

        filtered_hash = []
        filtered_libs = []
        for l in libs:
            if hash(l) not in filtered_hash:
                filtered_libs.append(l)
                filtered_hash.append(hash(l))

        hashes = [hash(l) for l in filtered_libs] 
        hashes_set = set(hashes)

        for x in libs:
            if x.system not in dictionary:
                dictionary[x.system] = {}
            dictionary[x.system][x.version] = "http://anaconda.org" + x.link

    return dictionary

def update_python_occ_precompiled_packages():
    global python_occ_precompiled_packages 
    global occt_precompiled_libraries
    if python_occ_precompiled_packages is None: 
        python_occ_precompiled_packages = get_conda_pythonocc_list()
        print(python_occ_precompiled_packages)
    if occt_precompiled_libraries is None:
        occt_precompiled_libraries = get_conda_occt_list()
        print(occt_precompiled_libraries)

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
                sys.stdout.write(
                    f"\rProgress: {downloaded_size}, {int(downloaded_size_M)}MB/{int(file_size_M)}MB, {int(downloaded_size/file_size*100)}%")
        print()
        print("Downloading status: Success")


def download_repo_to_temporary_directory(url) -> str:
    """Download repo and return its temporary path"""
    addname = "".join(random.choice(string.ascii_lowercase) for i in range(12))
    path = os.path.join(tempfile.gettempdir(), addname +
                        "." + os.path.basename(url))
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


def getsitepackages():
    """Returns a list containing all global site-packages directories
    (and possibly site-python).

    For each directory present in the global ``PREFIXES``, this function
    will find its `site-packages` subdirectory depending on the system
    environment, and will return a list of full paths.
    """
    sitepackages = []
    seen = set()

    for prefix in PREFIXES:
        if not prefix or prefix in seen:
            continue
        seen.add(prefix)

        if sys.platform in ('os2emx', 'riscos'):
            sitepackages.append(os.path.join(prefix, "Lib", "site-packages"))
        elif os.sep == '/':
            sitepackages.append(os.path.join(prefix, "local/lib",
                                             "python" + get_python_version(),
                                             "dist-packages"))
            sitepackages.append(os.path.join(prefix, "lib",
                                             "python" + get_python_version(),
                                             "dist-packages"))
        else:
            sitepackages.append(prefix)
            sitepackages.append(os.path.join(prefix, "lib", "site-packages"))
        if sys.platform == "darwin":
            # for framework builds *only* we add the standard Apple
            # locations.
            from sysconfig import get_config_var
            framework = get_config_var("PYTHONFRAMEWORK")
            if framework:
                sitepackages.append(
                    os.path.join("/Library", framework,
                                 get_python_version(), "site-packages"))
    return sitepackages


def user_site_packages_directories():
    # user = os.environ.get('USER') # TODO: Win?

    # if user != "root":
    #	return site.USER_SITE
    # else:
    import numpy as _
    # print(_.__path__)
    # print(os.path.dirname(_.__path__))
    sdir = os.path.join(os.path.dirname(_.__file__), "..")
    sdir = os.path.abspath(sdir)

    print("SDIR", sdir)

    return [sdir, site.USER_SITE]


def get_platform():
    if sys.platform == "linux":
        return "linux-64"
    elif sys.platform == "win32":
        return "win-64"
    else:
        raise Exception("Unresolved architecture")


def install_precompiled_python_occ(occversion):
    update_python_occ_precompiled_packages()
    systref = get_platform()

    ver = get_python_version()
    python_name = "python" + ver
    
    # print system list
    print("Available python-occ systems:")
    for k in python_occ_precompiled_packages.keys():
        print("\t" + k)

    # print current system
    print("Current system:", systref)
    print("Available python versions:")
    for k in python_occ_precompiled_packages[systref].keys():
        print("\t" + k)

    # print current python version  
    print("Current python version:", python_name)

    # print available OCC versions
    print("Available OCC versions:")
    for k in python_occ_precompiled_packages[systref][python_name].keys():
        print("\t" + k)

    

    # Downloading precompiled repo
    url = python_occ_precompiled_packages[systref][python_name][occversion]
    print(f"Use url: {url}")
    path = download_repo_to_temporary_directory(url)
    print("Use temporary path: ", path)

    # Extraction
    extract_directory = extract_archive(path)

    # Copy to site packages
    print("Copy package to site-packages")

    if systref == "linux-64":
        source_directory = os.path.join(extract_directory,
                                        "lib",
                                        python_name,
                                        "site-packages",
                                        "OCC")
    else:
        source_directory = os.path.join(extract_directory,
                                        "Lib",
                                        "site-packages",
                                        "OCC")

    for t in user_site_packages_directories():
        try:
            target_directory = os.path.join(t,
                                            "OCC")
            print(f"Source: {source_directory}")
            print(f"Target: {target_directory}")
            shutil.copytree(source_directory, target_directory)
            break
        except Exception as ex:
            print("Fault", ex)
    else:
        print("Copying status: Fault")
        return -1

    print("Copying status: Success")
    print(f"Precomiled OCC succesfually installed in {target_directory}")
    return 0


def install_precompiled_occt_library(tgtpath, occt_version):
    update_python_occ_precompiled_packages()
    print("install_precompiled_occt_library", "tgtpath:",
          tgtpath, "occt_version:", occt_version)

    try:
        architecture = get_platform()

        # Downloading precompiled repo
        url = occt_precompiled_libraries[architecture][occt_version]
        path = download_repo_to_temporary_directory(url)

        # Extraction
        extract_directory = extract_archive(path)

        if architecture in ("linux-64"):
            target_directory = os.path.expanduser(
                f"~/.local/lib") if tgtpath is None else tgtpath
        elif architecture in ("win-64"):
            target_directory = os.path.expanduser(
                f"~/AppData/Local/occt-{occt_version}") if tgtpath is None else tgtpath
        else:
            raise Exception("unresolved architecture")
            #target_directory = os.path.expanduser(f"/usr/local/lib/") if tgtpath is None else tgtpath

        if not os.path.exists(target_directory):
            os.mkdir(target_directory)

        print("Copy libs to system libs directory")
        source_directory = os.path.join(os.path.join(extract_directory, "lib"))
        target_directory = os.path.join(target_directory)
        print(f"Source: {source_directory}")
        print(f"Target: {target_directory}")

        for item in os.listdir(source_directory):
            if os.path.isdir(os.path.join(source_directory, item)):
                continue
            shutil.copy(
                os.path.join(source_directory, item),
                os.path.join(target_directory, item)
            )

        print("Copying status: Success")

    except Exception as ex:
        print("Fault", ex)
        traceback.print_exc()
        return -1

    return 0


def test_third_libraries():
    update_python_occ_precompiled_packages()
    try:
        import OCC
        import OCC.Core
        import OCC.Core.gp
    except Exception as ex:
        print("test_third_libraries_import finished with exception:", str(ex))

        if "libTK" in str(ex) or "_gp" in str(ex):
            return {
                "occt": False,
                "pythonocc": OCC.__file__,
            }

        return {
            "occt": None,
            "pythonocc": False,
        }

    return {
        "occt": True,
        "pythonocc": OCC.__file__,
    }


def ask_yes_no(question):
    yes = ['yes', 'y', '', "ye"]
    no = ['n', 'no']

    while True:
        inp = input(question).lower()
        if inp in yes:
            return True
        elif inp in no:
            return False
        else:
            print("Unresolved answer")


def console_third_libraries_installer_utility(yes=False):
    update_python_occ_precompiled_packages()
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

            answer = ask_yes_no(
                "Are you want to install it from repository? [Y/n]") if not yes else True

            if answer:
                install_precompiled_python_occ()
                continue
            else:
                return False

        if third_libraries_status["occt"] is False:
            print("OCCT library is not found")

            answer = ask_yes_no(
                "Are you want to install it from repository? [Y/n]") if not yes else True

            if answer:
                install_precompiled_occt_library()
                continue
            else:
                return False

        break

    return False

if __name__ == "__main__":
    print(get_conda_occt_list())
