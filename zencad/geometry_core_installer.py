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

from zencad.version import __occt_version__, __pythonocc_version__

python_occ_precompiled_packages = {
    "linux-64": {
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
    "win-64": {
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

occt_precompiled_libraries = {
    "linux-64":
        {
            "7.4.0": "https://github.com/zencad/x86_64-linux64-occt7.4.0/raw/master/bin/x86_64-linux64-occt7.4.0.tar.gz"
        },
    "win-64":
        {
            "7.4.0": "https://github.com/zencad/servoce-thirdlibs-win-occ7.4/raw/master/dll/x86_64-win64-occt7.4.0.tar.gz"
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
                                             "python" + sys.version[:3],
                                             "dist-packages"))
            sitepackages.append(os.path.join(prefix, "lib",
                                             "python" + sys.version[:3],
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
                                 sys.version[:3], "site-packages"))
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


def install_precompiled_python_occ(occversion=__pythonocc_version__):
    systref = get_platform()

    ver = sys.version[:3]
    python_name = "python" + ver

    # Downloading precompiled repo
    url = python_occ_precompiled_packages[systref][python_name][occversion]
    path = download_repo_to_temporary_directory(url)

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


def install_precompiled_occt_library(tgtpath=None, occt_version=__occt_version__):
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
                f"~/.local/lib/occt-{occt_version}") if tgtpath is None else tgtpath
        elif architecture in ("win-64"):
            target_directory = os.path.expanduser(
                f"~/AppData/Local/occt-{occt_version}") if tgtpath is None else tgtpath
        else:
            raise Exception("unresolved architecture")
            #target_directory = os.path.expanduser(f"/usr/local/lib/") if tgtpath is None else tgtpath

        if not os.path.exists(target_directory):
            os.mkdir(target_directory)

        print("Copy libs to system libs directory")
        source_directory = os.path.join(extract_directory)
        target_directory = os.path.join(target_directory)
        print(f"Source: {source_directory}")
        print(f"Target: {target_directory}")

        for item in os.listdir(source_directory):
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
    sts = console_third_libraries_installer_utility()
