ZenCad
======
CAD system for righteous zen programmers  

What is it?
-----------
ZenCad is a system for using the OpenCascade geometry core in an OpenSCAD-like
script style.
So, it's  openscad idea, python language and opencascade power in one.  

Manual and Information
----------------------
- Manual: [here](https://mirmik.github.io/zencad/).

- Articles:  
	- habr: [Система скриптового 3д моделирования ZenCad](https://habr.com/ru/post/443140/)

- Community chat (Telegram): [https://t.me/zencad](https://t.me/zencad)

Installation
------------
### GUI system libraries on Linux
```
sudo apt install libxcb-xinerama0 libxkbcommon-x11-0
```

### Common

The default installation uses the prebuilt `cadquery-ocp-novtk` wheel from
PyPI. It does not use conda, download OCCT at import time, or install VTK.

```
python3 -m pip install "zencad[gui]"
zencad
```

For headless geometry use:

```
python3 -m pip install zencad
```

The current OCP wheels support CPython 3.10-3.14 on Windows x86-64, macOS
11+ x86-64/arm64, and Linux x86-64/aarch64 with glibc 2.31 or newer.

### For Windows:  
The PyPI OCP wheel currently targets 64-bit Windows.

To run ZenCad from a source checkout, open PowerShell in the repository and
use:

```powershell
.\start.ps1
```

The script creates `venv`, installs the project with its GUI dependencies,
and starts ZenCad. Arguments are forwarded to ZenCad; for example:

```powershell
.\start.ps1 .\zencad\examples\0.Base\helloworld.py
.\start.ps1 -SkipInstall
```

For an editable development installation without the startup script, install
the `gui` extra explicitly:

```powershell
python -m pip install -e ".[gui]"
python -m zencad
```

`python -m pip install -e .` installs only the headless geometry dependencies
and is not sufficient to launch the GUI.

Standalone Distribution
-----------------------
ZenCad have standalone version for Windows.
Windows prerelease version in [releases](https://github.com/mirmik/zencad/releases).

Source code
---------------
Main project repo: 
	[https://github.com/mirmik/zencad](https://github.com/mirmik/zencad)  
Related repos:  
	[https://github.com/mirmik/zenframe](https://github.com/mirmik/zenframe)  
	[https://github.com/mirmik/evalcache](https://github.com/mirmik/evalcache)  

HelloWorld
----------
```python
#!/usr/bin/env python3
#coding: utf-8

from zencad import *

model = box(200, center = True) - sphere(120) + sphere(60)

display(model)
show()
```
Result:  
![result.png](https://mirmik.github.io/zencad/images/generic/zencad-logo.png)
