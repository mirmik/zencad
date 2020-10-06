# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import sys
import os
import glob

datas = []
for (p, d, f) in os.walk("./zencad/examples"):
  print(p)
  datas.extend([(os.path.join(p,a), os.path.relpath(p, start=".")) for a in f])

datas.append(("zencad/industrial-robot.svg", "zencad"))
datas.append(("zencad/techpriest.jpg", "zencad"))
datas.append(("zencad/zencad_logo.png", "zencad"))

print(datas)

extra_dll_dir = "../servoce/pyservoce/libs"
os.environ['PATH'] += os.pathsep + extra_dll_dir

a = Analysis(['zencad/__main__.py'],
             pathex=['~/project/zencad'],
             binaries=[],
             hiddenimports=[],
             hookspath=[],
             datas=datas,
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='ZenCad',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='ZenCad')
