:ru
# Экспорт и импорт

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
:en
# Export and import

Export is an explicit evaluation boundary: the shape is materialized, validated and written. Qt and `show()` are not required.

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

| Format | Stored data |
| --- | --- |
| STL | Triangle mesh; no unit metadata, so coordinates are scaled |
| STEP | Exact BREP geometry and units; ISO-10303-21 text |
| 3MF | Mesh, units and metadata; binary ZIP container |
| BREP | Native OCCT geometry through `to_brep`/`from_brep` |

STL/STEP/3MF accept a path or binary stream with `write(bytes)`. Units include `mm`, `cm`, `m`, `um`, `in`, `ft` and their full names. Internal geometry uses millimetres. `linear_tolerance` and `angular_tolerance` control STL/3MF meshing; STEP requires no tessellation. Linear tolerance uses export units.

Invalid shapes raise `ShapeValidationError`; write failures raise `OSError` with format and destination context. `to_stl(shape, path, delta)` remains an ASCII compatibility facade returning `True` on success.

```python
import zencad as z

z.to_brep(z.box(3), "part.brep")
restored = z.from_brep("part.brep")
restored.assert_valid()
```

SVG uses `to_svg`/`to_svg_string` and `from_svg`/`from_svg_string`. STEP/3MF export does not imply matching import support. [Full export contract](../development/export-formats.md).
::
