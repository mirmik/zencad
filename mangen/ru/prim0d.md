# Значения, точки и преобразования

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
- `Transform.matrix()` возвращает числовую матрицу 4×4.

Обычный `math.sin(scalar)` получает число через `float`; `z.sin(scalar)` сохраняет зависимость в графе. Доменные значения логически неизменяемы: новую позицию создают операцией, а не присваиванием координате.

## Преобразования

```python
import zencad as z

move = z.translate(10, 0, 0)
turn = z.rotateZ(z.deg(90))
combined = move * turn
p = combined(z.point3(1, 0, 0))
assert abs(float(p.x) - 10) < 1e-7
assert abs(float(p.y) - 1) < 1e-7
matrix = combined.matrix()
```

`outer * inner` сначала применяет `inner`, затем `outer`. `Transform` описывает перенос, вращение и равномерный масштаб, включая отражения через знаковый масштаб; для общего аффинного преобразования есть отдельный `AffineTransform`. [Селекторы топологии](selectors.html).
