:ru
# Проверка и исправление геометрии

```python
import zencad as z

body = z.box(10) + z.box(10).right(10)
report = body.validate()
assert report.valid
print(report.to_dict())
body.assert_valid()
cleaned = body.clean()
healed = cleaned.heal(tolerance=1e-7, max_tolerance=1e-3)
healed.assert_valid()
```

`validate()` вычисляет форму и возвращает `ValidationReport`: `valid` и структурированные ошибки с `code`, `occt_status`, `path`, типом формы и, при необходимости, контекстом. `is_valid()` даёт краткий ответ, `assert_valid()` возвращает ту же форму или выбрасывает `ShapeValidationError`.

Проверка не исправляет геометрию. `clean()` удаляет избыточные границы одной поверхности; `heal()` выполняет ограниченное допусками исправление OCCT. Обе операции создают новый результат, не изменяя исходник. `heal()` не гарантирует успеха — проверяйте возвращённую форму. `sew()` остаётся отдельной операцией сшивки.

Валидная открытая оболочка не обязательно является замкнутым телом. Для замкнутости используйте `is_closed()`, для автоматической проверки итогового тела — `zencad check model.py --valid --solid`. [Headless workflow](headless.html), [формат отчёта](../development/shape-validation.md).
:en
# Geometry validation and repair

```python
import zencad as z

body = z.box(10) + z.box(10).right(10)
report = body.validate()
assert report.valid
print(report.to_dict())
body.assert_valid()
cleaned = body.clean()
healed = cleaned.heal(tolerance=1e-7, max_tolerance=1e-3)
healed.assert_valid()
```

`validate()` materializes the shape and returns a `ValidationReport`: `valid` and structured issues with `code`, `occt_status`, `path`, shape type and optional context. `is_valid()` provides a short answer; `assert_valid()` returns the same shape or raises `ShapeValidationError`.

Validation does not repair geometry. `clean()` removes redundant same-domain boundaries; `heal()` applies tolerance-bounded OCCT healing. Both create a new result without mutating the source. Healing is best-effort: validate its result. `sew()` remains a separate sewing operation.

A valid open shell is not necessarily a closed solid. Use `is_closed()` for closure, or `zencad check model.py --valid --solid` for automated checks of the final body. [Headless workflow](headless.html), [report format](../development/shape-validation.md).
::
