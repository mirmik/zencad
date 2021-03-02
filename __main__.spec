# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

datas = []
for (p, d, f) in os.walk("./zencad/examples"):
  datas.extend([(os.path.join(p,a), os.path.relpath(p, start=".")) for a in f])

datas.append(("zencad/industrial-robot.svg", "zencad"))
datas.append(("zencad/techpriest.jpg", "zencad"))
datas.append(("zencad/zencad_logo.png", "zencad"))

path = os.getcwd()
zenframe_path = os.path.join(os.getcwd(), "..", "zenframe")

a = Analysis(['zencad/__main__.py'],
             pathex=[path, zenframe_path],
             binaries=[],
             datas=datas,
             hiddenimports=["zenframe"],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=True)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='ZenCad.exe' if sys.platform == "win32" else 'ZenCad',
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
