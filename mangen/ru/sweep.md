:ru
# Траекторная развёртка.

Широкий класс операций ссылочной геометрии представляют операции, построения тела путём трансляции (англ. sweep) некоторого профиля или семейства профилей (_profile_, _profiles_) вдоль заданной траектории _spine_.

## Формально о том, что такое траекторная развёртка:

Траекторная развёртка - это методика построения поверхности путём протягивания профиля вдоль траектории. В общем случае вид профиля непостояннен и может меняться по определённым законам. Таким образом, относительно того, как профиль протягивается вдоль траектории существует два вопроса, или, иными словами, мы должны определить два закона, а именно:

1. Закон, определяющий форму траектории.
2. Закон определяющий форму профиля.

Второй закон удобно разбить на два подзакона: 
1.1. Закон, определяющий форму транслируемого тела.
1.2. Закон, определяющий угловую эволюцию базиса.

По сути, многообразие всех имеющихся в системе операций траекторной трансляции - суть разные формы ответов на эти вопросы. 
:en
# Trajectory sweep.

A wide class of reference geometry operations is represented by operations, constructing a body by translation (English sweep) of a certain profile or a family of profiles (_profile_, _profiles_) along a given trajectory _spine_.

## Formally about what a trajectory sweep is:

Trajectory sweep is a technique for constructing a surface by sweeping a profile along a path. In general, the profile view is not constant and can change according to certain laws. Thus, there are two questions regarding how the profile extends along the trajectory, or, in other words, we must define two laws, namely:

1. The law that determines the shape of the trajectory.
2. The law determining the shape of the profile.

It is convenient to split the second law into two sub-laws:
1.1. The law that determines the shape of the translated body.
1.2. The law governing the angular evolution of the basis.

In fact, the variety of all trajectory translation operations available in the system are different forms of answers to these questions.
::

----------------------

:ru
## Линейная развёртка.
Самый часто используемый метод придания объёма плоскому объекту. Операция разворачивает плоское тело _face_ по вектору _vec_. Если вместо вектора указать одну координату, модель будет вытянута в положительном направлении оси Z.
При указании опции center, после выполнения операции модель будет транслирована в направлении обратном vec на его половинную длину.
:en
## Linear sweep.
The most commonly used method of adding volume to a flat object. The operation unfolds the flat body _face_ along the vector _vec_. Specifying a single coordinate instead of a vector will stretch the model in the positive Z direction.
If the center option is specified, after the operation is performed, the model will be translated in the direction opposite to vec by its half length.
::

Сигнатура:
```python
extrude(proto=face, vec=(x,y,z), center=True/False)
extrude(proto=face, vec=z, center=True/False) #equal: vec=(0,0,z)
face.extrude(vec) #alternate
```

Пример:
```python
ngon(r=10, n=10)
ngon(r=10, n=10).extrude(4)
extrude((1, 0, 4), ngon(r=10, n=10))
extrude(textshape(text="TextShape", fontpath=FONTPATH, size=100), 20)
```

![](../images/generic/extrude0.png) ![](../images/generic/extrude1.png) </br>  
![](../images/generic/extrude2.png) ![](../images/generic/extrude3.png)

--------------------------
:ru
## Труба.
Строит на основе траектории _spine_ и профиля круглого сечения радиуса _r_.
_maxdegree_ максимальная степень bspline поверхности.
_maxsegm_ - ?
_bounds_ - при установке этой опции операция возвращает кортеж из резултьата, а также профилей в первой и последней позициях.
:en
## Trumpet.
Draws on the path _spine_ and the circular profile of the radius _r_.
_maxdegree_ is the maximum bspline degree of the surface.
_maxsegm_ -?
_bounds_ - when this option is set, the operation returns a tuple from the result, as well as the profiles in the first and last positions.
::

Сигнатура:
```python
tube(spine, r, tol=1e-6, cont=2, maxdegree=3, maxsegm=20, bounds=False):
```

Примеры:
```python
POINTS = [ (0,0,0), (0,0,20), (0,20,40),
	(-90,20,40), (-90,20,20), (0,20,0) ]
spine = rounded_polysegment(POINTS, r=10)
a = tube(spine, r=5) 

POINTS = [ (0,0,0), (20,0,40) ]
TANGS = [ (0,0,1), (1,0,1) ]
spine = interpolate(POINTS, TANGS)
b = tube(spine, r=5, maxdegree=8)
```
![](../images/generic/tube0.png) ![](../images/generic/tube1.png)

---
:ru
## Развёртка профиля по траектории. Развёртка с изменяемым профилем.
Операция строит тело по одному профилю или набору сменяющих друг друга профилей _profiles_, вытянутых по траектории _spine_.
Указание опции _frenet_ активирует закон изменения углового положения профиля в соответствии с трёхгранником Френе-Серре. Опция _binormal_ активирует закон изменения углового положения профиля в соответствии с константной бинормалью.
:en
## Sweep a profile along a path. Sweep with a variable profile.
The operation constructs a body from one profile or a set of successive _profiles_ profiles, stretched along the _spine_ path.
Specifying the _frenet_ option activates the law of variation of the angular position of the profile in accordance with the Frenet-Serre trihedron. The _binormal_ option activates the law of variation of the angular position of the profile in accordance with the constant binormal.
::

Сигнатура:
```python
pipe_shell(profiles, spine, frenet=False, binormal=vector3(0,0,0), solid=True)
```

Примеры:
```python
```

![](../images/generic/sweep0.png) ![](../images/generic/sweep1.png)  </br>
![](../images/generic/sweep2.png) ![](../images/generic/sweep3.png)  </br>
![](../images/generic/sweep4.png)

---
:ru
## Тело вращения.
Операция создания тела вращения от прототипа _proto_. При необходимости создания сектора задаётся угол _yaw_.
Если указан радиус _r_, объект разворачивается на 90 градусов вокруг оси X и смещается по оси X на растояние равное радиусу _r_.
:en
## Body of rotation.
The operation of creating a body of revolution from the _proto_ prototype. If it is necessary to create a sector, the angle _yaw_ is set.
If radius _r_ is specified, the object is rotated 90 degrees around the X axis and displaced along the X axis by a distance equal to the radius _r_.
::

Сигнатура:
```python
revol(profile, r=None, yaw=deg(360))
```

Пример:
```python
```

![](../images/generic/revol0.png) ![](../images/generic/revol1.png)  </br>
![](../images/generic/revol2.png) ![](../images/generic/revol3.png)  

---
:ru
## Тело вращения. (расширенная версия).
Расширенная версия операции _revol_. Строит тело вращения от прототипа _proto_ на интервале угла поворота _yaw_. Указание опции _roll_ позволяет изменять угол поворота прототипа по мере прохождения интервала. Тело строится по опорным копиям тела прототипа, количество копий задаётся опцией _n_. _nparts_ определяет количество сегментов результирующего тела вращения.
:en
## Body of rotation. (extended version).
An extended version of the _revol_ operation. Constructs a body of revolution from the prototype _proto_ at the interval of the rotation angle _yaw_. Specifying the _roll_ option allows you to change the rotation angle of the prototype as it traverses the interval. The body is built from reference copies of the prototype body, the number of copies is set by the _n_ option. _nparts_ defines the number of segments of the resulting rotation body.
::

Сигнатура:
```python
revol2(profile, r, n=30, yaw=(0,deg(360)), roll=(0,0), nparts=None)
```

Примеры:
```python
revol2(profile=square(10, center=True), r=20, n=60, yaw=(0,deg(360)), roll=(0,deg(360)))
```

![](../images/generic/revol20.png)
