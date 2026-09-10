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

----------------------

## Линейная развёртка.
Самый часто используемый метод придания объёма плоскому объекту. Операция разворачивает плоское тело _face_ по вектору _vec_. Если вместо вектора указать одну координату, модель будет вытянута в положительном направлении оси Z.
При указании опции center, после выполнения операции модель будет транслирована в направлении обратном vec на его половинную длину.

Сигнатура:
```python
extrude(face, (x,y,z), center=False)
extrude(face, z, center=False) #equal: vec=(0,0,z)
face.extrude(vec) #alternate
```

Пример:
```python
ngon(r=10, n=10)
ngon(r=10, n=10).extrude(4)
extrude(ngon(r=10, n=10), (1, 0, 4))
register_font(FONTPATH)
extrude(textshape(text="TextShape", fontname=FONTNAME, size=100), 20)
```

![](../images/generic/extrude0.png) ![](../images/generic/extrude1.png) </br>  
![](../images/generic/extrude2.png) ![](../images/generic/extrude3.png)

--------------------------
## Труба
Круглый профиль можно протянуть по траектории с помощью `pipe_shell`. Полая труба получается вычитанием двух развёрток. Профиль располагают у начала траектории в плоскости, перпендикулярной её начальному направлению.

```python
from zencad import *

spine = interpolate(
    points([(0, 0, 0), (0, 0, 35), (20, 0, 55), (45, 15, 65)]),
    tangs=[vector3(0, 0, 1), None, None, vector3(1, 1, 0)],
)
outer = pipe_shell([circle(3, wire=True)], spine, frenet=True)
inner = pipe_shell([circle(2, wire=True)], spine, frenet=True)
body = outer - inner
body.assert_valid()
disp(body)
```

![](../images/generic/tube0.png) ![](../images/generic/tube1.png)

---
## Развёртка профиля по траектории. Развёртка с изменяемым профилем.
Операция строит тело по одному профилю или набору сменяющих друг друга профилей _profiles_, вытянутых по траектории _spine_.
Указание опции _frenet_ активирует закон изменения углового положения профиля в соответствии с трёхгранником Френе-Серре. Опция _binormal_ активирует закон изменения углового положения профиля в соответствии с константной бинормалью.

Сигнатура:
```python
pipe_shell(profiles, spine, frenet=False, binormal=None, solid=True)
```

Примеры:
```python
spine = segment((0, 0, 0), (0, 0, 40))
profiles = [circle(10, wire=True), circle(5, wire=True).up(40)]
body = pipe_shell(profiles, spine)
```

![](../images/generic/sweep0.png) ![](../images/generic/sweep1.png)  </br>
![](../images/generic/sweep2.png) ![](../images/generic/sweep3.png)  </br>
![](../images/generic/sweep4.png)

---
## Тело вращения.
Операция создания тела вращения от прототипа _proto_. При необходимости создания сектора задаётся угол _yaw_.
Если указан радиус _r_, объект разворачивается на 90 градусов вокруг оси X и смещается по оси X на растояние равное радиусу _r_.

Сигнатура:
```python
revol(profile, r=None, yaw=deg(360))
```

Пример:
```python
profile = rectangle(5, 12).rotateX(deg(90)).right(15)
body = revol(profile)
sector = revol(profile, yaw=deg(120))
```

![](../images/generic/revol0.png) ![](../images/generic/revol1.png)  </br>
![](../images/generic/revol2.png) ![](../images/generic/revol3.png)  

---
## Тело вращения. (расширенная версия).
Расширенная версия операции _revol_. Строит тело вращения от прототипа _proto_ на интервале угла поворота _yaw_. Указание опции _roll_ позволяет изменять угол поворота прототипа по мере прохождения интервала. Тело строится по опорным копиям тела прототипа, количество копий задаётся опцией _n_. _parts_ определяет количество сегментов результирующего тела вращения.

Сигнатура:
```python
revol2(profile, r, n=30, yaw=(0,deg(360)), roll=(0,0), parts=None)
```

Примеры:
```python
revol2(profile=square(10, center=True), r=20, n=60, yaw=(0,deg(360)), roll=(0,deg(360)))
```

![](../images/generic/revol20.png)

## Типы результатов

`extrude()` и `revol()` возвращают `Shape`; форму с единственным телом можно извлечь через `result.solids().only()`. `pipe_shell(..., solid=True)` возвращает `Solid` и требует замкнутых профилей; открытый профиль вызывает `ValueError` при вычислении, с указанием его номера. При `solid=False` результат имеет тип `Shell`, допустимы открытые профили. `revol2()` с параметрами приведённого примера возвращает `Solid`.

<a id="sweep-surface"></a>

## Параметрическая поверхность: sweep_surface

`sweep_surface(section, spine)` протягивает кривую-профиль вдоль кривой-траектории и возвращает `Surface`. Это поверхность для дальнейших построений и измерений; для готового тела используйте `pipe_shell`.

В примере круг радиусом 3 движется по окружности радиусом 12. Поверхность показана сеткой изолиний:

```python
from zencad import *

surface = sweep_surface(circle_curve(3), circle_curve(12))
u = surface.u_range()
v = surface.v_range()

for i in range(12):
    value = u.lower + (u.upper - u.lower) * i / 12
    display(surface.u_iso(value).edge(v)).set_color(blue, wire_color=blue)
for i in range(8):
    value = v.lower + (v.upper - v.lower) * i / 8
    display(surface.v_iso(value).edge(u)).set_color(green, wire_color=green)
show()
```

![Изолинии поверхности круговой развёртки](../images/surface-sweep.png)

Параметр `scale` масштабирует профиль. `trihedron` задаёт способ его ориентации вдоль траектории: по умолчанию используется `SweepTrihedron.CORRECTED_FRENET`, доступен также `SweepTrihedron.FRENET`.
