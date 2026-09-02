import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

import zencad
from zencad.cache_config import (
    CACHE_DIRECTORY_ENV,
    CACHE_DISABLE_ENV,
    CacheConfiguration,
    current_cache_configuration,
    default_cache_directory,
    normalize_cache_directory,
    resolve_cache_configuration,
)
from zencad.settings import ZencadSettings


class CacheConfigurationTest(unittest.TestCase):
    def make_settings(self, root, directory, enabled=True):
        settings = ZencadSettings(Path(root) / "settings.conf")
        settings.set(["cache", "directory"], str(directory))
        settings.set(["cache", "enabled"], enabled)
        return settings

    def test_default_directory_is_shared_per_user_under_temp(self):
        with mock.patch(
            "zencad.cache_config.tempfile.gettempdir",
            return_value="/var/tmp",
        ):
            directory = default_cache_directory()
            self.assertEqual(directory.parent, Path("/var/tmp"))
            self.assertTrue(directory.name.startswith("zencad-cache-"))
            if hasattr(os, "getuid"):
                self.assertEqual(
                    directory.name,
                    f"zencad-cache-{os.getuid()}",
                )

    def test_environment_overrides_settings_directory(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = self.make_settings(root, root / "from-settings")
            resolved = resolve_cache_configuration(
                settings=settings,
                environ={
                    CACHE_DIRECTORY_ENV: str(root / "from-environment"),
                },
            )
            self.assertEqual(
                resolved,
                CacheConfiguration(
                    normalize_cache_directory(root / "from-environment"),
                    True,
                ),
            )

    def test_environment_can_disable_and_reenable_cache(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings = self.make_settings(
                root,
                root / "cache",
                enabled=True,
            )
            disabled = resolve_cache_configuration(
                settings=settings,
                environ={CACHE_DISABLE_ENV: "yes"},
            )
            enabled = resolve_cache_configuration(
                settings=settings,
                environ={CACHE_DISABLE_ENV: "0"},
            )
            self.assertFalse(disabled.enabled)
            self.assertTrue(enabled.enabled)

    def test_python_api_switches_directory_and_disables_disk_cache(self):
        previous = current_cache_configuration()
        self.addCleanup(
            zencad.configure,
            cache_dir=previous.directory,
            cache_enabled=previous.enabled,
        )
        with TemporaryDirectory() as directory:
            cache_directory = Path(directory) / "cache"
            configured = zencad.configure(
                cache_dir=cache_directory,
                cache_enabled=True,
            )
            expected_cache_directory = normalize_cache_directory(cache_directory)
            self.assertEqual(configured.directory, expected_cache_directory)
            self.assertTrue(cache_directory.is_dir())
            self.assertEqual(
                zencad.box(1).context.cache_directory,
                expected_cache_directory,
            )

            disabled_directory = Path(directory) / "disabled"
            configured = zencad.configure(
                cache_dir=disabled_directory,
                cache_enabled=False,
            )
            self.assertFalse(configured.enabled)
            self.assertFalse(disabled_directory.exists())

            shape = zencad.box(1)
            self.assertFalse(shape.context.cache_enabled)
            shape.native()
            self.assertFalse(disabled_directory.exists())

            brep_path = Path(directory) / "shape.brep"
            zencad.to_brep(shape, brep_path)
            self.assertGreater(brep_path.stat().st_size, 0)

    def test_public_clear_cache_removes_v2_records(self):
        previous = current_cache_configuration()
        self.addCleanup(
            zencad.configure,
            cache_dir=previous.directory,
            cache_enabled=previous.enabled,
        )
        with TemporaryDirectory() as directory:
            cache_directory = Path(directory) / "cache"
            zencad.configure(cache_dir=cache_directory, cache_enabled=True)
            zencad.box(2).native()

            removed = zencad.clear_cache()

            self.assertGreater(removed, 0)
            self.assertEqual(zencad.clear_cache(), 0)

    def test_fresh_process_honors_environment_without_settings_or_pyqt(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cache_directory = root / "agent-cache"
            config_directory = root / "config"
            environment = os.environ.copy()
            environment["XDG_CONFIG_HOME"] = str(config_directory)
            environment[CACHE_DIRECTORY_ENV] = str(cache_directory)
            environment[CACHE_DISABLE_ENV] = "1"
            process = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import zencad; "
                        "shape = zencad.box(1); "
                        "assert not shape.context.cache_enabled; "
                        "shape.native()"
                    ),
                ],
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertFalse(cache_directory.exists())

    def test_fresh_process_uses_directory_saved_in_settings(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cache_directory = root / "settings-cache"
            config_directory = root / "config"
            settings = ZencadSettings(config_directory / "ZenCad" / "settings.conf")
            settings.set(["cache", "directory"], str(cache_directory))
            settings.store()

            environment = os.environ.copy()
            environment["XDG_CONFIG_HOME"] = str(config_directory)
            environment.pop(CACHE_DIRECTORY_ENV, None)
            environment.pop(CACHE_DISABLE_ENV, None)
            process = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import zencad; "
                        "shape = zencad.box(1); shape.native(); "
                        "assert str(shape.context.cache_directory) == "
                        f"{str(normalize_cache_directory(cache_directory))!r}"
                    ),
                ],
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertTrue(cache_directory.is_dir())

    @unittest.skipUnless(os.name == "posix", "POSIX permissions required")
    def test_default_cache_does_not_require_writable_home(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            readonly_home = root / "home"
            readonly_home.mkdir()
            readonly_home.chmod(0o500)
            environment = os.environ.copy()
            environment["HOME"] = str(readonly_home)
            environment["XDG_CONFIG_HOME"] = str(readonly_home / ".config")
            environment.pop(CACHE_DIRECTORY_ENV, None)
            environment.pop(CACHE_DISABLE_ENV, None)
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        "import zencad; zencad.box(1).native()",
                    ],
                    cwd=Path(__file__).resolve().parents[1],
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            finally:
                readonly_home.chmod(0o700)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(list(readonly_home.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
