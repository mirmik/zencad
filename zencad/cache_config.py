"""Resolve and apply ZenCad's process-wide cache configuration."""

from dataclasses import dataclass
import getpass
import os
from pathlib import Path
import re
import stat
import tempfile


CACHE_DIRECTORY_ENV = "ZENCAD_CACHE_DIR"
CACHE_DISABLE_ENV = "ZENCAD_CACHE_DISABLE"

_UNSET = object()
_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off", ""}


@dataclass(frozen=True)
class CacheConfiguration:
    directory: Path
    enabled: bool


def _user_cache_token():
    if hasattr(os, "getuid"):
        return str(os.getuid())
    username = re.sub(r"[^A-Za-z0-9_.-]", "_", getpass.getuser())
    return username or "user"


def default_cache_directory():
    """Return one shared temporary cache directory for the current user."""
    return Path(tempfile.gettempdir()) / f"zencad-cache-{_user_cache_token()}"


def _as_bool(value, name):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(
        f"{name} must be one of: 1/0, true/false, yes/no, on/off"
    )


def normalize_cache_directory(value):
    if value is None or not str(value).strip():
        raise ValueError("Cache directory must not be empty")
    expanded = os.path.expandvars(os.path.expanduser(str(value)))
    return Path(expanded).resolve()


def resolve_cache_configuration(settings=None, environ=None):
    """Resolve settings first, then apply process environment overrides."""
    if settings is None:
        from zencad.settings import Settings

        settings = Settings
    if environ is None:
        environ = os.environ

    settings.restore()
    directory = normalize_cache_directory(
        settings.get(["cache", "directory"])
    )
    enabled = _as_bool(
        settings.get(["cache", "enabled"]),
        "cache.enabled",
    )

    if CACHE_DIRECTORY_ENV in environ:
        directory = normalize_cache_directory(environ[CACHE_DIRECTORY_ENV])
    if CACHE_DISABLE_ENV in environ:
        enabled = not _as_bool(
            environ[CACHE_DISABLE_ENV],
            CACHE_DISABLE_ENV,
        )
    return CacheConfiguration(directory=directory, enabled=enabled)


def prepare_cache_directory(directory):
    """Create a cache directory and secure the shared default on POSIX."""
    directory = normalize_cache_directory(directory)
    default_directory = normalize_cache_directory(default_cache_directory())
    if directory != default_directory:
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    try:
        directory.mkdir(mode=0o700, parents=True)
    except FileExistsError:
        pass

    metadata = directory.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise RuntimeError(
            f"Default cache path is not a directory: {directory}"
        )
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise PermissionError(
            f"Default cache directory belongs to another user: {directory}"
        )
    if os.name == "posix":
        directory.chmod(0o700)
    return directory


def configure(*, cache_dir=_UNSET, cache_enabled=_UNSET):
    """Apply an explicit cache override to the current Python process."""
    from zencad import lazifier

    current = lazifier.get_cache_configuration()
    directory = (
        current.directory
        if cache_dir is _UNSET
        else normalize_cache_directory(cache_dir)
    )
    enabled = (
        current.enabled
        if cache_enabled is _UNSET
        else _as_bool(cache_enabled, "cache_enabled")
    )
    return lazifier.apply_cache_configuration(
        CacheConfiguration(directory=directory, enabled=enabled)
    )


def reload_cache_configuration():
    """Reapply settings and environment after persistent settings changed."""
    from zencad import lazifier

    return lazifier.apply_cache_configuration(
        resolve_cache_configuration()
    )
