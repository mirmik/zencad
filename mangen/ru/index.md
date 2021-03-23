<center><h0>ZenCad.<h0/></center>

:ru
<center>
<div class="t0"><p>Скриптовый CAD для праведных прогеров.</p></div>
![](../images/generic/zencad-logo.png)  
</center>
:en
<center>
<div class="t0"><p>Script CAD for righteous programmers.</p></div>
![](../images/generic/zencad-logo.png)  
</center>
::

-------------
:ru
## Что это?
_ZenCad_ - это библиотека параметрического 3д моделирования. библиотека исповедует идею создания 3д модели путём написания скрипта и ноги её растут из системы _OpenScad_. В отличие от _OpenScad_, библиотека использует геометрическое ядро граничного представления _OpenCascade_ и язык общего назначения _Python_.

_ZenCad_ может использоваться как самостоятельная система быстрого прототипирования для целей макетирования или 3д печати, так и в комплексе с библиотеками экосистемы _Python_, в частности для построения 3д моделий на основе расчетов выполненных в таких системах как scipy и sympy.
:en
## What is ZenCad?
_ZenCad_ is a library for parametric 3D modeling. the library adheres to the idea of ​​creating a 3D model by writing a script and its legs grow from the _OpenScad_ system. Unlike _OpenScad_, the library uses the geometrical core of the boundary representation _OpenCascade_ and the general-purpose language _Python_.

_ZenCad_ can be used as an independent rapid prototyping system for prototyping or 3D printing purposes, and in combination with the libraries of the _Python_ ecosystem, in particular for building 3D models based on calculations performed in such systems as scipy and sympy. 
::

--------------
:ru
# Быстрый старт.
:en
# Fast start.
::

------------
:ru
## Установка.
:en
## Install.
::
```sh
python3 -m pip install zencad
```

--------------
:ru
## Запуск графической оболочки.
:en
## Graphic user intrface.
::
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
:ru
## Ссылки
:en
## References
::
github: [https://github.com/mirmik/zencad](https://github.com/mirmik/zencad)  
pypi: [https://pypi.org/project/zencad](https://pypi.org/project/zencad)  

