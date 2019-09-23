ZenCad
======
CAD system for righteous zen programmers

What is it?
-----------
ZenCad - it's a system for use oce geometry core in openscad's script style.
So, it's  openscad idea, python language and opencascade power in one.  

Manual
------
You can find manual [here](https://mirmik.github.io/zencad/). Now only russian version.

Install
-------  
Install zencad from pypi:  
```python3 -m pip install zencad ```

Maybe need install qt5-default, because pyqt5 has trouble with xcb plugin.  
```apt install qt5-default ```


Get source code
---------------
```sh
git clone https://github.com/mirmik/zencad
```

Other repos of this project
---------------------------
[https://github.com/mirmik/servoce](https://github.com/mirmik/servoce)  
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

Articles
--------
habr: [Система скриптового 3д моделирования ZenCad](https://habr.com/ru/post/443140/)

![https://raw.githubusercontent.com/mirmik/zencad/master/docs/images/logo.png](https://raw.githubusercontent.com/mirmik/zencad/master/docs/images/car.png)
