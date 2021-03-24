:ru
# Анализ кривых
:en
# Curve analysis 
::

-------------------------
:ru
## Теоретическая сводка.
Общепризнанным методом задания кривых в системах вычислительной геометрии является параметрический метод.

Согласно ему кривая задана непрерывным отображением скалярного множества _[U\_min, U\_max]_ на пространство заданной мерности.
_P = F(U) : P ∈ R^N, U ∈ R^1[U\_min, U\_max]_, где _F_ - функтор отображения, а _N_ - мерность пространства.

На практике это означает, что любая точка _P_ на кривой имеет соответствующее ей значение скалярного параметра _U_. Следует понимать, что в общем случае функция связывающая параметр _U_ в точке _P_ и длину кривой из точки начала _O_ до точки _P_ не линейна. Поэтому вычисления над кривой в терминах длин требуют применения специального математического аппарата (реализованного в виде методов настоящей библиотеки).
:en
## Theoretical summary.
The generally accepted method for defining curves in computational geometry systems is the parametric method.

According to him, the curve is given by a continuous mapping of the scalar set _[U \_min, U \_max]_ onto a space of a given dimension.
_P = F (U): P ∈ R ^ N, U ∈ R ^ 1 [U \_min, U \_max]_, where _F_ is the mapping functor and _N_ is the dimension of the space.

In practice, this means that any point _P_ on the curve has a corresponding value of the scalar parameter _U_. It should be understood that, in the general case, the function connecting the parameter _U_ at the point _P_ and the length of the curve from the start point _O_ to the point _P_ is not linear. Therefore, calculations over a curve in terms of lengths require the use of a special mathematical apparatus (implemented in the form of methods in this library). 
::

-----------------
:ru
## Классы кривых.
В ZenCad существуют следующие классы реализующие методы анализа кривых:

* Edge (порождается инструментами segment, interpolate, bezier, bspline и т.д.)
* Curve
* Curve2
:en
## Classes of curves.
ZenCad has the following classes that implement curve analysis methods:

* Edge (spawned by segment, interpolate, bezier, bspline, etc.)
* Curve
* Curve2 
::

---
:ru
## Крайние точки и диапазон конечной кривой.
Определение концевых точек конечных кривых.

Метод _endpoints_ возвращает объекты крайних точек. 
Параметры этих точек могут быть запрошены методом _range_.
:en
## End points and end curve range.
Determines the endpoints of the end curves.

The _endpoints_ method returns endpoint objects.
The parameters of these points can be queried using the _range_ method. 
::

```python 
curve.endpoints() -> point3, point3
curve.range() -> float, float
```

```python
crv = circle(r=5, wire=True, angle=deg(270))
s,f = crv.endpoints()
disp([crv, s, f])
```
![](../images/generic/endpoints0.png)

-----------------
:ru
## curve.length()
Вернуть длину кривой между параметрами _U\_min_ и _U\_max_.
:en
## curve.length ()
Return the length of the curve between the _U \ _min_ and _U \ _max_ parameters. 
::

--------------
:ru
## curve.d0(u)
Вернуть точку, соответствующую параметру _u_.
:en
## curve.d0 (u)
Return the point corresponding to the _u_ parameter. 
::

---------------
:ru
## curve.d1(u)
Вернуть вектор первой производной, соответствующие параметру _u_.
:en
## curve.d1 (u)
Return the vector of the first derivative matching the _u_ parameter. 
::

------------------------
:ru
## curve.linoff(u, dist)
Вернуть параметр точки, смещенной на длину _dist_ относительно точки задаваемой параметром _u_.
:en
## curve.linoff (u, dist)
Return the parameter of the point offset by the length _dist_ relative to the point specified by the _u_ parameter. 
::

------------------------------
:ru
## curve.linoff_point(u, dist)
Вернуть точку, смещенную на длину dist относительно точки задаваемой параметром _u_.  
alternate: `curve.d0(curve.linoff(u,dist))`
:en
## curve.linoff_point (u, dist)
Return the point offset by the length dist relative to the point specified by the _u_ parameter. 
::

:ru
## curve.project(pnt)
Вернуть параметр, соответствующий точке кривой наиболее близкой к точке pnt. 
:en
## curve.project (pnt)
Return the parameter corresponding to the point on the curve closest to the point pnt. 
::

-------------------------------------------
:ru
## Равнораспределённые точки кривой.
Вернуть массив точек, равномерно распределённых на кривой. Параметр _npnts_ - задаёт количество точек.
Параметры umin, umax задают диапазон на множестве параметров в котором будет проведена процедура распределения.
:en
## Equidistant curve points.
Return an array of points equally spaced along the curve. The _npnts_ parameter sets the number of points.
The parameters umin, umax set the range on the set of parameters in which the distribution procedure will be carried out. 
::

```python3
curve.uniform(npnts, umin=U_min, umax=U_max) -> list(float) 
curve.uniform_points(npnts, umin=U_min, umax=U_max) -> list(point3) 
```  

```python
crv = circle(r=5, wire=True, angle=deg(270))

params = crv.uniform(8, math.pi/4, math.pi)
print(params) # [0.7853981633974483, 1.121997376282069, 1.4585965891666897, 1.7951958020513104, 2.131795014935931, 2.4683942278205517, 2.8049934407051724, 3.141592653589793]

pnts = crv.uniform_points(8, math.pi/4, math.pi)
disp(pnts + [crv])
```

![](../images/generic/uniform_points0.png)