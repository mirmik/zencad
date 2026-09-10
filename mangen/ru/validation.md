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

Валидная открытая оболочка не является замкнутым телом. `is_closed()` проверяет замкнутость только `Edge` и `Wire`; для `Shell` и `Solid` этот метод не поддерживается. Для итогового тела проверяйте одновременно валидность и наличие solid-компонентов: `zencad check model.py --valid --solid`. [Headless workflow](headless.html), [формат отчёта](../development/shape-validation.md).
