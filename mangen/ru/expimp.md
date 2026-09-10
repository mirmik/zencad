# Экспорт и импорт

Экспорт вычисляет геометрию и записывает файл; `show()` и графический интерфейс не нужны.

| Формат | Что сохраняется | Запись | Чтение |
| --- | --- | --- | --- |
| STL | Треугольная сетка без единиц измерения | `export_stl` | Через сторонние библиотеки, например trimesh |
| STEP | Точная BREP-геометрия и единицы | `export_step` | Нет |
| 3MF | Сетка, единицы и метаданные | `export_3mf` | Нет |
| BREP | Геометрия OpenCascade | `to_brep` | `from_brep` |
| SVG | Плоская геометрия, поддержка ограничена | `to_svg` | `from_svg` |

## STL, STEP и 3MF

```python
import zencad as z

part = z.box(20) - z.cylinder(4, 20).translate(10, 10, 0)
z.export_stl(part, "part.stl", binary=True)
z.export_step(part, "part.step", unit="mm")
z.export_3mf(part, "part.3mf", unit="mm", name="Bracket")
```

Экспортёры считают исходные координаты миллиметрами. `unit` выбирает единицы файла: `mm`, `cm`, `m`, `um`, `in`, `ft` или полные имена. Например, при `unit="cm"` размер 20 записывается как 2 сантиметра. STL не хранит единицы: в нём меняется только масштаб координат.

`linear_tolerance` и `angular_tolerance` управляют детализацией сетки STL/3MF. Линейный допуск задаётся в единицах файла; меньший допуск даёт более мелкую сетку. STEP не требует триангуляции.

Вместо пути можно передать бинарный поток:

```python
import io
import zencad as z

stream = io.BytesIO()
z.export_step(z.box(10), stream)
assert stream.getvalue().startswith(b"ISO-10303-21")
```

Невалидная форма вызывает `ShapeValidationError`, ошибка записи — `OSError`. `to_stl(model, path, delta)` — короткий вариант экспорта в ASCII STL; `delta` задаёт детализацию, при успехе возвращается `True`.

## BREP

```python
import zencad as z

z.to_brep(z.box(3), "part.brep")
restored = z.from_brep("part.brep")
restored.assert_valid()
```

## SVG

Для файлов используются `to_svg(model, path)` и `from_svg(path)`. Для обмена строками — `to_svg_string(model)` и `from_svg_string(svg)`.

```python
import zencad as z

svg = z.to_svg_string(z.rectangle(20, 10))
restored = z.from_svg_string(svg)
restored.assert_valid()
```

SVG работает с плоской геометрией; поддерживаются не все типы кривых. Пример импорта малополигонального STL через trimesh находится в `zencad/examples/Integration/trimesh`. [Подробности экспорта](../development/export-formats.md).
