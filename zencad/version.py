import pkg_resources
import sys

try:
    __version__ = pkg_resources.get_distribution("zencad").version
except:
    __version__ = "Unresolved???"

if sys.version_info[1] >= 10:
    __occt_version__ = "7.6.2"
    __pythonocc_version__ = "7.6.2"

else:
    __occt_version__ = "7.5.1"
    __pythonocc_version__ = "7.5.1"
