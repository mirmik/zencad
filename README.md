ZenCad
======
**NOTE: Astrologers have announced a month of changes. ZenCad migrate to pythonocc wrapper. It break old library distribution strategy. Now OCCT and pythonocc will be installed over console/gui instruments or mannually. Most of the functionality has been restored on the new shell, but some backward compatibility violations are possible. servoce package is removed for now. (You can find old zencad/servoce variant in `master_v2_archive` branch)**

CAD system for righteous zen programmers  

Status:  
![](https://travis-ci.org/mirmik/zencad.svg?branch=master) - master  
![](https://travis-ci.org/mirmik/zencad.svg?branch=dev) - dev  

What is it?
-----------
ZenCad - it's a system for use oce geometry core in openscad's script style.
So, it's  openscad idea, python language and opencascade power in one.  

Manual and Information
----------------------
- Manual: You can find manual [here](https://mirmik.github.io/zencad/).

- Articles:  
	- habr: [Система скриптового 3д моделирования ZenCad](https://habr.com/ru/post/443140/)

- Community chat (Telegram): [https://t.me/zencad](https://t.me/zencad)

Installation
------------
Install zencad from pypi:  
```python3 -m pip install zencad ```

Maybe need install qt5-default, because pyqt5 has trouble with xcb plugin.  
```apt install qt5-default ```

### For Windows:  
Windows version of ZenCad needed `vcredist` (Microsoft Redistibutable Package).  
Please, install `vcredist 2015` for Python3.7 and also `vcredist 2019` for Python3.8  

Standalone Distribution
-----------------------
ZenCad have standalone version for Windows.  
You can find windows prerelease version in [releases](https://github.com/mirmik/zencad/releases).

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

display(m)
show()
```
Result:  
![result.png](https://mirmik.github.io/zencad/images/generic/zencad-logo.png)
