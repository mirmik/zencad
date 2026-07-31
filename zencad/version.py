from importlib.metadata import PackageNotFoundError, version

import OCP

try:
    __version__ = version("zencad")
except PackageNotFoundError:
    __version__ = "0+unknown"

__ocp_version__ = OCP.__version__
