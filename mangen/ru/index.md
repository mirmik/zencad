<center><h0>ZenCad.<h0/></center>

<center>
<div class="t0"><p>Скриптовый CAD для праведных прогеров.</p></div>
![](../images/generic/zencad-logo.png)  
</center>

-------------
## Что это?
_ZenCad_ - это библиотека параметрического 3д моделирования. библиотека исповедует идею создания 3д модели путём написания скрипта и ноги её растут из системы _OpenScad_. В отличие от _OpenScad_, библиотека использует геометрическое ядро граничного представления _OpenCascade_ и язык общего назначения _Python_.

_ZenCad_ может использоваться как самостоятельная система быстрого прототипирования для целей макетирования или 3д печати, так и в комплексе с библиотеками экосистемы _Python_, в частности для построения 3д моделий на основе расчетов выполненных в таких системах как scipy и sympy.

--------------
# Быстрый старт.
------------
## Установка.
```sh
python3 -m pip install zencad
```

--------------
## Запуск графической оболочки.
```sh
zencad

# alternate:
python3 -m pip zencad
```

-------------
## HelloWorld
```python
#!/usr/bin/env python3
#coding: utf-8

from zencad import *

box = box(200, 200, 200, center = True)
sphere1 = sphere(120)
sphere2 = sphere(60)

model = box - sphere1 + sphere2

display(model)
show()
```

---------
## Ссылки
github: [https://github.com/mirmik/zencad](https://github.com/mirmik/zencad)  
pypi: [https://pypi.org/project/zencad](https://pypi.org/project/zencad)  

