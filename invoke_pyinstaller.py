#!/usr/bin/env python3

import PyInstaller.__main__
import os

package_name = "zencad"

PyInstaller.__main__.run([
    '--name=%s' % package_name,
    '--onefile',
    '--windowed',
    #'--add-binary=%s' % os.path.join('resource', 'path', '*.png'),
    #'--add-data=%s' % os.path.join('resource', 'path', '*.txt'),
    #'--icon=%s' % os.path.join('resource', 'path', 'icon.ico'),
    os.path.join('zencad', '__main__.py'),
])
