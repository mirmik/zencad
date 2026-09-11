"""Launch the configured editor with the model path as an argument."""

import os
import shlex
import shutil
import subprocess


def editor_arguments(command, path, *, windows=None):
    if not isinstance(command, str):
        raise ValueError("Configure an external editor command in Settings.")
    if windows is None:
        windows = os.name == "nt"
    lexer = shlex.shlex(command, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    if windows:
        # Backslashes in Windows executable paths are literal separators.
        lexer.escape = ""
    arguments = list(lexer)
    if not arguments or not arguments[0]:
        raise ValueError("Configure an external editor command in Settings.")
    # Parse the template first: quotes and shell symbols in the filename
    # must never affect tokenization or select the executable.
    if "{path" in arguments[0]:
        raise ValueError("{path} must be an editor argument, not the executable.")
    try:
        arguments = [argument.format(path=os.fspath(path)) for argument in arguments]
    except (AttributeError, KeyError, IndexError, ValueError) as error:
        raise ValueError("Invalid editor command: use {path} for the file path.") from error
    if windows:
        executable = shutil.which(arguments[0]) or arguments[0]
        if executable.lower().endswith((".bat", ".cmd")):
            raise ValueError("Use the editor's .exe instead of a .bat/.cmd launcher.")
    return arguments


def launch_external_editor(command, path):
    if path is None:
        return None
    return subprocess.Popen(editor_arguments(command, path), shell=False)
