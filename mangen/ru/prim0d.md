# Точка, вектор, вспомогательные функции.

В библиотеки ZenCad есть некоторые вспомогательные математические объекты и функции для работы с ними.

---
## Точка
Некоторые функции ZenCad используют в качестве параметров точки или массивы точек. Для создания объекта точки можно использовать функцию `point3`. Кроме того, часто функция может сама сформировать точки по списку или кортежу координат.

```python
point3(0,3,6)

#Equivalent calls
interpolate([point3(0,0,0), point3(0,0,10), point3(10,0,10)])
interpolate([(0,0,0), (0,0,10), (10,0,10)])
interpolate(points([(0,0,0), (0,0,10), (10,0,10)]))
```

Точка может быть отображена функцией display, как соответствующая такой точке вершина.

---
## Вектор
Иногда кроме указаний точек используются объекты-векторы для указания направлений. Принцип работы с векторами аналогичен работе с точками.

```python
vector3(1,2,3)

interpolate(pnts=[(0,0,0), (0,0,10), (10,0,10)], tangs=[(0,0,1), (1,0,0), (0,1,0)])
```

Вектор не может быть отображен непосредственно.  
В отличии от точки вектор игнорирует трансляцию при преобразованиях.

---
## Масивы точек и векторов
Функции vectors и points явно создают массивы точек из массивов координат.
points2 создаёт двумерный массив точек из двумерного списка.

```python
points([(0,0,0), (0,0,10), (10,0,10)])
vectors([(0,0,1), (1,0,0), (0,1,0)])

points2([
	[(0,0,0), (0,0,10), (10,0,10)],
	[(1,6,0), (0,5,10), (10,5,10)]
])
```

---
## Операции над точками и векторами
Точки и вектора могут использоваться в математических операциях в соответствиями с правилами линейной алгебры.

```python
pnt - pnt # -> vec
pnt + vec # -> pnt
vec + vec # -> vec
vec - vec # -> vec
```

---
## Пустое примитив. nullshape
Пустой примитив. Может участвовать в булевых операциях.  

Пример использования в цикле:
```python
it = nullshape()
for i in range(7):
	it = it + box(20).translate(10*i,10*i,10*i)

#alternate: union([box(20).translate(10*i,10*i,10*i) for i in range(7)])
```

---
## Перевод угловых величин. Радианы и градусы
API zencad использует радианы для задания углов. Использование градусов требует масштабирования численного коэффициента. Именно этим и занимается функция deg (синоним deg2rad):  
`deg(180)` соответствует `math.pi`.

Обратное преобразование выполняется функцией rad2deg.

Сигнатуры:
```python
# Convert degrees to radians:
deg2rad(grad)
deg(grad)

# Convert radians to degrees:
rad2deg(rad)
```

Код функции deg2rad, rad2deg:
```python
def deg2rad(grad):
    return float(grad) / 180.0 * math.pi

def rad2deg(rad):
    return float(rad) * 180.0 / math.pi
```

Пример:
```python
rotateZ(deg(45))
```

---
### Зарегистрировать шрифт
Регистрирует в системе шрифт в формате FreeType.

```python
register_font(fontpath)
```


## Доменные значения и вычисления

`scalar`, `point2`, `point3`, `vector2`, `vector3`, `quaternion` и `transform` создают числа, точки, векторы, кватернионы и преобразования. Результаты имеют типы `Scalar`, `Point2`, `Point3`, `Vector2`, `Vector3`, `Quaternion` и `Transform` соответственно. Формы и численные зависимости сохраняются в графе до явного запроса результата.

```python
import zencad as z

p = z.point3(1, 2, 3)
v = z.vector3(4, 0, 0)
q = p + v
assert q.value() == (5, 2, 3)
assert isinstance(q - p, z.Vector3)
assert isinstance(v + v, z.Vector3)
coordinates = q.to_numpy()
assert coordinates.shape == (3,)
body = z.box(2)
volume = body.mass()
assert isinstance(volume, z.Scalar)
assert abs(volume.value() - 8) < 1e-7
assert isinstance(body.center().x, z.Scalar)
```

Координаты можно задавать числами, а поддерживаемые операции принимают зависимые `Scalar`. `Point + Point` запрещено. Масштабирование вектора даёт вектор; перенос действует на точку, но не на направление.

```python
import zencad as z

number = z.scalar(2)
p2 = z.point2(1, 2)
p3 = z.point3(1, 2, 3)
v2 = z.vector2(1, 0)
v3 = z.vector3(0, 0, 1)
rotation = z.quaternion(0, 0, 0, 1)
placement = z.transform()
assert placement(p3).value() == p3.value()
```

## Когда начинается вычисление

- `Scalar.value()`, `float()`, `int()`, `bool()` и сравнения требуют число.
- `Point/Vector.value()` возвращает кортеж; `.to_numpy()` — массив чисел.
- `Shape.native()` возвращает OCP-форму; `Point/Vector.to_ocp()` — native точку/вектор.

Обычный `math.sin(scalar)` получает число через `float`; `z.sin(scalar)` сохраняет зависимость в графе. Доменные значения логически неизменяемы: новую позицию создают операцией, а не присваиванием координате.
