# zencad
CAD system for righteous zen programmers

![https://raw.githubusercontent.com/mirmik/zencad/master/docs/images/logo.png](https://raw.githubusercontent.com/mirmik/zencad/master/docs/images/logo.png)

What is it?
-----------
ZenCad - it's a system for use oce geometry core in openscad's script style.
So, it's  openscad idea, python language and opencascade power in one.  

Manual
------
[Мануал читать тут](https://mirmik.github.io/zencad/)

Install
-------  
```python3 -m pip install zencad ```

Get source code
---------------
```sh
git clone https://github.com/mirmik/zencad
```

HelloWorld
----------
```python
#!/usr/bin/env python3
#coding: utf-8

from zencad import *

m = box(10,10,10) + sphere(5).translate(5,5,10)

display(m)
show()
```
