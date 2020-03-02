# Афинные преобразования.

Парадигма _ZenCad_ предполагает, что большая часть объектов появляется в точке начала координат, после чего перемещается к месту своего назначения с помощью механизма преобразований. 

Обычно, при работе с геометрией, преобразования выполняются с помощью методов класса _Shape_ (представляющего геометрические тела), но для построения сложных преобразований или работы с анимацией афинные преобразования также могут создаваться в качестве обособленных объектов.

Афинные преобразования в _ZenCad_ представлены объектами класса _Transformation_ (однородные преобразования) и класса _GeneralTransformation_ (афинное преобразование общего вида). Объекты этих класов порождаются семейством функций описанных ниже в этом разделе. 

Следует помнить, что преобразования общего вида вычислительно сложнее и могут сильно изменять внутреннее представление геометрического объекта.  
  
С математической точки зрения объекты преобразования является линейными операторами и относительно них допустимы некоторые операции линейной алгебры. Соответствующий функционал библиотеки описан в разделе "Операции над преобразованиями".  

Функции для работы с преобразованиями и специальные виды преобразований описаны в разделе "Дополнительные преобразования".

----------------------------------------------------
## Базовые преобразования.
Существует четыре базовых преобразования: поворот, трансляция, масштабирование и отражение.

----------------------------------------
### Поворот
Поворот тела вокруг оси заданной вектором _v_ и проходящей через начало координат на угол _a_.

Если угол _a_ не указан, то в качестве угла поворота берётся радианная мера, численно равная модулю вектора _v_.

Методы трансформируемых геометрических объектов: 
```python
# Основной синтаксис:
shp.rotate([x,y,z], a=None)
shp.rotate(x,y,z)
shp.rotateX(x)
shp.rotateY(y)
shp.rotateZ(z)

# Сокращенный синтаксис:
shp.rot([x,y,z], a=None)
shp.rot(x,y,z)
shp.rotX(x)
shp.rotY(y)
shp.rotZ(z)
```
Создание объекта трансформации:
```python
rotate([x,y,z], a=None)
rotate(x,y,z)
rotateX(x)
rotateY(y)
rotateZ(z)
```

-----------------------------------------
### Трансляция
Паралельный перенос тела на вектор _(x,y,z)_.
По историческим причинам (в частности для совместимости с OpenScad), в библиотеке zencad есть два синонимичных семейства функций/методов translate и move, а также их мнемонические обозначения.

Методы трансформируемых геометрических объектов: 
```python
# Основной, альтернативный, мнемонический синтаксис:
shp.translate(x=0,y=0,z=0)
shp.translate([x,y,z])
shp.move(x=0,y=0,z=0)
shp.move([x,y,z])
shp.moveX(x)
shp.moveY(y)
shp.moveZ(z)
shp.right(x) # moveX(+x)
shp.left(x)  # moveX(-x)
shp.forw(y)  # moveY(+y)
shp.back(y)  # moveY(-y)
shp.up(z)    # moveZ(+z)
shp.down(z)  # moveZ(-z)

# Сокращенный синтаксис:
shp.movX(x)
shp.movY(y)
shp.movZ(z)
```

Создание объекта трансформации:
```python
# Основной синтаксис:
translate(x=0,y=0,z=0)
translate([x,y,z])

# Альтернативный синтаксис:
move(x=0,y=0,z=0)
move([x,y,z])
moveX(x)
moveY(y)
moveZ(z)

# Мнемонический синтаксис:
right(x) # moveX(+x)
left(x)  # moveX(-x)
forw(y)  # moveY(+y)
back(y)  # moveY(-y)
up(z)    # moveZ(+z)
down(z)  # moveZ(-z)
```

-------------------------------
### Масштабирование
Изменение размера тела на коэффициент a. Может выполняться в направлении заданной оси или изотропно.

Методы трансформируемых геометрических объектов: 
```python
shp.scale(a)
shp.scaleX(a)
shp.scaleY(a)
shp.scaleZ(a)
```

Создание объекта трансформации:
```python
scale(a)
scaleX(a) # general_transformation
scaleY(a) # general_transformation
scaleZ(a) # general_transformation
scaleXYZ(x,y,z) # general_transformation
```

----------------------------------
### Отражение
Операция отражения геометрии относительно точки, оси проходящей через начало координат или плоскости, проходящей через начало координат.

При отражение относительно точки задаются координаты центра трансформации.
При отражение относительно оси задаётся вектор оси трансформации.
При отражение относительно плоскости задаётся вектор нормали отражающей плоскости.

Методы трансформируемых геометрических объектов: 
```python
# Отражение относительно центра.
shp.mirrorO(x=0,y=0,z=0)
shp.mirrorO([x,y,z])

# Отражение относительно оси.
shp.mirror_axis(x,y,z)
shp.mirror_axis([x,y,z])
shp.mirrorX() # equal to mirror_axis(1,0,0)
shp.mirrorY() # equal to mirror_axis(0,1,0)
shp.mirrorZ() # equal to mirror_axis(0,0,1)

# Отражение относительно плоскости.
shp.mirror_plane(x,y,z)
shp.mirror_plane([x,y,z])
shp.mirrorXY() # equal to mirror_axis(0,0,1)
shp.mirrorYZ() # equal to mirror_axis(1,0,0)
shp.mirrorXZ() # equal to mirror_axis(0,1,0)
```

Создание объекта трансформации:
```python
# Отражение относительно центра.
mirrorO(x=0,y=0,z=0)
mirrorO([x,y,z])

# Отражение относительно оси.
mirror_axis(x,y,z)
mirror_axis([x,y,z])
mirrorX() # equal to mirror_axis(1,0,0)
mirrorY() # equal to mirror_axis(0,1,0)
mirrorZ() # equal to mirror_axis(0,0,1)

# Отражение относительно плоскости.
mirror_plane(x,y,z)
mirror_plane([x,y,z])
mirrorXY() # equal to mirror_axis(0,0,1)
mirrorYZ() # equal to mirror_axis(1,0,0)
mirrorXZ() # equal to mirror_axis(0,1,0)
```

-----
## Операции над преобразованиями.

Аффинные преобразования являются линейными операторами и относительно них может быть выполнены некоторые операции линейной алгебры. 

---------------
### Композиция.
Композиции аффинных преобразований выполняются с помощью оператора умножения. 
Следует учесть, что композиции аффинных преобразований некоммутативны.

Композиции преобразований следует читать справа налево. Нпример, в примере ниже, запись `moveX(20) * rotateZ(deg(60))` Означает, что мы сначала совершаем поворот на 60 градусов, а потом делаем паралельный перенос по оси X на 20 единиц.

Пример:
```python
trans = moveX(20) * rotateZ(deg(60))
m = zencad.internal_models.knight()
disp(trans(m))

# alternate: box(5, center=True).rotZ(deg(60).movX(20)
```

| До | После |
|---|---|
| ![complextrans0](../images/generic/complextrans0.png) | ![complextrans1](../images/generic/complextrans1.png) |

-----
### Инверсия.
Вычисление обратного преобразования.

Сигнатура:
```python
trsf.inverse()
```

Пример:
```python
trans = rotateZ(deg(45))
m = zencad.internal_models.knight()
disp(trans(m), color.green)
disp(trans.inverse()(m), color.red)
```
| Преобразование | Инверсия |
|---|---|
| ![invtrans0](../images/generic/invtrans2.png) | ![invtrans1](../images/generic/invtrans3.png) |

Пример:
```python
trans = moveX(20) * rotateZ(deg(45))
m = zencad.internal_models.knight()
disp(trans(m), color.green)
disp(trans.inverse()(m), color.red)
```
| Преобразование | Инверсия |
|---|---|
| ![invtrans0](../images/generic/invtrans0.png) | ![invtrans1](../images/generic/invtrans1.png) |

Примечание. Инверсия композиции преобразований может быть вычеслена как:  
_<p align=center>(A * B)<sup>-1</sup> = B<sup>-1</sup> * A<sup>-1</sup><p/>_


----
## Дополнительные преобразования.

-----------------------------------
### Преобразование само в себя.
Специальное преобразование, никак не изменяющее объект.

```python
nulltrans()
```

| До | После |
|---|---|
| ![nulltrans0](../images/generic/nulltrans01.png) | ![nulltrans0](../images/generic/nulltrans01.png) |

------------------------------------
### Множественное преобразование.
Оператор множественного преобразования создаёт объединение преобразований объекта прототипа.
transes - массив преобразований.
```python
multitrans(transes)
```

Пример:
```python
def extrans(): return multitransform([ 
	translate(-20,20,0) * rotateZ(deg(60)),
    translate(-20,-20,0) * rotateZ(deg(120)),
    translate(20,20,0) * rotateZ(deg(180)),
    nulltrans()
])
disp(extrans(zencad.internal_models.knight()))
```

| До | После |
|---|---|
| ![multitrans0](../images/generic/multitrans0.png) | ![multitrans0](../images/generic/multitrans1.png) |

---------
## Минимальный поворот.
Данное преобразование соответствует минимальному поворота от вектора _f_ к вектору _t_. _f_ - необязательный параметр и по умолчанию соответствует вертикальному направлению.

Сигнатура:
```python
short_rotate(t, f=(0,0,1))
```

----------
## Круговой массив.
Строит круговой массив объектов.

Сигнатура и код преобразования:
```python
def rotate_array(n):
    transes = [
        rotateZ(angle) for angle in np.linspace(0, deg(360), num=n, endpoint=False)
    ]
    return multitrans(transes)
```

## Квадратное отражение.
Достраивает 3 отражения исходного объекта.

Сигнатура и код преобразования:
```python
def sqrmirror():
    return multitransform([nulltrans(), mirrorYZ(), mirrorXZ(), mirrorZ()])
```
