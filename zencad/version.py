import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("zencad").version
except:
    __version__ = "Unresolved???"

__occt_version__ = "7.4.0"
__pythonocc_version__ = "7.4.1"
