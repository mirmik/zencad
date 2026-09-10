# Экспорт/Импорт

Операции экспорта/импорта отличаются от большинства операций библиотеки zencad тем, что производятся не только над объектами в памяти программы, но и над файлами.

---
## STL
Создать файл мешсети формата STL, находящийся по пути `path`, из твердотельной модели `model`.
Параметр `delta` определяет степень детализации. Чем меньше `delta`, тем меньше размер полигонов.
```python3
to_stl(model, path, delta)
```

Импортирование МАЛОПОЛИГОНАЛЬНЫХ stl и прочих форматов mesh сетей возможно с применением сторонних библиотек, таких как trimesh. (см. examples/Integration/trimesh)

---
## BREP
Создать файл brep представления формата BREP, находящийся по пути `path`, из твердотельной модели `model`.
```python3
to_brep(model, path)
```

Считать файл brep представления формата BREP, находящийся по пути `path`. Вернуть полученную модель.
```python3
m = from_brep(path)
```

---
## SVG
Поддержка ограничена. Поддерживаются не все типы кривых.

Создать/считать svg файл из плоского тела `model`, находящийся по пути `path`.

```python3
to_svg(model, path)
model = from_svg(path)
```

Создать/считать строку svg представления плоского тела `model`.

```python3
svg = to_svg_string(model)
model = from_svg_string(svg)
```



## Экспорт STL, STEP и 3MF

Экспорт — явная граница вычисления: форма материализуется, валидируется и записывается. Qt и вызов `show()` не нужны.

```python
import io
import zencad as z

part = z.box(20) - z.cylinder(4, 20).translate(10, 10, 0)
z.export_stl(part, "part.stl", binary=True)
z.export_step(part, "part.step", unit="mm")
z.export_3mf(part, "part.3mf", unit="mm", name="Bracket")
stream = io.BytesIO()
z.export_step(part, stream)
assert stream.getvalue().startswith(b"ISO-10303-21")
```

| Формат | Что сохраняется |
| --- | --- |
| STL | Треугольная сетка; формат не хранит единицы, координаты масштабируются |
| STEP | Точная BREP-геометрия и единицы; текст ISO-10303-21 |
| 3MF | Сетка, единицы и метаданные; бинарный ZIP-контейнер |
| BREP | Native-геометрия OCCT для обмена через `to_brep`/`from_brep` |

STL/STEP/3MF принимают путь или бинарный поток с `write(bytes)`. Единицы: `mm`, `cm`, `m`, `um`, `in`, `ft` и полные имена. Внутренняя геометрия — в миллиметрах. `linear_tolerance` и `angular_tolerance` управляют сеткой STL/3MF; STEP не требует тесселяции. Линейный допуск задаётся в единицах экспорта.

Невалидная форма вызывает `ShapeValidationError`, ошибка записи — `OSError` с контекстом формата и назначения. `to_stl(shape, path, delta)` остаётся совместимым ASCII-фасадом с `True` при успехе.

```python
import zencad as z

z.to_brep(z.box(3), "part.brep")
restored = z.from_brep("part.brep")
restored.assert_valid()
```

SVG доступен через `to_svg`/`to_svg_string` и `from_svg`/`from_svg_string`. Наличие экспортёра STEP/3MF не означает наличия симметричного импортёра этих форматов. [Полный контракт экспорта](../development/export-formats.md).
