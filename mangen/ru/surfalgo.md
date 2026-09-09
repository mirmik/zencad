:ru
# Классы поверхностей.
:en
# Classes of surfaces. 
::

-----------------
:ru
## Классы поверхностей.
В ZenCad существуют следующие классы поверхностей:
:en
## Surface classes.
The following surface classes exist in ZenCad: 
::

* Face 
* Surface 

--------------------
:ru
## Поиск нормали
Нормаль возвращается как `Vector3` в точке с параметрами _u_, _v_. Для `Face.normal()` параметры по умолчанию равны нулю; для `Surface.normal(u, v)` оба параметра обязательны.
:en
## Find normal
Returns a `Vector3` normal at parameters _u_, _v_. `Face.normal()` defaults both parameters to zero; `Surface.normal(u, v)` requires both parameters.
::

Сигнатура:
```python
face.normal()
surface.normal(0, 0)
```

