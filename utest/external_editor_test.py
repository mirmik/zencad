import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import mock
import unittest

from zencad.gui.external_editor import editor_arguments, launch_external_editor


class ExternalEditorTest(unittest.TestCase):
    def test_path_is_substituted_after_parsing_the_template(self):
        paths = [
            '/tmp/моя модель.py',
            '/tmp/a "quote" and \'apostrophe\'.py',
            '/tmp/$(touch injected); `echo x` & %PATH% {path} #.py',
            'C:\\Мои модели\\part & (one) %TEMP%.py',
        ]
        for windows in (False, True):
            for template in ('editor --wait {path}', 'editor --wait "{path}"'):
                for path in paths:
                    with self.subTest(windows=windows, template=template, path=path):
                        self.assertEqual(
                            editor_arguments(template, path, windows=windows),
                            ['editor', '--wait', path],
                        )

    def test_executable_quotes_and_argument_suffixes(self):
        self.assertEqual(
            editor_arguments(
                '"/opt/My Editor/bin/editor" --goto="{path}:12:3"',
                '/tmp/my model.py', windows=False,
            ),
            ['/opt/My Editor/bin/editor', '--goto=/tmp/my model.py:12:3'],
        )
        self.assertEqual(
            editor_arguments(
                '"C:\\Program Files\\Editor\\editor.exe" --goto="{path}:12:3"',
                'C:\\Мои модели\\part.py', windows=True,
            ),
            ['C:\\Program Files\\Editor\\editor.exe',
             '--goto=C:\\Мои модели\\part.py:12:3'],
        )

    def test_posix_quoting_and_literal_braces_remain_supported(self):
        self.assertEqual(
            editor_arguments(
                "/opt/My\\ Editor/editor --title='{{model}} #1' '{path}'",
                '/tmp/a.py', windows=False,
            ),
            ['/opt/My Editor/editor', '--title={model} #1', '/tmp/a.py'],
        )

    def test_invalid_commands_and_windows_batch_launchers_are_rejected(self):
        for command in (None, '', '  ', '"" {path}', 'editor "{path}',
                        'editor {unknown}', 'editor {path.unknown}', '{path}', '{path!s}'):
            with self.subTest(command=command), self.assertRaises(ValueError):
                editor_arguments(command, '/tmp/a.py', windows=False)
        for executable in ('editor.cmd', 'editor.BAT'):
            with mock.patch('shutil.which', return_value=executable):
                with self.assertRaisesRegex(ValueError, r'\.exe'):
                    editor_arguments('editor {path}', 'part & other.py', windows=True)

    def test_no_file_does_not_launch_and_missing_editor_is_reported(self):
        with mock.patch('subprocess.Popen') as popen:
            self.assertIsNone(launch_external_editor('editor {path}', None))
            popen.assert_not_called()
        with mock.patch('subprocess.Popen', side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                launch_external_editor('missing-editor {path}', '/tmp/a.py')

    def test_real_process_receives_one_path_without_shell_expansion(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            stub = root / 'editor stub.py'
            output = root / 'arguments.json'
            marker = root / 'INJECTED'
            stub.write_text(
                'import json, sys\n'
                'from pathlib import Path\n'
                'Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:]), encoding="utf-8")\n',
                encoding='utf-8',
            )
            arguments = [sys.executable, str(stub), str(output), '{path}']
            if os.name == 'nt':
                command = subprocess.list2cmdline(arguments)
                path = str(root / 'модель & echo injected & %TEMP%.py')
            else:
                command = shlex.join(arguments)
                path = str(root / ('модель $(touch INJECTED); \"quoted\" \'name\'.py'))
            Path(path).write_text('# model\n', encoding='utf-8')
            # An accidental shell command would create the marker in this cwd.
            original_popen = subprocess.Popen
            def start(*args, **kwargs):
                return original_popen(*args, cwd=root, **kwargs)

            with mock.patch('subprocess.Popen', side_effect=start) as popen:
                process = launch_external_editor(command, path)
                try:
                    self.assertEqual(process.wait(timeout=10), 0)
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
                self.assertFalse(popen.call_args.kwargs['shell'])
            self.assertEqual(json.loads(output.read_text(encoding='utf-8')), [path])
            self.assertFalse(marker.exists())

    def test_frozen_linux_editor_uses_original_library_path(self):
        for original in (None, '', '/opt/editor-libs'):
            environment = {
                'LD_LIBRARY_PATH': '/bundle/_internal', 'PATH': '/usr/bin',
                'QT_QPA_PLATFORM_PLUGIN_PATH': '/bundle/_internal/PyQt5/plugins',
                'QT_QPA_FONTDIR': '/usr/share/fonts',
            }
            if original is not None:
                environment['LD_LIBRARY_PATH_ORIG'] = original
            with mock.patch.dict(os.environ, environment, clear=True), \
                    mock.patch.object(sys, 'frozen', True, create=True), \
                    mock.patch.object(sys, '_MEIPASS', '/bundle/_internal', create=True), \
                    mock.patch.object(sys, 'platform', 'linux'), \
                    mock.patch('subprocess.Popen') as popen:
                launch_external_editor('editor {path}', '/tmp/model.py')
                child_env = popen.call_args.kwargs['env']
                self.assertEqual(child_env.get('LD_LIBRARY_PATH'), original)
                self.assertNotIn('LD_LIBRARY_PATH_ORIG', child_env)
                self.assertNotIn('QT_QPA_PLATFORM_PLUGIN_PATH', child_env)
                self.assertEqual(child_env['QT_QPA_FONTDIR'], '/usr/share/fonts')
                self.assertEqual(child_env['PATH'], '/usr/bin')
                self.assertEqual(dict(os.environ), environment)


if __name__ == '__main__':
    unittest.main()
