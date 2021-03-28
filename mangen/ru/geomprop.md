:ru
# Геометрические характеристики.
Раздел посвящен измерению геометрических характеристик конструируемой геометрии.

Поскольку понятия плотности и масштаба весьма эфемерны для вычислительной библиотеки, все вычисления проводятся в условных единицах. Перевод величин в систему си требует дополнительных вычислений.
:en
# Geometric characteristics.
The section is devoted to measuring the geometric characteristics of the constructed geometry.

Since the concepts of density and scale are very ephemeral for the computational library, all calculations are carried out in arbitrary units. Converting values to the si system requires additional calculations. 
::

----------------------------------------
:ru
## Встроенные методы
Shape имеет ряд методов, позволяющих запросить геометрическую информацию.
:en
## Built-in methods
Shape has a number of methods for querying geometric information. 
::

----
:ru
### Центр масс.
:en
::
```python
shape.center() -> point3
shape.cmradius() -> vector3
```

----
:ru
### Объём.
:en
### Center of mass. 
::
```python
shape.mass() -> float
```

----
:ru
### Матрица инерции.
:en
### Matrix of inertia. 
::
```python
shape.matrix_of_inertia() -> matrix33
```

---
:ru
### Статические моменты.
:en
### Static moments. 
::
```python
shape.static_moments() -> float, float, float
```

---
:ru
### Момент инерции относительно оси.
:en
### Moment of inertia about the axis. 
::
UNDER_CONSTRUCTION

------
:ru
### Радиус инерции.
:en
### Radius of gyration. 
::
UNDER_CONSTRUCTION

-----------------------------------------
:ru
## Измерение систем тел
:en
## Measuring body systems 
::
UNDER_CONSTRUCT
