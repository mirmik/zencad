ZenCad
======
CAD system for righteous zen programmers

What is it?
-----------
ZenCad - it's a system for use oce geometry core in openscad's script style.
So, it's  openscad idea, python language and opencascade power in one.  

Manual and Information
----------------------
- Manual: You can find manual [here](https://mirmik.github.io/zencad/). Now only russian version.  
- Articles:  
	- habr: [Система скриптового 3д моделирования ZenCad](https://habr.com/ru/post/443140/)

Installation
------------
Install zencad from pypi:  
```python3 -m pip install zencad ```

Maybe need install qt5-default, because pyqt5 has trouble with xcb plugin.  
```apt install qt5-default ```

Standalone Distribution
-----------------------
ZenCad should have standalone version for Windows.  
You can find windows prerelease version [here](https://github.com/mirmik/zencad/releases/tag/wintest)

Source code
---------------
Main project repo: 
	[https://github.com/mirmik/zencad](https://github.com/mirmik/zencad)  
Related repos:  
	[https://github.com/mirmik/servoce](https://github.com/mirmik/servoce)  
	[https://github.com/mirmik/evalcache](https://github.com/mirmik/evalcache)  

### Source code structure:
- ./zencad/ (package)
  - examples/ (gui`s example scripts)
  - gui/ (application and graphical interface code files)
  - geom/ (main zencad api functions)
  - . : other or not yet sorted....
- ./docs/ (manual directory. GitHub pages links here)
- ./mangen/ (scripts and texts for ./docs automated generation)
- ./utest/ (unit tests)
- ./tools/ (scripts for repository routine work)
- ./expers/ (place for maintainer experiments :-) )


HelloWorld
----------
```python
#!/usr/bin/env python3
#coding: utf-8

from zencad import *

model = box(200, center = True) - sphere(120) + sphere(60)

display(m)
show()
```
Result:  
![result.png](https://mirmik.github.io/zencad/images/generic/zencad-logo.png)
