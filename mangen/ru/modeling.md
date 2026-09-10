# Построение и разделение тел

Примитивы создаются модульными функциями: `box`, `sphere`, `cylinder`, `cone`, `torus`. Формы можно переносить, вращать, объединять (`+`), вычитать (`-`) и пересекать (`^`). Плоскую форму вытягивает `extrude`; для профилей и траекторий доступны `loft`, `revol`, `pipe_shell` и `sweep`. Условия применимости зависят от топологии входов.

```python
import zencad as z

outer = z.box(20, 10, 4)
hole = z.cylinder(2, 4).translate(10, 5, 0)
part = outer - hole
assert isinstance(part, z.Shape)
part.assert_valid()
```

## Split и slice

`split` разбивает тело инструментами и возвращает коллекцию частей. `slice` делит плоскостью и возвращает нижнюю/верхнюю части для горизонтального среза:

```python
import zencad as z

body = z.box(30, 20, 12)
parts = z.split(body, (z.infplane().up(4), z.infplane().up(8)))
assert len(parts) == 3
assert abs(sum(float(part.mass()) for part in parts) - 7200) < 1e-6
lower, upper = z.slice(z.box(20, center=True), z=0)
assert abs(float(lower.mass()) - 4000) < 1e-6
assert abs(float(upper.mass()) - 4000) < 1e-6
```

Для скругления/фаски отдельных рёбер и уклона граней используйте [селекторы](selectors.html). Проверяйте результат через [validate](validation.html), а не только по изображению. Примеры более сложных sweep и loft сохранены в `zencad/examples/2.Operations/3.Sweep` и `zencad/examples/2.Operations/2.Operations/loft.py`.
